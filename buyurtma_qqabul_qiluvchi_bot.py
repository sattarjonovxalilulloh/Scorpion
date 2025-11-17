from telegram import (
    Update,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler
)
import sqlite3

# === TOKEN VA ADMIN ===
TOKEN = "Bot token"
ADMIN_ID = ADMIN_ID

# === HOLATLAR ===
NAME, PHONE, SERVICE_TYPE, DESCRIPTION, BUDGET, PAYMENT, DEADLINE, SETTINGS = range(8)


# === DATABASE ===
def create_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            phone TEXT,
            service_type TEXT,
            description TEXT,
            budget TEXT,
            payment TEXT,
            deadline TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            about TEXT,
            contact TEXT
        )
    """)
    cur.execute("INSERT OR IGNORE INTO settings (id, about, contact) VALUES (1, 'Bu bot buyurtmalarni qabul qiladi.', '@admin_contact')")
    conn.commit()
    conn.close()


# === Sozlamalarni olish va yangilash ===
def get_settings():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT about, contact FROM settings WHERE id = 1")
    row = cur.fetchone()
    conn.close()
    return row

def update_settings(about, contact):
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("UPDATE settings SET about=?, contact=? WHERE id=1", (about, contact))
    conn.commit()
    conn.close()


# === Menyular ===
def main_menu_keyboard(user_id):
    if user_id == ADMIN_ID:
        return ReplyKeyboardMarkup(
            [["🧠 Bot yasash", "🌐 Sayt yasash"],
             ["📋 Barcha foydalanuvchilar", "⚙️ Sozlamalar"]],
            resize_keyboard=True
        )
    else:
        return ReplyKeyboardMarkup(
            [["🧠 Bot yasash", "🌐 Sayt yasash"]],
            resize_keyboard=True
        )


# === /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    about, contact = get_settings()
    await update.message.reply_text(
        f"👋 Salom! Xush kelibsiz.\n\nℹ️ {about}\n📞 Bog‘lanish: {contact}\n\nQuyidagilardan birini tanlang 👇",
        reply_markup=main_menu_keyboard(user_id)
    )


# === Buyurtma boshlanishi ===
async def buyurtma_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["service_type"] = update.message.text
    await update.message.reply_text("👤 Ismingizni kiriting:")
    return NAME


# === Ismni olish ===
async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("📞 Telefon raqamingiz yoki Telegram username’ingizni kiriting:")
    return PHONE


# === Telefonni olish ===
async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    if "Bot" in context.user_data["service_type"]:
        keyboard = [
            ["🤖 Savol-javob bot", "🛍 Buyurtma qabul bot"],
            ["💳 To‘lov qabul bot", "📊 CRM integratsiya bot"],
            ["📝 Boshqa"]
        ]
        text = "Qanday bot kerak? Quyidagilardan birini tanlang 👇"
    else:
        keyboard = [
            ["🌐 Landing Page", "🛒 Internet do‘kon"],
            ["🏢 Korporativ sayt", "🧾 Boshqa"]
        ]
        text = "Qanday sayt kerak? Quyidagilardan birini tanlang 👇"

    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return SERVICE_TYPE


# === Xizmat turi ===
async def get_service_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["subtype"] = update.message.text
    await update.message.reply_text("🗒 Qisqacha izoh yoki talablaringizni yozing:")
    return DESCRIPTION


# === Izoh ===
async def get_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["description"] = update.message.text
    keyboard = [
        ["💵 <100$", "💰 100–300$"],
        ["💎 300$+"]
    ]
    await update.message.reply_text(
        "💰 Taxminiy budjetingizni tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return BUDGET


# === Budjet ===
async def get_budget(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["budget"] = update.message.text
    keyboard = [["💳 Karta orqali", "💵 Naqd pul"]]
    await update.message.reply_text(
        "💳 To‘lov turini tanlang:",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return PAYMENT


# === To‘lov turi ===
async def get_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["payment"] = update.message.text
    keyboard = [["⏰ 1 kun", "🕒 3 kun", "📆 1 hafta"]]
    await update.message.reply_text(
        "⏳ Qachon tayyor bo‘lishini xohlaysiz?",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )
    return DEADLINE


# === Muddat ===
async def get_deadline(update: Update, context: ContextTypes.DEFAULT_TYPE):
    deadline = update.message.text.strip()

    valid_options = ["⏰ 1 kun", "🕒 3 kun", "📆 1 hafta", "1 kun", "3 kun", "1 hafta"]

    if deadline not in valid_options:
        await update.message.reply_text(
            keyboard = [
                ["⏰ 1 kun", "🕒 3 kun", "📆 1 hafta"]
            ]
await update.message.reply_text(
    "⏳ Qachon tayyor bo‘lishini xohlaysiz?",
    reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)
                    )

)
        return DEADLINE

    # Foydalanuvchi tanlovini saqlaymiz
    context.user_data["deadline"] = deadline
    user = update.message.from_user
    user_id = user.id

    # Ma’lumotlarni olish
    name = context.user_data["name"]
    phone = context.user_data["phone"]
    service_type = context.user_data["service_type"]
    subtype = context.user_data["subtype"]
    description = context.user_data["description"]
    budget = context.user_data["budget"]
    payment = context.user_data["payment"]

    # Bazaga yozish
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (user_id, name, phone, service_type, description, budget, payment, deadline)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, name, phone, f"{service_type} - {subtype}", description, budget, payment, deadline))
    conn.commit()
    conn.close()

    # Admin'ga yuboriladigan xabar
    msg = (
        f"🆕 Yangi buyurtma!\n\n"
        f"👤 Ism: {name}\n"
        f"📞 Aloqa: {phone}\n"
        f"💼 Xizmat: {service_type} ({subtype})\n"
        f"🗒 Izoh: {description}\n"
        f"💰 Budjet: {budget}\n"
        f"💳 To‘lov: {payment}\n"
        f"⏳ Muddat: {deadline}\n"
        f"🆔 User ID: {user_id}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    # Foydalanuvchiga javob
    await update.message.reply_text(
        "✅ Rahmat! Buyurtmangiz qabul qilindi.\n"
        "Tez orada siz bilan bog‘lanamiz.",
        reply_markup=main_menu_keyboard(user_id)
    )
    return ConversationHandler.END

    # Bazaga yozish
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO users (user_id, name, phone, service_type, description, budget, payment, deadline)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, name, phone, f"{service_type} - {subtype}", description, budget, payment, deadline))
    conn.commit()
    conn.close()

    # Admin'ga xabar
    msg = (
        f"🆕 Yangi buyurtma!\n\n"
        f"👤 Ism: {name}\n"
        f"📞 Aloqa: {phone}\n"
        f"💼 Xizmat: {service_type} ({subtype})\n"
        f"🗒 Izoh: {description}\n"
        f"💰 Budjet: {budget}\n"
        f"💳 To‘lov: {payment}\n"
        f"⏳ Muddat: {deadline}\n"
        f"🆔 User ID: {user_id}"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=msg)

    await update.message.reply_text(
        "✅ Rahmat! Buyurtmangiz qabul qilindi.\n"
        "Tez orada siz bilan bog‘lanamiz.",
        reply_markup=main_menu_keyboard(user_id)
    )
    return ConversationHandler.END


# === Admin uchun foydalanuvchilar ro‘yxati ===
async def show_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Bu bo‘lim faqat admin uchun.")
        return

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()
    cur.execute("SELECT name, phone, service_type, budget FROM users ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await update.message.reply_text("📂 Hali foydalanuvchilar yo‘q.")
        return

    text = "📋 <b>Barcha buyurtmalar:</b>\n\n"
    for i, row in enumerate(rows, 1):
        text += f"{i}. {row[0]} — {row[1]} — {row[2]} — {row[3]}\n"
    await update.message.reply_text(text, parse_mode="HTML")


# === Sozlamalar ===
async def settings_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("⛔ Sizda ruxsat yo‘q.")
        return

    about, contact = get_settings()
    await update.message.reply_text(
        f"⚙️ Hozirgi sozlamalar:\n\nℹ️ {about}\n📞 {contact}\n\n"
        "Yangi 'Haqida' matnini yuboring yoki /cancel bilan chiqish.",
    )
    context.user_data["edit_mode"] = "about"
    return SETTINGS


async def settings_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("edit_mode")
    text = update.message.text
    about, contact = get_settings()

    if mode == "about":
        about = text
        context.user_data["edit_mode"] = "contact"
        await update.message.reply_text("Endi yangi aloqa ma’lumotlarini yuboring:")
        update_settings(about, contact)
        return SETTINGS
    elif mode == "contact":
        contact = text
        update_settings(about, contact)
        await update.message.reply_text("✅ Sozlamalar yangilandi.", reply_markup=main_menu_keyboard(ADMIN_ID))
        return ConversationHandler.END


# === Bekor qilish ===
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text(
        "❌ Amal bekor qilindi.",
        reply_markup=main_menu_keyboard(user_id)
    )
    return ConversationHandler.END


# === Main ===
def main():
    create_db()
    app = ApplicationBuilder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^🧠 Bot yasash$"), buyurtma_start),
            MessageHandler(filters.Regex("^🌐 Sayt yasash$"), buyurtma_start),
        ],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            SERVICE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_service_type)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_description)],
            BUDGET: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_budget)],
            PAYMENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment)],
            DEADLINE: [
    MessageHandler(filters.TEXT & ~filters.COMMAND, get_deadline)
],

        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    settings_conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^⚙️ Sozlamalar$"), settings_menu)],
        states={SETTINGS: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_update)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_handler(settings_conv)
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex("^📋 Barcha foydalanuvchilar$"), show_users))

    print("🤖 Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
