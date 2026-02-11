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

# ============= TEST TIZIMINI ISHGA TUSHIRISH =============
init_test_system()

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