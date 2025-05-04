import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram.helpers import escape_markdown

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Sample product data
PRODUCTS = [
    {
        "id": 1,
        "name": "Smart Laser Chase",
        "description": "Automatic rotating laser toy with 3 modes",
        "price": 29.99,
        "image": "https://example.com/laser.jpg",
        "link": "https://example.com/laser-product"
    },
    {
        "id": 2,
        "name": "Feather Whirlwind",
        "description": "Electronic feather spinner with timer",
        "price": 19.95,
        "image": "https://example.com/feather.jpg",
        "link": "https://example.com/feather-product"
    },
    {
        "id": 3,
        "name": "Interactive Puzzle Box",
        "description": "Treat-dispensing puzzle challenge toy",
        "price": 34.50,
        "image": "https://example.com/puzzle.jpg",
        "link": "https://example.com/puzzle-product"
    }
]

# In-memory storage for user carts
user_carts = {}

def escape(text: str) -> str:
    """Helper function to escape MarkdownV2 characters."""
    return escape_markdown(text, version=2)

def main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("View Products", callback_data="view_products")]
    ])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f"🐾 Welcome {escape(user.first_name)} to ModernCatToys!\n\n"
        "Browse our collection of high-tech cat toys!\n"
        "Use /products to see our collection\n"
        "Use /cart to view your shopping cart",
        reply_markup=main_menu_keyboard(),
        parse_mode="MarkdownV2"
    )

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(
            f"{escape(product['name'])} - ${product['price']:.2f}",
            callback_data=f"view_{product['id']}"
        )] for product in PRODUCTS
    ]

    await query.edit_message_text(
        text="🏷 **Our Products** 🏷\nSelect a product to view details:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="MarkdownV2"
    )

async def product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    
    try:
        product_id = int(query.data.split("_")[1])
        product = next(p for p in PRODUCTS if p["id"] == product_id)
    except (ValueError, StopIteration):
        await query.edit_message_text("❌ Product not found.")
        return

    caption = (
        f"*{escape(product['name'])}*\n\n"
        f"{escape(product['description'])}\n"
        f"Price: ${product['price']:.2f}\n"
        f"[Product Link]({product['link']})"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🛒 Add to Cart", callback_data=f"add_{product_id}"),
            InlineKeyboardButton("🔙 Back", callback_data="view_products")
        ]
    ])

    await context.bot.send_photo(
        chat_id=query.message.chat_id,
        photo=product["image"],
        caption=caption,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )
    await query.message.delete()

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    try:
        product_id = int(query.data.split("_")[1])
    except ValueError:
        await query.answer("Invalid product.", show_alert=True)
        return

    cart = user_carts.setdefault(user_id, {})
    cart[product_id] = cart.get(product_id, 0) + 1

    await query.answer(f"✅ Added {escape(PRODUCTS[product_id - 1]['name'])} to cart!", show_alert=False)

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    cart = user_carts.get(user_id, {})

    if not cart:
        await update.message.reply_text("Your cart is empty!")
        return

    total = 0
    message = "🛒 **Your Cart** 🛒\n\n"
    for product_id, quantity in cart.items():
        product = next((p for p in PRODUCTS if p["id"] == product_id), None)
        if not product:
            continue
        subtotal = product['price'] * quantity
        total += subtotal
        message += f"{escape(product['name'])} x{quantity} - ${subtotal:.2f}\n"

    message += f"\n**Total: ${total:.2f}**"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Checkout", callback_data="checkout")],
        [InlineKeyboardButton("Continue Shopping", callback_data="view_products")]
    ])

    await update.message.reply_text(
        message,
        reply_markup=keyboard,
        parse_mode="MarkdownV2"
    )

async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if not user_carts.get(user_id):
        await query.edit_message_text("Your cart is already empty.")
        return

    user_carts[user_id] = {}  # Clear the cart

    await query.edit_message_text("✅ Thank you for your purchase! Your cart is now empty.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Please use the menu buttons to navigate!",
        reply_markup=main_menu_keyboard(),
        parse_mode="MarkdownV2"
    )

def main() -> None:
    application = Application.builder().token("7811645028:AAGgPneHRCHvvpz6p0Kmj4QSsP_heUee3bw").build()

    # Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("products", show_products))
    application.add_handler(CommandHandler("cart", view_cart))

    # Callback Query Handlers
    application.add_handler(CallbackQueryHandler(show_products, pattern="^view_products$"))
    application.add_handler(CallbackQueryHandler(product_detail, pattern="^view_\\d+$"))
    application.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_\\d+$"))
    application.add_handler(CallbackQueryHandler(checkout, pattern="^checkout$"))

    # Fallback message handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
