import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import os
import json
from datetime import datetime

# Конфигурация
BOT_TOKEN = os.getenv("BOT_TOKEN") or "7242725938:AAF4kjuq-pW1yKRQ65H94xa2uAoT067dfcE"
DEST_GROUP_ID = int(os.getenv("DEST_GROUP_ID") or "-4603122462")
AUTHORIZED_USERS = json.loads(os.getenv("AUTHORIZED_USERS") or "[123456789, 987654321, 931156301, 5169701031, 5169167062, 2775849, 5615990266, 161924982]")

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
    user = update.effective_user
    if user.id not in AUTHORIZED_USERS:
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")

        # Отправка ID в группу
        message = (
            f"🚫 Неавторизованный пользователь:\n"
            f"👤 Username: @{user.username or '—'}\n"
            f"🆔 ID: {user.id}"
        )
        await context.bot.send_message(chat_id=DEST_GROUP_ID, text=message)
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

        count = get_and_increment_counter()

        full_number = f"{code}/{count}"

        user_states[query.from_user.id] = code  # сохранить юникод для следующего шага (handle_photo)

        await query.edit_message_text(f"✅ Подписант выбран: {full_number}\n📷 Пожалуйста, отправьте фото письма.")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in AUTHORIZED_USERS:
        await update.message.reply_text("⛔ У вас нет доступа к этому боту.")
        return

    if user_id not in user_states:
        await update.message.reply_text("Пожалуйста, сначала выберите подписанта через кнопку.")
        return

    signer_code = user_states.pop(user_id)

    # signer_code уже содержит только код без номера, значит, надо вытащить номер из сообщения?
    # НЕТ — давай сохраним сразу готовый full_number в user_states

    # ОБНОВИМ: теперь сохраняем full_number (01-01/341) в user_states:
    full_number = signer_code  # теперь это уже "01-01/341"
    date_str = datetime.now().strftime("%d.%m.%Y")

    caption = (
        f"📤 Исходящее письмо\n"
        f"Номер: {full_number}\n"
        f"Дата: {date_str}\n"
        f"Отправил: @{update.effective_user.username or update.effective_user.id}"
    )

    photo = update.message.photo[-1]
    file_id = photo.file_id
    await context.bot.send_photo(chat_id=DEST_GROUP_ID, photo=file_id, caption=caption)

    await update.message.reply_text(
        f"✅ Номер письма: {full_number}\nФото успешно отправлено."
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()


if __name__ == "__main__":
    main()
    # force redeploy
