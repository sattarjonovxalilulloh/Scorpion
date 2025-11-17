import logging
import json
import os
from datetime import datetime
from typing import Dict

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

# ==================== KONFIGURATSIYA ====================
BOT_TOKEN = "Bot token"
ADMIN_CHAT_ID = "Admin id"  # Adminning Telegram ID'si

# JSON fayl nomlari
PRODUCTS_FILE = "products.json"
ORDERS_FILE = "orders.json"

# ==================== LOGGING ====================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== MA'LUMOTLAR STRUKTURASI ====================
class Product:
    def __init__(self, id: int, name: str, price: float, description: str, image_url: str = None):
        self.id = id
        self.name = name
        self.price = price
        self.description = description
        self.image_url = image_url

class Cart:
    def __init__(self):
        self.items: Dict[int, int] = {}

    def add_product(self, product_id: int, quantity: int = 1):
        self.items[product_id] = self.items.get(product_id, 0) + quantity

    def remove_product(self, product_id: int):
        if product_id in self.items:
            del self.items[product_id]

    def get_total_price(self, products: Dict[int, Product]) -> float:
        return sum(products[pid].price * qty for pid, qty in self.items.items() if pid in products)

    def clear(self):
        self.items.clear()

# ==================== GLOBAL O'ZGARUVCHILAR ====================
products_db: Dict[int, Product] = {}
user_carts: Dict[int, Cart] = {}

# ==================== MA'LUMOTLARNI YUKLASH ====================
def load_products():
    """Mahsulotlarni JSON fayldan yuklash"""
    global products_db
    try:
        if os.path.exists(PRODUCTS_FILE):
            with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for p in data:
                products_db[p["id"]] = Product(
                    id=p["id"],
                    name=p["name"],
                    price=p["price"],
                    description=p["description"],
                    image_url=p.get("image_url")
                )
        else:
            demo_products = [
                {"id": 1, "name": "iPhone 15 Pro", "price": 999.99, "description": "Eng yangi iPhone modeli"},
                {"id": 2, "name": "Samsung Galaxy S24", "price": 899.99, "description": "Kuchli Android telefon"},
                {"id": 3, "name": "MacBook Air M2", "price": 1299.99, "description": "Yengil va kuchli noutbuk"},
                {"id": 4, "name": "AirPods Pro", "price": 249.99, "description": "Noise cancellation bilan airpods"},
            ]
            with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
                json.dump(demo_products, f, ensure_ascii=False, indent=2)
            load_products()
    except Exception as e:
        logger.error(f"Mahsulotlarni yuklashda xato: {e}")

def save_order(order_data: dict):
    """Buyurtmani JSON faylga saqlash"""
    try:
        orders = []
        if os.path.exists(ORDERS_FILE):
            with open(ORDERS_FILE, "r", encoding="utf-8") as f:
                orders = json.load(f)
        orders.append(order_data)
        with open(ORDERS_FILE, "w", encoding="utf-8") as f:
            json.dump(orders, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Buyurtmani saqlashda xato: {e}")

# ==================== KEYBOARD LAR ====================
def get_main_menu_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛍 Mahsulotlar", callback_data="products")],
        [InlineKeyboardButton("📞 Aloqa", callback_data="contact"),
         InlineKeyboardButton("ℹ️ Ma'lumot", callback_data="info")],
        [InlineKeyboardButton("🛒 Savatcha", callback_data="cart")],
        [InlineKeyboardButton("📦 Mening buyurtmalarim", callback_data="my_orders")]
    ])

def get_products_keyboard():
    keyboard = [[InlineKeyboardButton(f"{p.name} - ${p.price}", callback_data=f"product_{p.id}")]
                for p in products_db.values()]
    keyboard.append([InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def get_product_detail_keyboard(product_id: int):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Savatga qo'shish", callback_data=f"add_to_cart_{product_id}")],
        [InlineKeyboardButton("🔙 Mahsulotlar", callback_data="products")]
    ])

def get_cart_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📦 Buyurtma berish", callback_data="checkout")],
        [InlineKeyboardButton("🗑 Savatni tozalash", callback_data="clear_cart")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")]
    ])

# ==================== HANDLERLAR ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id not in user_carts:
        user_carts[user.id] = Cart()
    await update.message.reply_text(
        f"👋 Salom, {user.first_name}!\n🛍 Mini Online Store botiga xush kelibsiz!",
        reply_markup=get_main_menu_keyboard()
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "back_to_main":
        await query.edit_message_text("🏠 Asosiy menyu:", reply_markup=get_main_menu_keyboard())
    elif data == "products":
        await show_products(query)
    elif data.startswith("product_"):
        product_id = int(data.split("_")[1])
        await show_product_detail(query, product_id)
    elif data.startswith("add_to_cart_"):
        product_id = int(data.split("_")[2])  # ✅ To‘g‘rilandi!
        await add_to_cart(query, user_id, product_id)
    elif data == "cart":
        await show_cart(query, user_id)
    elif data == "clear_cart":
        await clear_cart(query, user_id)
    elif data == "checkout":
        await checkout(query, user_id, context)
    elif data == "contact":
        await show_contact(query)
    elif data == "info":
        await show_info(query)
    elif data == "my_orders":
        await show_user_orders(query, user_id)

# ==================== FUNKSIYALAR ====================
async def show_products(query):
    text = "📦 Mahsulotlar ro‘yxati:"
    await query.edit_message_text(text, reply_markup=get_products_keyboard())

async def show_product_detail(query, product_id: int):
    product = products_db.get(product_id)
    if not product:
        await query.edit_message_text("❌ Mahsulot topilmadi.")
        return
    text = f"📱 {product.name}\n💲 Narx: ${product.price}\n📝 {product.description}"
    await query.edit_message_text(text, reply_markup=get_product_detail_keyboard(product_id))

async def add_to_cart(query, user_id: int, product_id: int):
    if user_id not in user_carts:
        user_carts[user_id] = Cart()
    user_carts[user_id].add_product(product_id)
    await query.edit_message_text("✅ Mahsulot savatga qo‘shildi!", reply_markup=get_products_keyboard())

async def show_cart(query, user_id: int):
    cart = user_carts.get(user_id)
    if not cart or not cart.items:
        await query.edit_message_text("🛒 Savatchangiz bo‘sh!", reply_markup=get_main_menu_keyboard())
        return
    text = "🛍 Savatchangiz:\n\n"
    total = 0
    for pid, qty in cart.items.items():
        if pid in products_db:
            p = products_db[pid]
            text += f"• {p.name} — {qty} x ${p.price}\n"
            total += p.price * qty
    text += f"\n💰 Jami: ${total:.2f}"
    await query.edit_message_text(text, reply_markup=get_cart_keyboard())

async def clear_cart(query, user_id: int):
    user_carts[user_id].clear()
    await query.edit_message_text("✅ Savat tozalandi!", reply_markup=get_main_menu_keyboard())

async def checkout(query, user_id: int, context):
    cart = user_carts.get(user_id)
    if not cart or not cart.items:
        await query.edit_message_text("❌ Savat bo‘sh!", reply_markup=get_main_menu_keyboard())
        return
    order = {
        "order_id": f"ORD_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "user_id": user_id,
        "total": cart.get_total_price(products_db),
        "date": datetime.now().isoformat()
    }
    save_order(order)
    cart.clear()
    await context.bot.send_message(ADMIN_CHAT_ID, f"🆕 Yangi buyurtma!\n{order}")
    await query.edit_message_text("✅ Buyurtma qabul qilindi!", reply_markup=get_main_menu_keyboard())

async def show_contact(query):
    text = "📞 Biz bilan aloqa: +998901234567\n📧 info@onlinestore.com"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")]]))

async def show_info(query):
    text = "ℹ️ Mini Online Store bot — siz uchun qulay onlayn xaridlar!"
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Orqaga", callback_data="back_to_main")]]))

async def show_user_orders(query, user_id: int):
    if not os.path.exists(ORDERS_FILE):
        await query.edit_message_text("Sizda hali buyurtma yo‘q.")
        return
    with open(ORDERS_FILE, "r", encoding="utf-8") as f:
        orders = json.load(f)
    user_orders = [o for o in orders if o["user_id"] == user_id]
    if not user_orders:
        await query.edit_message_text("Sizda hali buyurtma yo‘q.")
        return
    text = "📋 So‘nggi buyurtmalaringiz:\n\n"
    for o in user_orders[-3:]:
        text += f"🆔 {o['order_id']} — ${o['total']}\n📅 {o['date'][:10]}\n\n"
    await query.edit_message_text(text, reply_markup=get_main_menu_keyboard())

# ==================== ASOSIY FUNKSIYA ====================
def main():
    load_products()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    print("✅ Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()
