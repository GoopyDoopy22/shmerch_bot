import os
import logging
import time
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, LabeledPrice
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, PreCheckoutQueryHandler, MessageHandler, filters
from PIL import Image, ImageDraw, ImageFont
import io

logging.basicConfig(level=logging.INFO)

# ================ НАСТРОЙКИ ================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7650289555:AAGnpjQ6-C2tg6I8ey4yiJFCUQopY7kp2AA")
PRICE_STARS = 5
ITEMS_PER_PAGE = 6
ITEMS_PER_ROW = 3
# ============================================

def load_items():
    items = {}
    categories = ['body', 'eyes', 'mouth', 'hair', 'glasses', 'hat']
    base_path = '/app/images'  # Изменил путь для Railway
    for category in categories:
        category_path = os.path.join(base_path, category)
        items[category] = []
        if os.path.exists(category_path):
            files = [f for f in os.listdir(category_path) if f.endswith('.png')]
            items[category] = sorted(files)
    return items

ITEMS = load_items()
user_selections = {}
user_current_pages = {}
user_last_message_ids = {}

category_names = {
    'body': 'Тело',
    'eyes': 'Глаза',
    'mouth': 'Рот',
    'hair': 'Прическа',
    'glasses': 'Очки',
    'hat': 'Шапка'
}

async def clean_previous_messages(update, context, except_message_id=None):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if user_id in user_last_message_ids:
        for msg_id in user_last_message_ids[user_id]:
            if msg_id != except_message_id:
                try:
                    await context.bot.delete_message(chat_id=chat_id, message_id=msg_id)
                except:
                    pass
        user_last_message_ids[user_id] = []

async def save_message_id(user_id, message_id):
    if user_id not in user_last_message_ids:
        user_last_message_ids[user_id] = []
    user_last_message_ids[user_id].append(message_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_selections[user_id] = {}
    user_current_pages[user_id] = {cat: 0 for cat in ITEMS.keys()}
    await clean_previous_messages(update, context)
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧱 Тело", callback_data="cat_body")],
        [InlineKeyboardButton("👁 Глаза", callback_data="cat_eyes")],
        [InlineKeyboardButton("👄 Рот", callback_data="cat_mouth")],
        [InlineKeyboardButton("💇 Прическа", callback_data="cat_hair")],
        [InlineKeyboardButton("👓 Очки", callback_data="cat_glasses")],
        [InlineKeyboardButton("🎩 Шапка", callback_data="cat_hat")],
        [InlineKeyboardButton("🔄 Сбросить всё", callback_data="reset"),
         InlineKeyboardButton("✅ Готово", callback_data="done")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🎨 **Shmerch Avatar Maker**\n\nВыбирай детали для своего персонажа:"
    
    if update.callback_query:
        sent_message = await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    else:
        sent_message = await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    await save_message_id(update.effective_user.id, sent_message.message_id)

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data.startswith("cat_"):
        category = data[4:]
        await show_category_preview(update, context, category)
    elif data.startswith("select_"):
        await select_item(update, context, data)
    elif data == "reset":
        user_selections[user_id] = {}
        await clean_previous_messages(update, context)
        await query.edit_message_text("✅ Все выборы сброшены")
        await show_main_menu(update, context)
    elif data == "done":
        await show_result(update, context)
    elif data.startswith("page_"):
        await change_page(update, context, data)
    elif data == "back_to_main":
        await show_main_menu(update, context)

async def show_category_preview(update: Update, context: ContextTypes.DEFAULT_TYPE, category):
    query = update.callback_query
    user_id = query.from_user.id
    items = ITEMS.get(category, [])
    
    if not items:
        await query.edit_message_text(f"❌ В категории {category} пока нет предметов")
        await show_main_menu(update, context)
        return
    
    await clean_previous_messages(update, context, except_message_id=query.message.message_id)
    
    page = user_current_pages[user_id].get(category, 0)
    start_idx = page * ITEMS_PER_PAGE
    end_idx = min(start_idx + ITEMS_PER_PAGE, len(items))
    page_items = items[start_idx:end_idx]
    
    media_group = []
    keyboard = []
    
    for i, item in enumerate(page_items):
        file_path = f"/app/images/{category}/{item}"
        try:
            img = Image.open(file_path)
            img.thumbnail((200, 200))
            bio = io.BytesIO()
            img.save(bio, 'PNG')
            bio.seek(0)
            
            display_name = item.replace('.png', '').replace('_', ' ').title()
            media_group.append(InputMediaPhoto(media=bio, caption=display_name))
            
            callback = f"select_{category}_{item}"
            row_pos = i // ITEMS_PER_ROW
            if len(keyboard) <= row_pos:
                keyboard.append([])
            keyboard[row_pos].append(InlineKeyboardButton(f"✅ Выбрать {i+1}", callback_data=callback))
        except:
            pass
    
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ Предыдущая", callback_data=f"page_{category}_{page-1}"))
    if end_idx < len(items):
        nav_buttons.append(InlineKeyboardButton("Следующая ▶️", callback_data=f"page_{category}_{page+1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)
    
    keyboard.append([InlineKeyboardButton("🔙 Назад в меню", callback_data="back_to_main")])
    
    if media_group:
        sent_media = await context.bot.send_media_group(chat_id=user_id, media=media_group)
        for msg in sent_media:
            await save_message_id(user_id, msg.message_id)
    
    sent_message = await context.bot.send_message(
        chat_id=user_id,
        text=f"{category_names.get(category, category)} — стр.{page+1}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await save_message_id(user_id, sent_message.message_id)
    await query.delete_message()

async def select_item(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    query = update.callback_query
    user_id = query.from_user.id
    parts = data.split('_', 2)
    category = parts[1]
    filename = parts[2]
    
    if user_id not in user_selections:
        user_selections[user_id] = {}
    user_selections[user_id][category] = filename
    
    await clean_previous_messages(update, context, except_message_id=query.message.message_id)
    await query.edit_message_text(f"✅ {category_names.get(category, category)} выбран")
    await save_message_id(user_id, query.message.message_id)
    await show_main_menu(update, context)

async def change_page(update: Update, context: ContextTypes.DEFAULT_TYPE, data):
    query = update.callback_query
    user_id = query.from_user.id
    parts = data.split('_')
    category = parts[1]
    page = int(parts[2])
    user_current_pages[user_id][category] = page
    await clean_previous_messages(update, context, except_message_id=query.message.message_id)
    await show_category_preview(update, context, category)

async def generate_image_from_selections(selections, watermark=True):
    result = None
    order = ['body', 'eyes', 'mouth', 'hair', 'glasses', 'hat']
    
    for category in order:
        if category in selections:
            file_path = f"/app/images/{category}/{selections[category]}"
            if os.path.exists(file_path):
                img = Image.open(file_path).convert('RGBA')
                if result is None:
                    result = img
                else:
                    if result.size != img.size:
                        img = img.resize(result.size)
                    result = Image.alpha_composite(result, img)
    
    if result and watermark:
        draw = ImageDraw.Draw(result)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 60)
        except:
            font = ImageFont.load_default()
        
        text = "Shmerch"
        bbox = draw.textbbox((0, 0), text, font=font)
        pos = ((result.width - (bbox[2]-bbox[0]))//2, (result.height - (bbox[3]-bbox[1]))//2)
        draw.text(pos, text, font=font, fill=(255,255,255,77))
        
        draw.text((result.width-80, result.height-80), "Ⓢ", font=font, fill=(255,255,255,128))
    
    return result

async def show_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    selections = user_selections.get(user_id, {})
    
    if not selections:
        await query.edit_message_text("❌ Ничего не выбрано")
        return
    
    await clean_previous_messages(update, context, except_message_id=query.message.message_id)
    
    try:
        result = await generate_image_from_selections(selections, watermark=True)
        if result:
            bio = io.BytesIO()
            result.save(bio, 'PNG')
            bio.seek(0)
            
            await query.edit_message_text("🎉 Твой Shmerch готов! (с водяным знаком)")
            sent_photo = await context.bot.send_photo(chat_id=user_id, photo=bio)
            await save_message_id(user_id, sent_photo.message_id)
            
            # ПЛАТЕЖИ ЧЕРЕЗ TELEGRAM STARS
            await context.bot.send_invoice(
                chat_id=user_id,
                title="Shmerch Avatar",
                description="Чистое изображение без водяного знака",
                payload=f"stars_{user_id}_{int(time.time())}",
                provider_token="",
                currency="XTR",
                prices=[LabeledPrice("Аватар", PRICE_STARS)]
            )
            
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {e}")

async def pre_checkout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.pre_checkout_query.answer(ok=True)

async def successful_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    selections = user_selections.get(user_id, {})
    
    if not selections:
        await update.message.reply_text("❌ Ошибка: данные не найдены")
        return
    
    result = await generate_image_from_selections(selections, watermark=False)
    if result:
        bio = io.BytesIO()
        result.save(bio, 'PNG')
        bio.seek(0)
        
        await update.message.reply_text("✅ Оплата прошла! Держи чистое изображение:")
        await context.bot.send_photo(chat_id=user_id, photo=bio)

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await clean_previous_messages(update, context)
    await show_main_menu(update, context)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback))
    app.add_handler(PreCheckoutQueryHandler(pre_checkout))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment))
    
    print("\n" + "="*60)
    print("✅ Shmerch Bot ЗАПУЩЕН!")
    print(f"💰 Цена: {PRICE_STARS} ⭐")
    print("⭐ Telegram Stars: ПОДКЛЮЧЕНЫ")
    print(f"📁 Категорий: {len(ITEMS)}")
    for cat, items in ITEMS.items():
        print(f"   • {cat}: {len(items)} предметов")
    print("="*60 + "\n")
    
    app.run_polling()

if __name__ == "__main__":
    main()
