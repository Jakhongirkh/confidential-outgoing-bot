import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import os
import json
from datetime import datetime

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEST_GROUP_ID = int(os.getenv("DEST_GROUP_ID"))
AUTHORIZED_USERS = json.loads(os.getenv("AUTHORIZED_USERS", "[]"))

SUBSCRIBERS = {
    "Эшанкулов Х. М.": "01",
    "Насретдинов Б.": "01-01",
    "Тахиров И.": "01-03",
    "Мамажонов Х.": "01-04",
    "Мирсаидов А.": "01-05",
    "Убайдуллаев А.": "01-06",
    "Любушкина М.": "01-07"
}

# Установка логгера
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Чтение/обновление счётчика
def get_and_increment_counter():
    if not os.path.exists("counter.txt"):
        with open("counter.txt", "w") as f:
            f.write("0")
    with open("counter.txt", "r+") as f:
        value = int(f.read())
        f.seek(0)
        f.write(str(value + 1))
        f.truncate()
    return value + 1

# Хранилище для временных данных пользователя
user_states = {}

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in AUTHORIZED_USERS:
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return

    keyboard = [[InlineKeyboardButton("📄 Получить номер исходящего письма", callback_data="get_number")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Добро пожаловать! Выберите действие:", reply_markup=reply_markup)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "get_number":
        keyboard = [[InlineKeyboardButton(name, callback_data=f"signer_{code}")] for name, code in SUBSCRIBERS.items()]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Выберите, пожалуйста, подписанта письма:", reply_markup=reply_markup)
    
    elif query.data.startswith("signer_"):
        code = query.data.split("_")[1]
        user_states[query.from_user.id] = code
        await query.edit_message_text(f"✅ Подписант выбран: {code}\n📷 Пожалуйста, отправьте фото письма.")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return

    if user_id not in user_states:
        await update.message.reply_text("Пожалуйста, сначала выберите подписанта через кнопку.")
        return

    signer_code = user_states.pop(user_id)
    count = get_and_increment_counter()
    number = f"{signer_code}/{count}"
    date_str = datetime.now().strftime("%d.%m.%Y")

    caption = f"📤 Исходящее письмо
Номер: {number}
Дата: {date_str}
Отправил: @{update.effective_user.username or update.effective_user.id}"
    
    photo = update.message.photo[-1]
    file_id = photo.file_id
    await context.bot.send_photo(chat_id=DEST_GROUP_ID, photo=file_id, caption=caption)
    await update.message.reply_text(f"✅ Номер письма: {number}
Фото успешно отправлено.")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()

if __name__ == "__main__":
    main()
