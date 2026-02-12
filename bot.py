import os
import logging
import asyncio
import json
import uuid
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# ============= KONFIGURATSIYA =============
TOKEN = os.environ.get('BOT_TOKEN')
ADMIN_ID = 7923179229  # <--- FAQAT 1 TA ADMIN, INTEGER!

if not TOKEN:
    load_dotenv()
    TOKEN = os.getenv('BOT_TOKEN')

if not TOKEN:
    print("❌ XATO: BOT_TOKEN topilmadi!")
    exit(1)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot va Dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ============= MA'LUMOTLAR BAZASI =============
USERS_DB_FILE = 'users_db.json'
BOOKS_DB_FILE = 'books_db.json'

users_db = {}
books_db = {}
pending_requests = {}  # Faqat bitta admin uchun

# ============= ADMIN TEKSHIRISH - SODDA =============
def is_admin(user_id):
    """1 ta adminni tekshirish"""
    return user_id == ADMIN_ID  # INTEGER bilan taqqoslash

def admin_required(handler):
    """Admin uchun decorator"""
    async def wrapper(message: Message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            await message.answer("❌ Bu funksiya faqat admin uchun!")
            return
        return await handler(message, *args, **kwargs)
    return wrapper

def admin_callback_required(handler):
    """Admin callback decorator"""
    async def wrapper(callback: CallbackQuery, *args, **kwargs):
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Siz admin emassiz!", show_alert=True)
            return
        await callback.answer()
        return await handler(callback, *args, **kwargs)
    return wrapper

# ============= FOYDALANUVCHILAR =============
def load_users_db():
    global users_db
    try:
        if os.path.exists(USERS_DB_FILE):
            with open(USERS_DB_FILE, 'r', encoding='utf-8') as f:
                users_db = json.load(f)
    except: users_db = {}

def save_users_db():
    with open(USERS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(users_db, f, ensure_ascii=False, indent=4)

def is_user_allowed(user_id):
    return str(user_id) in users_db and users_db[str(user_id)].get('allowed', False)

def add_user(user_id, username, first_name, last_name):
    user_id_str = str(user_id)
    users_db[user_id_str] = {
        'user_id': user_id,
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'joined_date': datetime.now().isoformat(),
        'allowed': False,
        'quizzes_played': 0,
        'total_score': 0
    }
    save_users_db()

def approve_user(user_id):
    user_id_str = str(user_id)
    if user_id_str in users_db:
        users_db[user_id_str]['allowed'] = True
        users_db[user_id_str]['approved_date'] = datetime.now().isoformat()
        save_users_db()
        return True
    return False

# ============= RUXSAT SO'ROVI - 1 ADMINGA =============
async def request_access(message: Message):
    user = message.from_user
    user_id = user.id
    
    if str(user_id) not in users_db:
        add_user(user_id, user.username, user.first_name, user.last_name)
    
    pending_requests[user_id] = True
    
    # SODDA keyboard
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ruxsat berish", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")
            ]
        ]
    )
    
    # HTML format - XAVFSIZ!
    user_info = (
        f"🆕 <b>Yangi foydalanuvchi</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"👤 Ism: {user.first_name}\n"
    )
    if user.username:
        user_info += f"📱 Username: @{user.username}\n"
    user_info += f"📅 Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # FAQAT 1 ADMINGA yuboramiz
    try:
        await bot.send_message(ADMIN_ID, user_info, reply_markup=keyboard, parse_mode='HTML')
        logger.info(f"✅ Admin {ADMIN_ID} ga xabar yuborildi")
    except Exception as e:
        logger.error(f"❌ Admin ga xabar yuborilmadi: {e}")
    
    await message.answer(
        "👋 Xush kelibsiz!\n\n"
        "📝 Botdan foydalanish uchun admin ruxsati talab qilinadi.\n"
        "✅ So'rovingiz adminga yuborildi.\n"
        "⏳ Iltimos, tasdiqlashni kuting..."
    )

# ============= ADMIN CALLBACK - 1 ADMIN =============
@dp.callback_query(F.data.startswith('approve_'))
async def approve_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    user_id = int(callback.data.split('_')[1])
    
    if approve_user(user_id):
        await callback.answer("✅ Ruxsat berildi!", show_alert=True)
        await callback.message.edit_text(callback.message.text + "\n\n✅ <b>Ruxsat berildi!</b>", parse_mode='HTML')
        
        try:
            await bot.send_message(user_id, "✅ <b>Tabriklaymiz!</b>\n\nSizga ruxsat berildi!\n/quiz - boshlash", parse_mode='HTML')
        except: pass
    
    if user_id in pending_requests:
        del pending_requests[user_id]

@dp.callback_query(F.data.startswith('reject_'))
async def reject_callback(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    user_id = int(callback.data.split('_')[1])
    await callback.answer("❌ Rad etildi!", show_alert=True)
    await callback.message.edit_text(callback.message.text + "\n\n❌ <b>Rad etildi!</b>", parse_mode='HTML')
    
    if user_id in pending_requests:
        del pending_requests[user_id]

# ============= ADMIN PANEL - 1 ADMIN =============
@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer(f"❌ Siz admin emassiz!\nSizning ID: {message.from_user.id}")
        return
    
    total_users = len(users_db)
    allowed_users = sum(1 for u in users_db.values() if u.get('allowed', False))
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="📋 Foydalanuvchilar", callback_data="admin_users")],
            [InlineKeyboardButton(text="⏳ Kutilayotgan", callback_data="admin_pending")],
            [InlineKeyboardButton(text="📚 Test yaratish", callback_data="back_to_test_menu")]
        ]
    )
    
    await message.answer(
        f"👨‍💼 <b>Admin Panel</b>\n\n"
        f"👥 Umumiy: {total_users}\n"
        f"✅ Ruxsat: {allowed_users}\n"
        f"⏳ Kutilgan: {len(pending_requests)}",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

# ============= TEST YARATISH - 1 ADMIN =============
class TestCreationStates(StatesGroup):
    waiting_book_name = State()
    waiting_book_description = State()
    waiting_unit_name = State()
    waiting_unit_description = State()
    waiting_question_text = State()
    waiting_question_audio = State()
    waiting_options = State()
    waiting_correct_answer = State()
    waiting_explanation = State()

def load_books_db():
    global books_db
    try:
        if os.path.exists(BOOKS_DB_FILE):
            with open(BOOKS_DB_FILE, 'r', encoding='utf-8') as f:
                books_db = json.load(f)
    except: books_db = {}

def save_books_db():
    with open(BOOKS_DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(books_db, f, ensure_ascii=False, indent=4)

@dp.message(Command("create_test"))
@admin_required
async def cmd_create_test(message: Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Yangi kitob", callback_data="create_new_book")],
            [InlineKeyboardButton(text="📖 Mavjud kitob", callback_data="select_existing_book")],
            [InlineKeyboardButton(text="◀️ Admin panel", callback_data="back_to_admin")]
        ]
    )
    
    await message.answer(
        "📚 <b>TEST YARATISH</b>\n\n"
        "Tanlang:",
        reply_markup=keyboard,
        parse_mode='HTML'
    )

@dp.callback_query(F.data == "back_to_test_menu")
@admin_callback_required
async def back_to_test_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await cmd_create_test(callback.message, state)

@dp.callback_query(F.data == "back_to_admin")
@admin_callback_required
async def back_to_admin(callback: CallbackQuery):
    await callback.message.delete()
    await admin_panel(callback.message)

# ============= START =============
@dp.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    
    if is_admin(user_id):
        await message.answer(
            "👨‍💼 <b>Admin paneliga xush kelibsiz!</b>\n\n"
            "/admin - Admin panel\n"
            "/create_test - Test yaratish",
            parse_mode='HTML'
        )
        return
    
    if is_user_allowed(user_id):
        await message.answer(
            "🎧 <b>Audio Quiz Bot</b>\n\n"
            "Quiz boshlash: /quiz",
            parse_mode='HTML'
        )
    else:
        await request_access(message)

@dp.message(Command("quiz"))
async def quiz(message: Message):
    user_id = message.from_user.id
    
    if not is_user_allowed(user_id) and not is_admin(user_id):
        await message.answer("❌ Ruxsat yo'q! /start ni bosing.")
        return
    
    await message.answer("🎵 Quiz boshlanmoqda... (demo)")

# ============= DEFAULT =============
@dp.message()
async def echo(message: Message):
    user_id = message.from_user.id
    
    if not is_user_allowed(user_id) and not is_admin(user_id):
        await message.answer("❌ Ruxsat yo'q! /start ni bosing.")
    else:
        await message.answer("/quiz - boshlash\n/help - yordam")

# ============= STARTUP =============
async def on_startup():
    logger.info("=" * 50)
    logger.info("Bot ishga tushmoqda...")
    logger.info("=" * 50)
    
    load_users_db()
    load_books_db()
    
    logger.info(f"👨‍💼 Admin ID: {ADMIN_ID}")
    logger.info(f"👥 Foydalanuvchilar: {len(users_db)}")
    logger.info(f"📚 Kitoblar: {len(books_db)}")
    
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook o'chirildi")
    except: pass
    
    bot_info = await bot.get_me()
    logger.info(f"✅ Bot: @{bot_info.username}")
    
    # Admin ga xabar
    try:
        await bot.send_message(ADMIN_ID, "✅ <b>Bot ishga tushdi!</b>", parse_mode='HTML')
        logger.info("✅ Admin ga xabar yuborildi")
    except:
        logger.error("❌ Admin ga xabar yuborilmadi")
    
    logger.info("=" * 50)

async def main():
    await on_startup()
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    asyncio.run(main())