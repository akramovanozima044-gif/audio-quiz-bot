import os
import logging
import asyncio
import json
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import F
import uuid
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class TestCreationStates(StatesGroup):
    # Kitob yaratish
    waiting_book_name = State()
    waiting_book_description = State()
    
    # Kitob tanlash
    selecting_book = State()
    
    # Unit yaratish
    waiting_unit_name = State()
    waiting_unit_description = State()
    
    # Unit tanlash
    selecting_unit = State()
    
    # Test yaratish
    waiting_question_text = State()
    waiting_question_audio = State()
    waiting_options = State()
    waiting_correct_answer = State()
    waiting_explanation = State()

# Token olish
TOKEN = os.environ.get('BOT_TOKEN')

# Admin ID lari - o'zingizning Telegram ID ni qo'ying
ADMIN_IDS = [7923179229]  # BU YERGA O'ZINGIZNING TELEGRAM ID NI YOZING

if not TOKEN:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        TOKEN = os.getenv('BOT_TOKEN')
    except ImportError:
        pass

if not TOKEN:
    print("❌ XATO: BOT_TOKEN topilmadi!")
    exit(1)

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Bot va Dispatcher yaratish
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ============= RUXSATNOMA TIZIMI =============
# Foydalanuvchilar ma'lumotlar bazasi (JSON fayl)
USERS_DB_FILE = 'users_db.json'

# Foydalanuvchilar holati
users_db = {}
pending_requests = {}  # Kutilayotgan so'rovlar

BOOKS_DB_FILE = 'books_db.json'

# Kitoblar va testlar bazasi
books_db = {}

def load_books_db():
    """Kitoblar ma'lumotlarini yuklash"""
    global books_db
    try:
        if os.path.exists(BOOKS_DB_FILE):
            with open(BOOKS_DB_FILE, 'r', encoding='utf-8') as f:
                books_db = json.load(f)
            logger.info(f"✅ {len(books_db)} ta kitob ma'lumotlari yuklandi")
        else:
            books_db = {}
            save_books_db()
            logger.info("🆕 Yangi kitoblar bazasi yaratildi")
    except Exception as e:
        logger.error(f"❌ Kitoblarni yuklashda xatolik: {e}")
        books_db = {}

def save_books_db():
    """Kitoblar ma'lumotlarini saqlash"""
    try:
        with open(BOOKS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(books_db, f, ensure_ascii=False, indent=4)
        logger.info(f"💾 {len(books_db)} ta kitob ma'lumotlari saqlandi")
    except Exception as e:
        logger.error(f"❌ Kitoblarni saqlashda xatolik: {e}")

# ============= ADMIN TEKSHIRISH =============
def admin_required(handler):
    """Admin huquqini tekshirish (message uchun)"""
    async def wrapper(message: Message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            await message.reply("❌ Bu funksiya faqat adminlar uchun!")
            return
        return await handler(message, *args, **kwargs)
    return wrapper

def admin_callback_required(handler):
    """Admin huquqini tekshirish (callback uchun)"""
    async def wrapper(callback: CallbackQuery, *args, **kwargs):
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Bu funksiya faqat adminlar uchun!", show_alert=True)
            return
        await callback.answer()
        return await handler(callback, *args, **kwargs)
    return wrapper

def load_users_db():
    """Foydalanuvchilar ma'lumotlarini yuklash"""
    global users_db
    try:
        if os.path.exists(USERS_DB_FILE):
            with open(USERS_DB_FILE, 'r', encoding='utf-8') as f:
                users_db = json.load(f)
            logger.info(f"✅ {len(users_db)} ta foydalanuvchi ma'lumotlari yuklandi")
        else:
            users_db = {}
            logger.info("🆕 Yangi ma'lumotlar bazasi yaratildi")
    except Exception as e:
        logger.error(f"❌ Ma'lumotlarni yuklashda xatolik: {e}")
        users_db = {}

def save_users_db():
    """Foydalanuvchilar ma'lumotlarini saqlash"""
    try:
        with open(USERS_DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(users_db, f, ensure_ascii=False, indent=4)
        logger.info(f"💾 {len(users_db)} ta foydalanuvchi ma'lumotlari saqlandi")
    except Exception as e:
        logger.error(f"❌ Ma'lumotlarni saqlashda xatolik: {e}")

def is_user_allowed(user_id):
    """Foydalanuvchi ruxsatini tekshirish"""
    return str(user_id) in users_db and users_db[str(user_id)]['allowed']

def is_admin(user_id):
    """Foydalanuvchi admin ekanligini tekshirish"""
    return user_id in ADMIN_IDS

def add_user(user_id, username, first_name, last_name):
    """Yangi foydalanuvchi qo'shish"""
    user_id_str = str(user_id)
    users_db[user_id_str] = {
        'user_id': user_id,
        'username': username,
        'first_name': first_name,
        'last_name': last_name,
        'joined_date': datetime.now().isoformat(),
        'allowed': False,  # Avval ruxsat yo'q
        'is_active': True,
        'quizzes_played': 0,
        'total_score': 0
    }
    save_users_db()
    logger.info(f"👤 Yangi foydalanuvchi qo'shildi: @{username} ({user_id})")

def approve_user(user_id):
    """Foydalanuvchiga ruxsat berish"""
    user_id_str = str(user_id)
    if user_id_str in users_db:
        users_db[user_id_str]['allowed'] = True
        users_db[user_id_str]['approved_date'] = datetime.now().isoformat()
        save_users_db()
        logger.info(f"✅ Foydalanuvchiga ruxsat berildi: {user_id}")
        return True
    return False

def reject_user(user_id):
    """Foydalanuvchini rad etish"""
    user_id_str = str(user_id)
    if user_id_str in users_db:
        users_db[user_id_str]['allowed'] = False
        users_db[user_id_str]['rejected_date'] = datetime.now().isoformat()
        save_users_db()
        logger.info(f"❌ Foydalanuvchi rad etildi: {user_id}")
        return True
    return False

def remove_user(user_id):
    """Foydalanuvchini o'chirish"""
    user_id_str = str(user_id)
    if user_id_str in users_db:
        del users_db[user_id_str]
        save_users_db()
        logger.info(f"🗑️ Foydalanuvchi o'chirildi: {user_id}")
        return True
    return False

def update_user_stats(user_id, score=0):
    """Foydalanuvchi statistikasini yangilash"""
    user_id_str = str(user_id)
    if user_id_str in users_db:
        users_db[user_id_str]['quizzes_played'] += 1
        users_db[user_id_str]['total_score'] += score
        save_users_db()

# ============= RUXSAT TEKSHIRISH DECORATOR =============
def access_required(handler):
    """Foydalanuvchi ruxsatini tekshirish decoratori"""
    async def wrapper(message: types.Message):
        user_id = message.from_user.id
        
        # Adminlar har doim ruxsat
        if is_admin(user_id):
            return await handler(message)
        
        # Ruxsat tekshirish
        if not is_user_allowed(user_id):
            # Ruxsat so'rovi yuborilganmi tekshirish
            if user_id in pending_requests:
                await message.reply(
                    "⏳ Sizning so'rovingiz admin tomonidan ko'rib chiqilmoqda.\n"
                    "Iltimos, biroz kuting..."
                )
            else:
                # Ruxsat so'rovi yuborish
                await request_access(message)
            return
        
        # Ruxsat berilgan - handler ni ishga tushirish
        return await handler(message)
    return wrapper

# ============= RUXSAT SO'ROVI =============
async def request_access(message: types.Message):
    """Admin ga ruxsat so'rovi yuborish"""
    user = message.from_user
    user_id = user.id
    
    # Foydalanuvchi ma'lumotlarini saqlash
    if str(user_id) not in users_db:
        add_user(user_id, user.username, user.first_name, user.last_name)
    
    # So'rovni yuborganini belgilash
    pending_requests[user_id] = True
    
    # Admin uchun tugmalar
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ruxsat berish", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")
            ],
            [
                InlineKeyboardButton(text="👤 Profil", callback_data=f"profile_{user_id}")
            ]
        ]
    )
    
    # Foydalanuvchi ma'lumotlari
    user_info = (
        f"🆕 **Yangi foydalanuvchi**\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"👤 Ism: {user.first_name}\n"
    )
    
    if user.last_name:
        user_info += f"👥 Familiya: {user.last_name}\n"
    if user.username:
        user_info += f"📱 Username: @{user.username}\n"
    
    user_info += f"📅 Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    # Barcha adminlarga xabar yuborish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                user_info,
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"❌ Admin {admin_id} ga xabar yuborilmadi: {e}")
    
    # Foydalanuvchiga xabar
    await message.reply(
        "👋 Xush kelibsiz!\n\n"
        "📝 Botdan foydalanish uchun admin ruxsati talab qilinadi.\n"
        "✅ Sizning so'rovingiz adminga yuborildi.\n"
        "⏳ Iltimos, tasdiqlashni kuting...",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔄 Holatni tekshirish", callback_data="check_status")]
            ]
        )
    )

# ============= ADMIN CALLBACKLAR =============
@dp.callback_query(F.data.startswith('approve_'))
async def approve_callback(callback: CallbackQuery):
    """Foydalanuvchiga ruxsat berish"""
    admin_id = callback.from_user.id
    
    # Admin tekshirish
    if not is_admin(admin_id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    user_id = int(callback.data.split('_')[1])
    
    # Ruxsat berish
    if approve_user(user_id):
        await callback.answer("✅ Ruxsat berildi!", show_alert=True)
        
        # Xabarni yangilash
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ **Ruxsat berildi!**",
            parse_mode='Markdown'
        )
        
        # Foydalanuvchiga xabar yuborish
        try:
            await bot.send_message(
                user_id,
                "✅ **Tabriklaymiz!**\n\n"
                "Sizga botdan foydalanish uchun ruxsat berildi.\n"
                "Botdan to'liq foydalanishingiz mumkin.\n\n"
                "Boshlash uchun /quiz buyrug'ini yuboring yoki /start ni bosing.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"❌ Foydalanuvchiga xabar yuborilmadi: {e}")
    else:
        await callback.answer("❌ Foydalanuvchi topilmadi!", show_alert=True)
    
    # So'rovni o'chirish
    if user_id in pending_requests:
        del pending_requests[user_id]

@dp.callback_query(F.data.startswith('reject_'))
async def reject_callback(callback: CallbackQuery):
    """Foydalanuvchini rad etish"""
    admin_id = callback.from_user.id
    
    if not is_admin(admin_id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    user_id = int(callback.data.split('_')[1])
    
    # Rad etish
    if reject_user(user_id):
        await callback.answer("❌ Rad etildi!", show_alert=True)
        
        # Xabarni yangilash
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ **Rad etildi!**",
            parse_mode='Markdown'
        )
        
        # Foydalanuvchiga xabar yuborish
        try:
            await bot.send_message(
                user_id,
                "❌ **Afsus!**\n\n"
                "Sizning so'rovingiz rad etildi.\n"
                "Agar bu xato bo'lsa, admin bilan bog'lanishingiz mumkin.",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"❌ Foydalanuvchiga xabar yuborilmadi: {e}")
    else:
        await callback.answer("❌ Foydalanuvchi topilmadi!", show_alert=True)
    
    # So'rovni o'chirish
    if user_id in pending_requests:
        del pending_requests[user_id]

@dp.callback_query(F.data == "check_status")
async def check_status_callback(callback: CallbackQuery):
    """Foydalanuvchi holatini tekshirish"""
    user_id = callback.from_user.id
    
    if is_user_allowed(user_id):
        await callback.answer("✅ Sizga ruxsat berilgan!", show_alert=True)
        await callback.message.edit_text(
            "✅ **Ruxsat berilgan!**\n\n"
            "Botdan to'liq foydalanishingiz mumkin.\n"
            "Boshlash uchun /quiz ni bosing."
        )
    elif str(user_id) in users_db:
        if user_id in pending_requests:
            await callback.answer("⏳ So'rovingiz ko'rib chiqilmoqda...", show_alert=True)
        else:
            await callback.answer("❌ Sizga ruxsat berilmagan!", show_alert=True)
    else:
        await callback.answer("❌ Siz ro'yxatdan o'tmagansiz!", show_alert=True)
        await request_access(callback.message)

# ============= ADMIN PANEL =============
@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    """Admin panel - asosiy menyu"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.reply("❌ Siz admin emassiz!")
        return
    
    # Statistika
    total_users = len(users_db)
    allowed_users = sum(1 for u in users_db.values() if u['allowed'])
    pending_count = len(pending_requests)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="👥 Foydalanuvchilar ro'yxati", callback_data="admin_users_list")],
            [InlineKeyboardButton(text="⏳ Kutilayotgan so'rovlar", callback_data="admin_pending")],
            [InlineKeyboardButton(text="✅ Ruxsat berilganlar", callback_data="admin_allowed")],
            [InlineKeyboardButton(text="❌ Ruxsat berilmaganlar", callback_data="admin_not_allowed")],
            [InlineKeyboardButton(text="🗑️ Foydalanuvchi o'chirish", callback_data="admin_remove_menu")],
            [InlineKeyboardButton(text="📢 Xabar yuborish", callback_data="admin_broadcast_menu")],
            [InlineKeyboardButton(text="🔄 Ma'lumotlarni yangilash", callback_data="admin_refresh")]
        ]
    )
    
    await message.reply(
        f"👨‍💼 **Admin Panel**\n\n"
        f"📊 **Umumiy statistika:**\n"
        f"👥 Umumiy foydalanuvchilar: {total_users}\n"
        f"✅ Ruxsat berilgan: {allowed_users}\n"
        f"⏳ Kutilayotgan so'rovlar: {pending_count}\n"
        f"❌ Ruxsat berilmagan: {total_users - allowed_users}\n\n"
        f"🆔 Admin ID: `{user_id}`\n"
        f"🕐 So'ngi yangilanish: {datetime.now().strftime('%H:%M:%S')}",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# ============= ADMIN STATISTIKA =============
@dp.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery):
    """Batafsil statistika"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    total_users = len(users_db)
    allowed_users = sum(1 for u in users_db.values() if u['allowed'])
    
    # Bugun qo'shilganlar
    today = datetime.now().strftime('%Y-%m-%d')
    today_users = sum(1 for u in users_db.values() 
                     if u.get('joined_date', '').startswith(today))
    
    # Hafta qo'shilganlar
    from datetime import timedelta
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    week_users = sum(1 for u in users_db.values() 
                    if u.get('joined_date', '')[:10] >= week_ago)
    
    # O'yin statistikasi
    total_quizzes = sum(u.get('quizzes_played', 0) for u in users_db.values())
    total_scores = sum(u.get('total_score', 0) for u in users_db.values())
    avg_score = total_scores / max(total_users, 1)
    
    # Eng yaxshi natija
    best_user = None
    best_score = 0
    for u in users_db.values():
        if u.get('total_score', 0) > best_score:
            best_score = u.get('total_score', 0)
            best_user = u
    
    stats_text = (
        f"📊 **BATAFSIL STATISTIKA**\n\n"
        f"👥 **FOYDALANUVCHILAR:**\n"
        f"• Umumiy: {total_users}\n"
        f"• Ruxsat berilgan: {allowed_users}\n"
        f"• Ruxsat berilmagan: {total_users - allowed_users}\n"
        f"• Bugun qo'shilgan: {today_users}\n"
        f"• Bu hafta qo'shilgan: {week_users}\n\n"
        
        f"🎮 **O'YIN STATISTIKASI:**\n"
        f"• Jami o'yinlar: {total_quizzes}\n"
        f"• Jami to'plangan ball: {total_scores}\n"
        f"• O'rtacha ball: {avg_score:.1f}\n\n"
        
        f"🏆 **ENG YAXSHI NATIJA:**\n"
    )
    
    if best_user:
        stats_text += (
            f"• Foydalanuvchi: {best_user.get('first_name', 'Noma\'lum')}\n"
            f"• Ball: {best_score}\n"
            f"• O'yinlar: {best_user.get('quizzes_played', 0)}\n"
        )
    else:
        stats_text += "• Hali hech kim o'ynamagan\n"
    
    stats_text += f"\n⏳ Kutilayotgan so'rovlar: {len(pending_requests)}"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Ortga", callback_data="back_to_admin")]
        ]
    )
    
    await callback.message.edit_text(stats_text, parse_mode='Markdown', reply_markup=keyboard)
    await callback.answer()


# ============= FOYDALANUVCHILAR RO'YXATI =============
@dp.callback_query(F.data == "admin_users_list")
async def admin_users_list_callback(callback: CallbackQuery):
    """Foydalanuvchilar ro'yxati"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    if not users_db:
        await callback.answer("📭 Hali foydalanuvchilar yo'q", show_alert=True)
        return
    
    # So'nggi 10 foydalanuvchi
    users_list = list(users_db.values())
    users_list.sort(key=lambda x: x.get('joined_date', ''), reverse=True)
    
    text = "👥 **SO'NGI FOYDALANUVCHILAR:**\n\n"
    
    for i, user in enumerate(users_list[:10], 1):
        name = user.get('first_name', 'Noma\'lum')
        username = f"@{user.get('username')}" if user.get('username') else 'No username'
        allowed = "✅" if user.get('allowed') else "❌"
        joined = user.get('joined_date', '')[5:16] if user.get('joined_date') else 'Noma\'lum'
        
        text += f"{i}. {allowed} {name} {username}\n"
        text += f"   🆔 `{user.get('user_id')}` | 📅 {joined}\n"
    
    text += f"\n📊 Jami: {len(users_db)} ta foydalanuvchi"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Ortga", callback_data="back_to_admin")]
        ]
    )
    
    await callback.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
    await callback.answer()

# ============= KUTILAYOTGAN SO'ROVLAR =============
@dp.callback_query(F.data == "admin_pending")
async def admin_pending_callback(callback: CallbackQuery):
    """Kutilayotgan so'rovlar ro'yxati"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    if not pending_requests:
        await callback.answer("⏳ Kutilayotgan so'rovlar yo'q", show_alert=True)
        return
    
    text = "⏳ **KUTILAYOTGAN SO'ROVLAR:**\n\n"
    
    for user_id in list(pending_requests.keys())[:10]:
        user_id_str = str(user_id)
        if user_id_str in users_db:
            user = users_db[user_id_str]
            name = user.get('first_name', 'Noma\'lum')
            username = f"@{user.get('username')}" if user.get('username') else 'No username'
            joined = user.get('joined_date', '')[5:16] if user.get('joined_date') else 'Noma\'lum'
            
            text += f"• {name} {username}\n"
            text += f"  🆔 `{user_id}` | 📅 {joined}\n\n"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Ortga", callback_data="back_to_admin")]
        ]
    )
    
    await callback.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
    await callback.answer()

# ============= RUXSAT BERILGANLAR =============
@dp.callback_query(F.data == "admin_allowed")
async def admin_allowed_callback(callback: CallbackQuery):
    """Ruxsat berilgan foydalanuvchilar"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    allowed_users_list = [u for u in users_db.values() if u.get('allowed')]
    
    if not allowed_users_list:
        await callback.answer("✅ Ruxsat berilgan foydalanuvchilar yo'q", show_alert=True)
        return
    
    allowed_users_list.sort(key=lambda x: x.get('approved_date', ''), reverse=True)
    
    text = "✅ **RUXSAT BERILGANLAR:**\n\n"
    
    for i, user in enumerate(allowed_users_list[:10], 1):
        name = user.get('first_name', 'Noma\'lum')
        username = f"@{user.get('username')}" if user.get('username') else 'No username'
        approved = user.get('approved_date', '')[5:16] if user.get('approved_date') else 'Noma\'lum'
        quizzes = user.get('quizzes_played', 0)
        score = user.get('total_score', 0)
        
        text += f"{i}. {name} {username}\n"
        text += f"   🆔 `{user.get('user_id')}` | 📅 {approved}\n"
        text += f"   🎮 {quizzes} o'yin | 🏆 {score} ball\n\n"
    
    text += f"\n📊 Jami: {len(allowed_users_list)} ta foydalanuvchi"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Ortga", callback_data="back_to_admin")]
        ]
    )
    
    await callback.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
    await callback.answer()

# ============= RUXSAT BERILMAGANLAR =============
@dp.callback_query(F.data == "admin_not_allowed")
async def admin_not_allowed_callback(callback: CallbackQuery):
    """Ruxsat berilmagan foydalanuvchilar"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    not_allowed_users = [u for u in users_db.values() if not u.get('allowed')]
    
    if not not_allowed_users:
        await callback.answer("❌ Ruxsat berilmagan foydalanuvchilar yo'q", show_alert=True)
        return
    
    text = "❌ **RUXSAT BERILMAGANLAR:**\n\n"
    
    for i, user in enumerate(not_allowed_users[:10], 1):
        name = user.get('first_name', 'Noma\'lum')
        username = f"@{user.get('username')}" if user.get('username') else 'No username'
        joined = user.get('joined_date', '')[5:16] if user.get('joined_date') else 'Noma\'lum'
        
        text += f"{i}. {name} {username}\n"
        text += f"   🆔 `{user.get('user_id')}` | 📅 {joined}\n\n"
    
    text += f"\n📊 Jami: {len(not_allowed_users)} ta foydalanuvchi"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Ortga", callback_data="back_to_admin")]
        ]
    )
    
    await callback.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
    await callback.answer()

# ============= FOYDALANUVCHI O'CHIRISH =============
@dp.callback_query(F.data == "admin_remove_menu")
async def admin_remove_menu_callback(callback: CallbackQuery):
    """Foydalanuvchi o'chirish menyusi"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    text = "🗑️ **FOYDALANUVCHI O'CHIRISH**\n\n"
    text += "Foydalanuvchini o'chirish uchun uning ID sini kiriting:\n\n"
    text += "Format: `/remove_user 123456789`"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Ortga", callback_data="back_to_admin")]
        ]
    )
    
    await callback.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
    await callback.answer()

@dp.message(Command("remove_user"))
async def remove_user_command(message: types.Message):
    """Foydalanuvchini o'chirish"""
    if not is_admin(message.from_user.id):
        await message.reply("❌ Siz admin emassiz!")
        return
    
    try:
        user_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.reply("❌ Noto'g'ri format! `/remove_user 123456789`")
        return
    
    if remove_user(user_id):
        await message.reply(f"✅ Foydalanuvchi `{user_id}` o'chirildi!", parse_mode='Markdown')
    else:
        await message.reply(f"❌ Foydalanuvchi `{user_id}` topilmadi!", parse_mode='Markdown')

# ============= XABAR YUBORISH =============
@dp.callback_query(F.data == "admin_broadcast_menu")
async def admin_broadcast_menu_callback(callback: CallbackQuery):
    """Xabar yuborish menyusi"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    text = "📢 **XABAR YUBORISH**\n\n"
    text += "Barcha foydalanuvchilarga xabar yuborish uchun:\n\n"
    text += "Format: `/broadcast Xabaringiz`\n\n"
    text += "Faqat ruxsat berilganlarga yuborish uchun:\n"
    text += "Format: `/broadcast_allowed Xabaringiz`"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Ortga", callback_data="back_to_admin")]
        ]
    )
    
    await callback.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
    await callback.answer()

@dp.message(Command("broadcast"))
async def broadcast_command(message: types.Message):
    """Barcha foydalanuvchilarga xabar yuborish"""
    if not is_admin(message.from_user.id):
        await message.reply("❌ Siz admin emassiz!")
        return
    
    try:
        broadcast_text = message.text.split(' ', 1)[1]
    except IndexError:
        await message.reply("❌ Xabar matnini kiriting! `/broadcast Salom hammaga!`")
        return
    
    sent_count = 0
    failed_count = 0
    
    status_msg = await message.reply("📤 Xabar yuborilmoqda...")
    
    for user_id_str, user_data in users_db.items():
        try:
            await bot.send_message(
                int(user_id_str),
                f"📢 **Admin xabari:**\n\n{broadcast_text}",
                parse_mode='Markdown'
            )
            sent_count += 1
            await asyncio.sleep(0.05)  # Rate limiting
        except Exception as e:
            failed_count += 1
            logger.error(f"❌ Xabar yuborilmadi {user_id_str}: {e}")
    
    await status_msg.edit_text(
        f"✅ Xabar yuborildi!\n\n"
        f"📤 Yuborilgan: {sent_count}\n"
        f"❌ Yuborilmagan: {failed_count}"
    )

@dp.message(Command("broadcast_allowed"))
async def broadcast_allowed_command(message: types.Message):
    """Faqat ruxsat berilgan foydalanuvchilarga xabar yuborish"""
    if not is_admin(message.from_user.id):
        await message.reply("❌ Siz admin emassiz!")
        return
    
    try:
        broadcast_text = message.text.split(' ', 1)[1]
    except IndexError:
        await message.reply("❌ Xabar matnini kiriting! `/broadcast_allowed Salom!`")
        return
    
    sent_count = 0
    failed_count = 0
    
    status_msg = await message.reply("📤 Xabar yuborilmoqda (faqat ruxsat berilganlarga)...")
    
    for user_id_str, user_data in users_db.items():
        if user_data.get('allowed'):
            try:
                await bot.send_message(
                    int(user_id_str),
                    f"📢 **Admin xabari:**\n\n{broadcast_text}",
                    parse_mode='Markdown'
                )
                sent_count += 1
                await asyncio.sleep(0.05)
            except Exception as e:
                failed_count += 1
                logger.error(f"❌ Xabar yuborilmadi {user_id_str}: {e}")
    
    await status_msg.edit_text(
        f"✅ Xabar yuborildi (faqat ruxsat berilganlarga)!\n\n"
        f"📤 Yuborilgan: {sent_count}\n"
        f"❌ Yuborilmagan: {failed_count}"
    )

# ============= MA'LUMOTLARNI YANGILASH =============
@dp.callback_query(F.data == "admin_refresh")
async def admin_refresh_callback(callback: CallbackQuery):
    """Ma'lumotlarni yangilash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    # Ma'lumotlar bazasini qayta yuklash
    load_users_db()
    
    await callback.answer("✅ Ma'lumotlar yangilandi!", show_alert=True)
    
    # Admin panelga qaytish
    await admin_panel(callback.message)

# ============= ORTGA QAYTISH =============
@dp.callback_query(F.data == "back_to_admin")
async def back_to_admin_callback(callback: CallbackQuery):
    """Admin panelga qaytish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    # Yangi xabar sifatida admin panelni yuborish
    await callback.message.delete()
    await admin_panel(callback.message)

# ============= FOYDALANUVCHI PROFILINI KO'RISH (ADMIN) =============
@dp.message(Command("user_info"))
async def user_info_command(message: types.Message):
    """Foydalanuvchi ma'lumotlarini ko'rish"""
    if not is_admin(message.from_user.id):
        await message.reply("❌ Siz admin emassiz!")
        return
    
    try:
        user_id = int(message.text.split()[1])
    except (IndexError, ValueError):
        await message.reply("❌ Noto'g'ri format! `/user_info 123456789`")
        return
    
    user_id_str = str(user_id)
    if user_id_str not in users_db:
        await message.reply(f"❌ Foydalanuvchi `{user_id}` topilmadi!", parse_mode='Markdown')
        return
    
    user = users_db[user_id_str]
    
    text = (
        f"👤 **Foydalanuvchi ma'lumotlari**\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"👤 Ism: {user.get('first_name', 'Noma\'lum')}\n"
    )
    
    if user.get('last_name'):
        text += f"👥 Familiya: {user['last_name']}\n"
    if user.get('username'):
        text += f"📱 Username: @{user['username']}\n"
    
    text += f"\n📅 Ro'yxatdan o'tgan: {user.get('joined_date', 'Noma\'lum')[:19]}\n"
    
    if user.get('approved_date'):
        text += f"✅ Ruxsat berilgan: {user['approved_date'][:19]}\n"
    elif user.get('rejected_date'):
        text += f"❌ Rad etilgan: {user['rejected_date'][:19]}\n"
    else:
        text += f"⏳ Ruxsat: Kutilmoqda\n"
    
    text += (
        f"\n🎮 **O'yin statistikasi:**\n"
        f"📊 O'ynalgan quizlar: {user.get('quizzes_played', 0)}\n"
        f"🏆 Umumiy ball: {user.get('total_score', 0)}\n"
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ruxsat berish", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")
            ],
            [
                InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"admin_remove_{user_id}"),
                InlineKeyboardButton(text="◀️ Ortga", callback_data="back_to_admin")
            ]
        ]
    )
    
    await message.reply(text, parse_mode='Markdown', reply_markup=keyboard)

@dp.callback_query(F.data.startswith('admin_remove_'))
async def admin_remove_callback(callback: CallbackQuery):
    """Admin panelidan foydalanuvchini o'chirish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Siz admin emassiz!", show_alert=True)
        return
    
    user_id = int(callback.data.split('_')[2])
    
    if remove_user(user_id):
        await callback.answer(f"✅ Foydalanuvchi o'chirildi!", show_alert=True)
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ **Foydalanuvchi o'chirildi!**"
        )
    else:
        await callback.answer(f"❌ Foydalanuvchi topilmadi!", show_alert=True)

# ============= QUIZ FUNKSIYALARI (faqat ruxsat berilganlar uchun) =============
QUIZ_DATA = [
    {
        "question": "Bu qaysi qo'shiq?",
        "audio_file": "audio1.mp3",
        "options": ["Sevgi qo'shig'i", "Vatan qo'shig'i", "Dostlik qo'shig'i", "Tabiat qo'shig'i"],
        "correct_answer": 0
    },
    {
        "question": "Bu qaysi artistning qo'shig'i?",
        "audio_file": "audio2.mp3",
        "options": ["Shahzoda", "Jaloliddin Ahmadaliyev", "Ozoda", "Rayhon"],
        "correct_answer": 1
    }
]

# Foydalanuvchilarning quiz holati
user_quiz_states = {}

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    
    # Admin uchun maxsus xabar
    if is_admin(user_id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Admin panel", callback_data="admin_panel")],
                [InlineKeyboardButton(text="Quizni boshlash", callback_data="start_quiz")]
            ]
        )
        await message.reply(
            "👨‍💼 **Admin paneliga xush kelibsiz!**\n\n"
            "Siz admin sifatida barcha funksiyalardan foydalana olasiz.",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
        return
    
    # Oddiy foydalanuvchilar
    if is_user_allowed(user_id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Quizni boshlash 🎵", callback_data="start_quiz")]
            ]
        )
        await message.reply(
            "🎧 Audio Quiz Botga xush kelibsiz!\n\n"
            "Quizni boshlash uchun tugmani bosing yoki /quiz buyrug'ini yuboring.",
            reply_markup=keyboard
        )
    else:
        # Ruxsat so'rovi
        await request_access(message)

@dp.message(Command("quiz"))
@access_required
async def start_quiz_command(message: types.Message):
    """Quiz boshlash - faqat ruxsat berilganlar uchun"""
    user_id = message.from_user.id
    
    if user_id in user_quiz_states:
        # Agar quiz davom etayotgan bo'lsa
        await message.reply("Sizda davom etayotgan quiz bor! Avval uni tugating.")
        return
    
    user_quiz_states[user_id] = {
        'current_question': 0,
        'score': 0,
        'total_questions': len(QUIZ_DATA)
    }
    await send_question(user_id, message.chat.id)

async def send_question(user_id, chat_id):
    """Savol yuborish"""
    state = user_quiz_states.get(user_id)
    if not state:
        return
    
    question_index = state['current_question']
    
    if question_index >= state['total_questions']:
        await finish_quiz(user_id, chat_id)
        return
    
    question = QUIZ_DATA[question_index]
    
    await bot.send_message(
        chat_id,
        f"🎵 Savol {question_index + 1}/{state['total_questions']}\n\n"
        f"{question['question']}\n\n"
        f"🔊 Audio fragment yuborilmoqda... (demo rejim)"
    )
    
    # Variantlar tugmalari
    buttons = []
    for i, option in enumerate(question['options']):
        buttons.append([InlineKeyboardButton(
            text=option, 
            callback_data=f"answer_{question_index}_{i}"
        )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await bot.send_message(chat_id, "Variantlardan birini tanlang:", reply_markup=keyboard)

@dp.callback_query(F.data.startswith('answer_'))
async def check_answer(callback: CallbackQuery):
    """Javobni tekshirish"""
    user_id = callback.from_user.id
    
    # Ruxsat tekshirish
    if not is_user_allowed(user_id) and not is_admin(user_id):
        await callback.answer("❌ Sizga ruxsat berilmagan!", show_alert=True)
        return
    
    if user_id not in user_quiz_states:
        await callback.answer("Quiz hozir boshlanmagan!", show_alert=True)
        return
    
    data_parts = callback.data.split('_')
    if len(data_parts) != 3:
        await callback.answer("Xatolik yuz berdi")
        return
    
    _, question_index, answer_index = data_parts
    question_index = int(question_index)
    answer_index = int(answer_index)
    
    if question_index >= len(QUIZ_DATA):
        await callback.answer("Savol topilmadi")
        return
    
    question = QUIZ_DATA[question_index]
    
    if answer_index == question['correct_answer']:
        user_quiz_states[user_id]['score'] += 1
        await callback.answer("✅ To'g'ri!", show_alert=True)
    else:
        correct_answer = question['options'][question['correct_answer']]
        await callback.answer(f"❌ Noto'g'ri! To'g'ri javob: {correct_answer}", show_alert=True)
    
    user_quiz_states[user_id]['current_question'] += 1
    await send_question(user_id, callback.message.chat.id)

async def finish_quiz(user_id, chat_id):
    """Quizni tugatish"""
    state = user_quiz_states.get(user_id)
    if not state:
        return
    
    score = state['score']
    total = state['total_questions']
    percentage = (score / total) * 100 if total > 0 else 0
    
    # Statistika yangilash
    update_user_stats(user_id, score)
    
    if percentage >= 80:
        message = "🎉 Ajoyib natija! Siz musiqadan juda yaxshi tushunasiz!"
    elif percentage >= 60:
        message = "👍 Yaxshi natija! Yana bir bor urinib ko'ring."
    else:
        message = "💪 O'rganish uchun hamma vaqt joy bor. Qayta urinib ko'ring!"
    
    await bot.send_message(
        chat_id,
        f"📊 Quiz yakunlandi!\n\n"
        f"To'g'ri javoblar: {score}/{total}\n"
        f"Foiz: {percentage:.1f}%\n\n"
        f"{message}\n\n"
        f"Yana o'ynash uchun /quiz ni bosing"
    )
    
    # Quiz holatini tozalash
    if user_id in user_quiz_states:
        del user_quiz_states[user_id]

@dp.callback_query(F.data == "start_quiz")
async def start_quiz_callback(callback: CallbackQuery):
    """Quiz boshlash callback"""
    await callback.answer()
    user_id = callback.from_user.id
    
    if not is_user_allowed(user_id) and not is_admin(user_id):
        await callback.message.reply("❌ Sizga ruxsat berilmagan!")
        return
    
    if user_id in user_quiz_states:
        await callback.message.reply("Sizda davom etayotgan quiz bor! Avval uni tugating.")
        return
    
    user_quiz_states[user_id] = {
        'current_question': 0,
        'score': 0,
        'total_questions': len(QUIZ_DATA)
    }
    await send_question(user_id, callback.message.chat.id)

# ============= BOSHQA KOMANDALAR =============
@dp.message(Command("help"))
async def send_help(message: types.Message):
    """Yordam komandasi"""
    user_id = message.from_user.id
    
    if not is_user_allowed(user_id) and not is_admin(user_id):
        await message.reply("❌ Botdan foydalanish uchun ruxsat talab qilinadi!")
        return
    
    help_text = (
        "🤖 **Botdan foydalanish:**\n\n"
        "/start - Botni ishga tushirish\n"
        "/quiz - Yangi quiz boshlash\n"
        "/profile - Profil ma'lumotlari\n"
        "/help - Yordam olish\n\n"
        "📌 **Quiz qoidalari:**\n"
        "1. Har bir savol uchun audio eshitasiz\n"
        "2. 4 ta variantdan to'g'ri javobni tanlang\n"
        "3. Quiz oxirida natijangizni ko'rasiz"
    )
    
    if is_admin(user_id):
        help_text += "\n\n👨‍💼 **Admin komandalari:**\n/admin - Admin panel"
    
    await message.reply(help_text, parse_mode='Markdown')

@dp.message(Command("profile"))
@access_required
async def show_profile(message: types.Message):
    """Foydalanuvchi profilini ko'rsatish"""
    user_id = message.from_user.id
    user_id_str = str(user_id)
    
    if user_id_str in users_db:
        user_data = users_db[user_id_str]
        
        profile_text = (
            f"👤 **Sizning profilingiz**\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"👤 Ism: {user_data['first_name']}\n"
        )
        
        if user_data.get('last_name'):
            profile_text += f"👥 Familiya: {user_data['last_name']}\n"
        if user_data.get('username'):
            profile_text += f"📱 Username: @{user_data['username']}\n"
        
        profile_text += (
            f"\n📅 Ro'yxatdan o'tgan: {user_data['joined_date'][:10]}\n"
            f"✅ Ruxsat: {'Berilgan' if user_data['allowed'] else 'Berilmagan'}\n"
            f"\n🎮 **Statistika:**\n"
            f"📊 O'ynalgan quizlar: {user_data['quizzes_played']}\n"
            f"🏆 Umumiy ball: {user_data['total_score']}"
        )
        
        await message.reply(profile_text, parse_mode='Markdown')
    else:
        await message.reply("❌ Profil ma'lumotlari topilmadi!")

# Audio fayllarni qabul qilish
@dp.message(F.audio | F.voice)
@access_required
async def handle_audio(message: types.Message):
    """Audio fayllarni qabul qilish"""
    await message.reply(
        "🎵 Audio qabul qilindi!\n\n"
        "Bu funksiya keyingi yangilanishda qo'shiladi. "
        "Hozircha faqat demo quiz ishlaydi."
    )

# Boshqa xabarlarga javob
@dp.message()
async def echo_message(message: types.Message):
    """Boshqa xabarlar"""
    user_id = message.from_user.id
    
    if not is_user_allowed(user_id) and not is_admin(user_id):
        await message.reply(
            "❌ Botdan foydalanish uchun ruxsat talab qilinadi!\n\n"
            "Ruxsat so'rash uchun /start ni bosing."
        )
    else:
        await message.answer(
            "Quizni boshlash uchun /quiz ni bosing.\n"
            "Yordam olish uchun /help ni bosing."
        )

# ============= BOTNI ISHGA TUSHIRISH =============
async def on_startup():
    """Bot ishga tushganda"""
    logger.info("=" * 50)
    logger.info("Audio Quiz Bot ishga tushmoqda...")
    logger.info("=" * 50)
    
    # Ma'lumotlar bazasini yuklash
    load_users_db()
    
    # Adminlarni tekshirish
    logger.info(f"👨‍💼 Adminlar: {ADMIN_IDS}")
    
    # Webhook ni o'chirish
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook o'chirildi")
    except Exception as e:
        logger.error(f"❌ Webhook o'chirishda xatolik: {e}")
    
    # Bot ma'lumotlari
    bot_info = await bot.get_me()
    logger.info(f"✅ Bot username: @{bot_info.username}")
    logger.info(f"✅ Bot ismi: {bot_info.first_name}")
    logger.info(f"✅ Bot ID: {bot_info.id}")
    logger.info("=" * 50)



@dp.message(Command("create_test"))
@admin_required
async def cmd_create_test(message: Message, state: FSMContext):
    """Test yaratish menyusi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Yangi kitob yaratish", callback_data="create_new_book")],
            [InlineKeyboardButton(text="📖 Mavjud kitobni tanlash", callback_data="select_existing_book")],
            [InlineKeyboardButton(text="📋 Kitoblar ro'yxati", callback_data="list_books")],
            [InlineKeyboardButton(text="◀️ Admin panel", callback_data="back_to_admin")]
        ]
    )
    
    await message.reply(
        "📚 **TEST TUZISH TIZIMI**\n\n"
        "Tanlang:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# ============= KITOBLAR RO'YXATI =============
@dp.callback_query(F.data == "list_books")
@admin_callback_required
async def list_books_callback(callback: CallbackQuery):
    """Kitoblar ro'yxatini ko'rsatish"""
    if not books_db:
        text = "📚 **Kitoblar ro'yxati**\n\nHali kitoblar mavjud emas."
    else:
        text = "📚 **KITOBLAR RO'YXATI**\n\n"
        for book_id, book in list(books_db.items())[:10]:
            units_count = len(book.get('units', {}))
            tests_count = sum(len(unit.get('tests', {})) for unit in book.get('units', {}).values())
            
            text += f"📖 **{book['name']}**\n"
            text += f"🆔 `{book_id}`\n"
            text += f"📝 {book.get('description', 'Tavsifsiz')[:50]}\n"
            text += f"📚 Unitlar: {units_count} | ❓ Testlar: {tests_count}\n"
            text += f"📅 {book.get('created_at', '')[:10]}\n\n"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Yangi kitob", callback_data="create_new_book")],
            [InlineKeyboardButton(text="◀️ Ortga", callback_data="back_to_test_menu")]
        ]
    )
    
    await callback.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)

@dp.callback_query(F.data == "back_to_test_menu")
@admin_callback_required
async def back_to_test_menu_callback(callback: CallbackQuery, state: FSMContext):
    """Test menyusiga qaytish"""
    await state.clear()
    await cmd_create_test(callback.message, state)

# ============= YANGI KITOB YARATISH =============
@dp.callback_query(F.data == "create_new_book")
@admin_callback_required
async def create_new_book_callback(callback: CallbackQuery, state: FSMContext):
    """Yangi kitob yaratish"""
    await state.set_state(TestCreationStates.waiting_book_name)
    await callback.message.edit_text(
        "📚 **YANGI KITOB YARATISH**\n\n"
        "Kitob nomini kiriting:",
        parse_mode='Markdown'
    )

@dp.message(TestCreationStates.waiting_book_name)
@admin_required
async def process_book_name(message: Message, state: FSMContext):
    """Kitob nomini qabul qilish"""
    book_name = message.text.strip()
    
    if len(book_name) < 2 or len(book_name) > 100:
        await message.reply("❌ Kitob nomi 2-100 belgi orasida bo'lishi kerak. Qayta kiriting:")
        return
    
    await state.update_data(book_name=book_name)
    await state.set_state(TestCreationStates.waiting_book_description)
    
    await message.reply(
        f"📚 Kitob nomi: **{book_name}**\n\n"
        "📝 Kitob tavsifini kiriting (yoki /skip - o'tkazib yuborish):",
        parse_mode='Markdown'
    )

@dp.message(TestCreationStates.waiting_book_description)
@admin_required
async def process_book_description(message: Message, state: FSMContext):
    """Kitob tavsifini qabul qilish"""
    data = await state.get_data()
    book_name = data.get('book_name')
    
    if message.text == '/skip':
        book_description = ""
    else:
        book_description = message.text.strip()[:200]
    
    # Yangi kitob yaratish
    book_id = f"book_{uuid.uuid4().hex[:8]}"
    
    books_db[book_id] = {
        "id": book_id,
        "name": book_name,
        "description": book_description,
        "created_by": message.from_user.id,
        "created_at": datetime.now().isoformat(),
        "units": {}
    }
    
    save_books_db()
    
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📖 Unit yaratish", callback_data=f"create_unit_{book_id}")],
            [InlineKeyboardButton(text="📚 Kitoblar ro'yxati", callback_data="list_books")],
            [InlineKeyboardButton(text="◀️ Test menyusi", callback_data="back_to_test_menu")]
        ]
    )
    
    await message.reply(
        f"✅ **Kitob muvaffaqiyatli yaratildi!**\n\n"
        f"📖 Nomi: {book_name}\n"
        f"🆔 ID: `{book_id}`\n"
        f"📝 Tavsif: {book_description or 'Yoq'}\n\n"
        f"Endi unitlar qo'shishingiz mumkin.",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

# ============= MAVJUD KITOB TANLASH =============
@dp.callback_query(F.data == "select_existing_book")
@admin_callback_required
async def select_existing_book_callback(callback: CallbackQuery, state: FSMContext):
    """Mavjud kitobni tanlash"""
    if not books_db:
        await callback.message.edit_text(
            "❌ Hali kitoblar mavjud emas.\n\n"
            "Avval yangi kitob yarating!",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Yangi kitob", callback_data="create_new_book")],
                    [InlineKeyboardButton(text="◀️ Ortga", callback_data="back_to_test_menu")]
                ]
            )
        )
        return
    
    keyboard = []
    for book_id, book in list(books_db.items())[:10]:
        keyboard.append([
            InlineKeyboardButton(
                text=f"📖 {book['name']} ({len(book.get('units', {}))} unit)",
                callback_data=f"select_book_{book_id}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="◀️ Ortga", callback_data="back_to_test_menu")])
    
    await callback.message.edit_text(
        "📚 **KITOB TANLASH**\n\n"
        "Qaysi kitobga test qo'shmoqchisiz?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='Markdown'
    )

@dp.callback_query(F.data.startswith('select_book_'))
@admin_callback_required
async def select_book_callback(callback: CallbackQuery, state: FSMContext):
    """Kitob tanlanganda"""
    book_id = callback.data.replace('select_book_', '')
    
    if book_id not in books_db:
        await callback.answer("❌ Kitob topilmadi!", show_alert=True)
        return
    
    book = books_db[book_id]
    
    await state.update_data(selected_book_id=book_id, selected_book_name=book['name'])
    
    keyboard = [
        [InlineKeyboardButton(text="📖 Yangi unit yaratish", callback_data=f"create_unit_{book_id}")],
        [InlineKeyboardButton(text="📚 Mavjud unitni tanlash", callback_data=f"select_unit_{book_id}")],
        [InlineKeyboardButton(text="📋 Unitlar ro'yxati", callback_data=f"list_units_{book_id}")],
        [InlineKeyboardButton(text="◀️ Ortga", callback_data="select_existing_book")]
    ]
    
    await callback.message.edit_text(
        f"📚 **Kitob: {book['name']}**\n\n"
        f"🆔 ID: `{book_id}`\n"
        f"📝 {book.get('description', 'Tavsifsiz')[:100]}\n"
        f"📚 Unitlar soni: {len(book.get('units', {}))}\n\n"
        f"Tanlang:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
        parse_mode='Markdown'
    )

# ============= UNITLAR RO'YXATI =============
@dp.callback_query(F.data.startswith('list_units_'))
@admin_callback_required
async def list_units_callback(callback: CallbackQuery):
    """Unitlar ro'yxatini ko'rsatish"""
    book_id = callback.data.replace('list_units_', '')
    
    if book_id not in books_db:
        await callback.answer("❌ Kitob topilmadi!", show_alert=True)
        return
    
    book = books_db[book_id]
    units = book.get('units', {})
    
    if not units:
        text = f"📚 **{book['name']}**\n\nHali unitlar mavjud emas."
    else:
        text = f"📚 **{book['name']} - UNITLAR**\n\n"
        for unit_id, unit in list(units.items())[:10]:
            tests_count = len(unit.get('tests', {}))
            text += f"📖 **{unit['name']}**\n"
            text += f"🆔 `{unit_id}`\n"
            text += f"📝 {unit.get('description', 'Tavsifsiz')[:50]}\n"
            text += f"❓ Testlar: {tests_count}\n"
            text += f"📅 {unit.get('created_at', '')[:10]}\n\n"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Yangi unit", callback_data=f"create_unit_{book_id}")],
            [InlineKeyboardButton(text="◀️ Ortga", callback_data=f"select_book_{book_id}")]
        ]
    )
    
    await callback.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)

# ============= YANGI UNIT YARATISH =============
@dp.callback_query(F.data.startswith('create_unit_'))
@admin_callback_required
async def create_unit_callback(callback: CallbackQuery, state: FSMContext):
    """Yangi unit yaratish"""
    book_id = callback.data.replace('create_unit_', '')
    
    if book_id not in books_db:
        await callback.answer("❌ Kitob topilmadi!", show_alert=True)
        return
    
    await state.update_data(creating_unit_book_id=book_id)
    await state.set_state(TestCreationStates.waiting_unit_name)
    
    await callback.message.edit_text(
        f"📚 **Kitob: {books_db[book_id]['name']}**\n\n"
        "📖 Yangi unit nomini kiriting:",
        parse_mode='Markdown'
    )

@dp.message(TestCreationStates.waiting_unit_name)
@admin_required
async def process_unit_name(message: Message, state: FSMContext):
    """Unit nomini qabul qilish"""
    unit_name = message.text.strip()
    
    if len(unit_name) < 2 or len(unit_name) > 100:
        await message.reply("❌ Unit nomi 2-100 belgi orasida bo'lishi kerak. Qayta kiriting:")
        return
    
    await state.update_data(unit_name=unit_name)
    await state.set_state(TestCreationStates.waiting_unit_description)
    
    await message.reply(
        f"📖 Unit nomi: **{unit_name}**\n\n"
        "📝 Unit tavsifini kiriting (yoki /skip):",
        parse_mode='Markdown'
    )

@dp.message(TestCreationStates.waiting_unit_description)
@admin_required
async def process_unit_description(message: Message, state: FSMContext):
    """Unit tavsifini qabul qilish"""
    data = await state.get_data()
    book_id = data.get('creating_unit_book_id')
    unit_name = data.get('unit_name')
    
    if message.text == '/skip':
        unit_description = ""
    else:
        unit_description = message.text.strip()[:200]
    
    # Yangi unit yaratish
    unit_id = f"unit_{uuid.uuid4().hex[:8]}"
    
    if book_id in books_db:
        if 'units' not in books_db[book_id]:
            books_db[book_id]['units'] = {}
        
        books_db[book_id]['units'][unit_id] = {
            "id": unit_id,
            "name": unit_name,
            "description": unit_description,
            "created_at": datetime.now().isoformat(),
            "tests": {}
        }
        
        save_books_db()
        
        await state.clear()
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="❓ Test yaratish", callback_data=f"create_test_{book_id}_{unit_id}")],
                [InlineKeyboardButton(text="📖 Unitlar ro'yxati", callback_data=f"list_units_{book_id}")],
                [InlineKeyboardButton(text="◀️ Kitob menyusi", callback_data=f"select_book_{book_id}")]
            ]
        )
        
        await message.reply(
            f"✅ **Unit muvaffaqiyatli yaratildi!**\n\n"
            f"📚 Kitob: {books_db[book_id]['name']}\n"
            f"📖 Unit: {unit_name}\n"
            f"🆔 ID: `{unit_id}`\n"
            f"📝 Tavsif: {unit_description or 'Yoq'}\n\n"
            f"Endi testlar qo'shishingiz mumkin.",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    else:
        await state.clear()
        await message.reply("❌ Xatolik: Kitob topilmadi!")

# ============= MAVJUD UNIT TANLASH =============
@dp.callback_query(F.data.startswith('select_unit_'))
@admin_callback_required
async def select_unit_callback(callback: CallbackQuery, state: FSMContext):
    """Mavjud unitni tanlash"""
    parts = callback.data.split('_')
    if len(parts) == 3:
        book_id = parts[2]
        
        if book_id not in books_db:
            await callback.answer("❌ Kitob topilmadi!", show_alert=True)
            return
        
        book = books_db[book_id]
        units = book.get('units', {})
        
        if not units:
            await callback.message.edit_text(
                f"❌ Bu kitobda hali unitlar mavjud emas.\n\n"
                f"📚 **{book['name']}**",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text="➕ Yangi unit", callback_data=f"create_unit_{book_id}")],
                        [InlineKeyboardButton(text="◀️ Ortga", callback_data=f"select_book_{book_id}")]
                    ]
                )
            )
            return
        
        keyboard = []
        for unit_id, unit in list(units.items())[:10]:
            tests_count = len(unit.get('tests', {}))
            keyboard.append([
                InlineKeyboardButton(
                    text=f"📖 {unit['name']} ({tests_count} test)",
                    callback_data=f"select_unit_{book_id}_{unit_id}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton(text="◀️ Ortga", callback_data=f"select_book_{book_id}")])
        
        await callback.message.edit_text(
            f"📚 **Kitob: {book['name']}**\n\n"
            "📖 Unitni tanlang:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    elif len(parts) == 4:
        book_id = parts[2]
        unit_id = parts[3]
        
        if book_id not in books_db or unit_id not in books_db[book_id]['units']:
            await callback.answer("❌ Unit topilmadi!", show_alert=True)
            return
        
        book = books_db[book_id]
        unit = book['units'][unit_id]
        
        await state.update_data(
            selected_book_id=book_id,
            selected_book_name=book['name'],
            selected_unit_id=unit_id,
            selected_unit_name=unit['name']
        )
        
        tests_count = len(unit.get('tests', {}))
        
        keyboard = [
            [InlineKeyboardButton(text="❓ Yangi test yaratish", callback_data=f"create_test_{book_id}_{unit_id}")],
            [InlineKeyboardButton(text="📋 Testlar ro'yxati", callback_data=f"list_tests_{book_id}_{unit_id}")],
            [InlineKeyboardButton(text="◀️ Unitlar ro'yxati", callback_data=f"list_units_{book_id}")]
        ]
        
        await callback.message.edit_text(
            f"📚 **Kitob: {book['name']}**\n"
            f"📖 **Unit: {unit['name']}**\n\n"
            f"🆔 ID: `{unit_id}`\n"
            f"📝 {unit.get('description', 'Tavsifsiz')[:100]}\n"
            f"❓ Testlar soni: {tests_count}\n\n"
            f"Tanlang:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode='Markdown'
        )

# ============= TEST YARATISH =============
@dp.callback_query(F.data.startswith('create_test_'))
@admin_callback_required
async def create_test_callback(callback: CallbackQuery, state: FSMContext):
    """Yangi test yaratish"""
    parts = callback.data.split('_')
    book_id = parts[2]
    unit_id = parts[3]
    
    if book_id not in books_db or unit_id not in books_db[book_id]['units']:
        await callback.answer("❌ Kitob yoki unit topilmadi!", show_alert=True)
        return
    
    await state.update_data(
        test_book_id=book_id,
        test_unit_id=unit_id,
        test_book_name=books_db[book_id]['name'],
        test_unit_name=books_db[book_id]['units'][unit_id]['name']
    )
    
    await state.set_state(TestCreationStates.waiting_question_text)
    
    await callback.message.edit_text(
        f"📚 **Kitob: {books_db[book_id]['name']}**\n"
        f"📖 **Unit: {books_db[book_id]['units'][unit_id]['name']}**\n\n"
        f"❓ **YANGI TEST YARATISH**\n\n"
        f"Savol matnini kiriting:",
        parse_mode='Markdown'
    )

@dp.message(TestCreationStates.waiting_question_text)
@admin_required
async def process_question_text(message: Message, state: FSMContext):
    """Savol matnini qabul qilish"""
    question_text = message.text.strip()
    
    if len(question_text) < 5:
        await message.reply("❌ Savol juda qisqa. Kamida 5 belgi bo'lishi kerak. Qayta kiriting:")
        return
    
    await state.update_data(question_text=question_text)
    await state.set_state(TestCreationStates.waiting_question_audio)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭️ Audiosiz davom etish", callback_data="skip_audio")]
        ]
    )
    
    await message.reply(
        f"❓ **Savol:**\n{question_text}\n\n"
        f"🎵 Audio fayl yuboring yoki 'Audiosiz davom etish' tugmasini bosing:",
        reply_markup=keyboard,
        parse_mode='Markdown'
    )

@dp.callback_query(F.data == "skip_audio")
@admin_callback_required
async def skip_audio_callback(callback: CallbackQuery, state: FSMContext):
    """Audioni o'tkazib yuborish"""
    await state.update_data(audio_file=None)
    await state.set_state(TestCreationStates.waiting_options)
    
    await callback.message.edit_text(
        "📝 **Variantlarni kiriting**\n\n"
        "4 ta variantni har bir qatorga bittadan yozing:\n"
        "Masalan:\n"
        "Variant 1\n"
        "Variant 2\n"
        "Variant 3\n"
        "Variant 4",
        parse_mode='Markdown'
    )

@dp.message(F.audio | F.voice, TestCreationStates.waiting_question_audio)
@admin_required
async def process_question_audio(message: Message, state: FSMContext):
    """Audio faylni qabul qilish"""
    try:
        if message.audio:
            file_id = message.audio.file_id
            file_name = message.audio.file_name or f"audio_{uuid.uuid4().hex[:8]}.mp3"
        else:
            file_id = message.voice.file_id
            file_name = f"voice_{uuid.uuid4().hex[:8]}.ogg"
        
        await state.update_data(audio_file=file_id, audio_file_name=file_name)
        await state.set_state(TestCreationStates.waiting_options)
        
        await message.reply(
            "✅ Audio qabul qilindi!\n\n"
            "📝 **Variantlarni kiriting**\n\n"
            "4 ta variantni har bir qatorga bittadan yozing:",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"❌ Audio yuklashda xatolik: {e}")
        await message.reply("❌ Audio yuklashda xatolik. Qayta urinib ko'ring.")

@dp.message(TestCreationStates.waiting_options)
@admin_required
async def process_options(message: Message, state: FSMContext):
    """Variantlarni qabul qilish"""
    options_text = message.text.strip()
    options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
    
    if len(options) != 4:
        await message.reply(
            "❌ 4 ta variant kiriting!\n\n"
            "Masalan:\n"
            "Variant 1\n"
            "Variant 2\n"
            "Variant 3\n"
            "Variant 4"
        )
        return
    
    await state.update_data(options=options)
    await state.set_state(TestCreationStates.waiting_correct_answer)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"1️⃣ {options[0]}", callback_data="correct_0")],
            [InlineKeyboardButton(text=f"2️⃣ {options[1]}", callback_data="correct_1")],
            [InlineKeyboardButton(text=f"3️⃣ {options[2]}", callback_data="correct_2")],
            [InlineKeyboardButton(text=f"4️⃣ {options[3]}", callback_data="correct_3")]
        ]
    )
    
    await message.reply(
        "✅ Variantlar qabul qilindi!\n\n"
        "❓ **To'g'ri javobni tanlang:**",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith('correct_'), TestCreationStates.waiting_correct_answer)
@admin_callback_required
async def process_correct_answer(callback: CallbackQuery, state: FSMContext):
    """To'g'ri javobni qabul qilish"""
    correct_index = int(callback.data.split('_')[1])
    await state.update_data(correct_answer=correct_index)
    await state.set_state(TestCreationStates.waiting_explanation)
    
    await callback.message.edit_text(
        f"✅ To'g'ri javob tanlandi!\n\n"
        f"📝 Izoh kiriting (yoki /skip):",
        parse_mode='Markdown'
    )

@dp.message(TestCreationStates.waiting_explanation)
@admin_required
async def process_explanation(message: Message, state: FSMContext):
    """Izohni qabul qilish"""
    if message.text == '/skip':
        explanation = ""
    else:
        explanation = message.text.strip()[:500]
    
    data = await state.get_data()
    
    test_id = f"test_{uuid.uuid4().hex[:8]}"
    book_id = data.get('test_book_id')
    unit_id = data.get('test_unit_id')
    
    if book_id in books_db and unit_id in books_db[book_id]['units']:
        books_db[book_id]['units'][unit_id]['tests'][test_id] = {
            "id": test_id,
            "question": data.get('question_text'),
            "audio_file": data.get('audio_file'),
            "audio_file_name": data.get('audio_file_name'),
            "options": data.get('options'),
            "correct_answer": data.get('correct_answer'),
            "explanation": explanation,
            "created_by": message.from_user.id,
            "created_at": datetime.now().isoformat()
        }
        
        save_books_db()
        await state.clear()
        
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="➕ Yana test qo'shish", callback_data=f"create_test_{book_id}_{unit_id}")],
                [InlineKeyboardButton(text="📋 Testlar ro'yxati", callback_data=f"list_tests_{book_id}_{unit_id}")],
                [InlineKeyboardButton(text="◀️ Unit menyusi", callback_data=f"select_unit_{book_id}_{unit_id}")]
            ]
        )
        
        await message.reply(
            f"✅ **Test muvaffaqiyatli yaratildi!**\n\n"
            f"📚 Kitob: {books_db[book_id]['name']}\n"
            f"📖 Unit: {books_db[book_id]['units'][unit_id]['name']}\n"
            f"🆔 Test ID: `{test_id}`\n\n"
            f"❓ Savol: {data.get('question_text')[:100]}...\n"
            f"🎵 Audio: {'Bor' if data.get('audio_file') else 'Yoq'}\n\n"
            f"Endi yana test qo'shishingiz mumkin.",
            reply_markup=keyboard,
            parse_mode='Markdown'
        )
    else:
        await state.clear()
        await message.reply("❌ Xatolik: Kitob yoki unit topilmadi!")

# ============= TESTLAR RO'YXATI =============
@dp.callback_query(F.data.startswith('list_tests_'))
@admin_callback_required
async def list_tests_callback(callback: CallbackQuery):
    """Testlar ro'yxatini ko'rsatish"""
    parts = callback.data.split('_')
    book_id = parts[2]
    unit_id = parts[3]
    
    if book_id not in books_db or unit_id not in books_db[book_id]['units']:
        await callback.answer("❌ Kitob yoki unit topilmadi!", show_alert=True)
        return
    
    book = books_db[book_id]
    unit = book['units'][unit_id]
    tests = unit.get('tests', {})
    
    if not tests:
        text = f"📚 **{book['name']}** / 📖 **{unit['name']}**\n\nHali testlar mavjud emas."
    else:
        text = f"📚 **{book['name']}** / 📖 **{unit['name']}**\n"
        text += f"📋 **TESTLAR RO'YXATI** ({len(tests)} ta)\n\n"
        
        for test_id, test in list(tests.items())[:10]:
            correct_answer = test['options'][test['correct_answer']]
            text += f"❓ **{test['question'][:50]}...**\n"
            text += f"🆔 `{test_id}`\n"
            text += f"✅ {correct_answer}\n"
            text += f"🎵 {'🔊' if test.get('audio_file') else '🔇'}\n"
            text += f"📅 {test.get('created_at', '')[:10]}\n\n"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Yangi test", callback_data=f"create_test_{book_id}_{unit_id}")],
            [InlineKeyboardButton(text="◀️ Unit menyusi", callback_data=f"select_unit_{book_id}_{unit_id}")]
        ]
    )
    
    await callback.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)

# ============= TEST TIZIMINI ISHGA TUSHIRISH =============
def init_test_system():
    """Test tizimini ishga tushirish"""
    global books_db
    load_books_db()
    logger.info("📚 Test tuzish tizimi yuklandi")
    logger.info(f"📊 Jami kitoblar: {len(books_db)} ta")

async def main():
    await on_startup()
    await dp.start_polling(bot, skip_updates=True)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot to'xtatildi")
    except Exception as e:
        logger.error(f"❌ Kutilmagan xatolik: {e}")