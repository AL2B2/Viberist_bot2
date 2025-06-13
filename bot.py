import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

AUTHORIZED_USERS = [7348005877, 6609148454]  # список разрешённых ID

CREDENTIALS_FILE = "credentials.json"
USERS_FILE = "users.json"

def load_json(filename):
    if not os.path.exists(filename):
        return {}
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(data, filename):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "пользователь"

    print(f"User ID: {user_id} (username: {username})")  # Вывод ID в консоль

    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return

    credentials = load_json(CREDENTIALS_FILE)
    keyboard = []

    button_list = list(credentials.keys())

    for i in range(0, len(button_list) - 1, 2):
        keyboard.append([
            InlineKeyboardButton(button_list[i], callback_data=button_list[i]),
            InlineKeyboardButton(button_list[i+1], callback_data=button_list[i+1])
        ])

    if len(button_list) % 2 == 1:
        keyboard.append([InlineKeyboardButton(button_list[-1], callback_data=button_list[-1])])

    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        with open("banner.jpg", "rb") as image_file:
            await update.message.reply_photo(
                photo=image_file,
                caption=f"👋 Добро пожаловать, @{username}! Выберите источник:",
                reply_markup=reply_markup
            )
    except FileNotFoundError:
        await update.message.reply_text(
            f"👋 Привет, @{username}!\nВыберите источник:",
            reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in AUTHORIZED_USERS:
        await query.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return

    source = query.data

    credentials = load_json(CREDENTIALS_FILE)
    users = load_json(USERS_FILE)

    user_id_str = str(user_id)
    user_sources = users.get(user_id_str, [])

    if source in user_sources:
        message = f"⚠️ Вы уже получили данные по {source}."
    elif source in credentials:
        available = [acc for acc in credentials[source] if not acc.get("used")]

        if available:
            account = available[0]
            account["used"] = True

            users.setdefault(user_id_str, []).append(source)

            save_json(credentials, CREDENTIALS_FILE)
            save_json(users, USERS_FILE)

            message = (
                f"🔐 <b>{source}</b>\n"
                f"👤 Логин: <code>{account['login']}</code>\n"
                f"🔑 Пароль: <code>{account['pass']}</code>"
            )
        else:
            message = f"❌ Нет доступных аккаунтов для {source}."
    else:
        message = f"⚠️ Источник '{source}' не найден."

    try:
        await query.edit_message_text(text=message, parse_mode="HTML")
    except:
        await query.message.reply_text(text=message, parse_mode="HTML")

def main():
    from dotenv import load_dotenv
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")

    app = Application.builder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Бот запущен...")
    app.run_polling()

if __name__ == "__main__":
    main()
