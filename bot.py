import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "7650289555:AAG-plwPXgnbdMY-ia-3kGqjkdMt9EypCIw")

def start(update: Update, context):
    keyboard = [[InlineKeyboardButton("🧱 Тело", callback_data="cat_body")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text("🎨 Shmerch Avatar Maker\n\nВыбирай детали:", reply_markup=reply_markup)

def menu_callback(update: Update, context):
    query = update.callback_query
    query.answer()
    query.edit_message_text("✅ Тело выбрано! Бот работает на Railway!")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(menu_callback))
    
    updater.start_polling()
    print("✅ Бот запущен на Railway!")
    updater.idle()

if __name__ == "__main__":
    main()
