import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7650289555:AAG-plwPXgnbdMY-ia-3kGqjkdMt9EypCIw")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🧱 Тело", callback_data="cat_body")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🎨 Shmerch Avatar Maker\n\nВыбирай детали:", reply_markup=reply_markup)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✅ Тело выбрано! Бот работает на Railway!")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback))
    print("✅ Бот запущен на Railway!")
    app.run_polling()

if __name__ == "__main__":
    main()