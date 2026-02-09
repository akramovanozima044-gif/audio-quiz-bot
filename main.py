import os
import logging
from typing import Optional
from datetime import datetime

from aiogram import Bot, Dispatcher, types, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.enums import ParseMode

from dotenv import load_dotenv
import database as db

# Logging sozlamalari
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Bot va dispatcher yaratish
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# FSM holatlari
class AdminStates(StatesGroup):
    waiting_for_broadcast = State()
    waiting_for_book_name = State()

# ========== A-QADAM: Asosiy funksiyalar ==========

async def check_access(message: Message) -> bool:
    """Foydalanuvchiga ruxsat borligini tekshirish"""
    user_id = message.from_user.id
    
    # Agar admin bo'lsa, har doim ruxsat berilgan
    if user_id == ADMIN_ID:
        db.add_user_if_not_exists(
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            is_admin=True
        )
        return True
    
    # Oddiy foydalanuvchi uchun tekshirish
    if db.is_user_allowed(user_id):
        return True
    
    # Agar ruxsat yo'q bo'lsa
    await message.answer(
        "❌ Sizga botdan foydalanishga ruxsat berilmagan.\n\n"
        "Foydalanish uchun admin bilan bog'laning yoki /request_access "
        "buyrug'i orqali ruxsat so'rang."
    )
    
    # Admin ga bildirishnoma yuborish
    admin_msg = (
        f"⚠️ Yangi ruxsat so'rovi:\n"
        f"👤 Foydalanuvchi: {message.from_user.first_name}\n"
        f"📛 Username: @{message.from_user.username}\n"
        f"🆔 ID: {user_id}\n\n"
        f"📩 Ruxsat so'rovi yuborish uchun /admin buyrug'idan foydalaning"
    )
    
    try:
        await bot.send_message(ADMIN_ID, admin_msg)
    except Exception as e:
        logger.error(f"Admin ga xabar yuborishda xatolik: {e}")
    
    return False

@router.message(Command("start"))
async def start_command(message: Message):
    """Start komandasi"""
    user_id = message.from_user.id
    
    # Adminni avtomatik ro'yxatdan o'tkazish
    if user_id == ADMIN_ID:
        db.add_user_if_not_exists(
            user_id=user_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            is_admin=True
        )
        
        # Admin menyusini ko'rsatish
        await show_admin_menu(message)
        return
    
    # Oddiy foydalanuvchi uchun tekshirish
    if not await check_access(message):
        return
    
    # Agar ruxsat berilgan bo'lsa, user menyusini ko'rsatish
    await show_user_menu(message)

async def show_user_menu(message: Message):
    """User menyusini ko'rsatish"""
    keyboard = ReplyKeyboardBuilder()
    keyboard.button(text="📝 Test yechish")
    keyboard.button(text="📊 Umumiy natijalar")
    keyboard.adjust(2)
    
    await message.answer(
        "👋 User menyusiga xush kelibsiz!\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=keyboard.as_markup(resize_keyboard=True)
    )

async def show_admin_menu(message: Message):
    """Admin menyusini ko'rsatish (B-qadam)"""
    keyboard = InlineKeyboardBuilder()
    
    keyboard.button(text="📝 Test tuzish", callback_data="admin_create_test")
    keyboard.button(text="🧪 Test yechish", callback_data="admin_solve_test")
    keyboard.button(text="🗑️ Testni o'chirish", callback_data="admin_delete_test")
    keyboard.button(text="👥 Foydalanuvchilar", callback_data="admin_users")
    keyboard.button(text="📢 Habar yuborish", callback_data="admin_broadcast")
    keyboard.button(text="📊 Umumiy natijalar", callback_data="admin_stats")
    
    keyboard.adjust(2)
    
    await message.answer(
        "🛠️ **Admin menyusi**\n\n"
        "Quyidagi funksiyalardan birini tanlang:",
        reply_markup=keyboard.as_markup(),
        parse_mode=ParseMode.MARKDOWN
    )

# ========== B-QADAM: Admin funksiyalari ==========

@router.callback_query(lambda c: c.data.startswith("admin_"))
async def admin_menu_handler(callback: CallbackQuery):
    """Admin menyusi tugmalarini boshqarish"""
    user_id = callback.from_user.id
    
    # Faqat admin uchun
    if user_id != ADMIN_ID:
        await callback.answer("Siz admin emassiz!", show_alert=True)
        return
    
    action = callback.data
    
    if action == "admin_create_test":
        await callback.message.answer("📝 Test tuzish bo'limiga o'tdingiz...")
        # Bu yerda keyinchalik test tuzish logikasi qo'shiladi
        await callback.message.answer("⚠️ Bu funksiya hali ishga tushirilmagan")
        
    elif action == "admin_solve_test":
        await callback.message.answer("🧪 Test yechish bo'limiga o'tdingiz...")
        # Bu yerda test yechish logikasi qo'shiladi
        
    elif action == "admin_delete_test":
        await callback.message.answer("🗑️ Testni o'chirish bo'limiga o'tdingiz...")
        # Bu yerda test o'chirish logikasi qo'shiladi
        
    elif action == "admin_users":
        await show_users_list(callback.message)
        
    elif action == "admin_broadcast":
        await broadcast_message_start(callback.message)
        
    elif action == "admin_stats":
        await callback.message.answer("📊 Umumiy natijalar bo'limiga o'tdingiz...")
        # Bu yerda statistikalar logikasi qo'shiladi
    
    await callback.answer()

async def show_users_list(message: Message):
    """Foydalanuvchilar ro'yxatini ko'rsatish"""
    users = db.get_all_users()
    pending_requests = db.get_pending_requests()
    
    if not users and not pending_requests:
        await message.answer("📭 Hozircha foydalanuvchilar yo'q")
        return
    
    text = "👥 **Foydalanuvchilar ro'yxati**\n\n"
    
    if pending_requests:
        text += "⏳ **Kutilayotgan so'rovlar:**\n"
        for req in pending_requests:
            text += (
                f"├─ 👤 {req['first_name']} (@{req['username']})\n"
                f"├─ 🆔 ID: {req['user_id']}\n"
                f"└─ 📅 {req['request_date']}\n\n"
            )
    
    text += "✅ **Ruxsat berilgan foydalanuvchilar:**\n"
    for user in users:
        status = "🟢" if user['is_allowed'] else "🔴"
        text += (
            f"{status} {user['first_name']} (@{user['username']})\n"
            f"  └─ 🆔 ID: {user['user_id']}\n"
            f"  └─ 📅 {user['join_date']}\n\n"
        )
    
    # Foydalanuvchilarni boshqarish tugmalari
    keyboard = InlineKeyboardBuilder()
    
    if pending_requests:
        keyboard.button(text="📩 So'rovlarni ko'rish", callback_data="view_requests")
    
    keyboard.button(text="👤 Foydalanuvchini o'chirish", callback_data="remove_user")
    keyboard.button(text="⬅️ Orqaga", callback_data="back_to_admin")
    
    keyboard.adjust(1)
    
    await message.answer(text, reply_markup=keyboard.as_markup(), parse_mode=ParseMode.MARKDOWN)

@router.callback_query(lambda c: c.data == "view_requests")
async def view_pending_requests(callback: CallbackQuery):
    """Kutilayotgan ruxsat so'rovlarini ko'rsatish"""
    requests = db.get_pending_requests()
    
    if not requests:
        await callback.answer("Kutilayotgan so'rovlar yo'q", show_alert=True)
        return
    
    for req in requests:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="✅ Ruxsat berish", callback_data=f"approve_{req['id']}")
        keyboard.button(text="❌ Rad etish", callback_data=f"reject_{req['id']}")
        
        text = (
            f"📨 **Ruxsat so'rovi**\n\n"
            f"👤 Foydalanuvchi: {req['first_name']}\n"
            f"📛 Username: @{req['username']}\n"
            f"🆔 ID: `{req['user_id']}`\n"
            f"📅 So'rov vaqti: {req['request_date']}"
        )
        
        await callback.message.answer(
            text,
            reply_markup=keyboard.as_markup(),
            parse_mode=ParseMode.MARKDOWN
        )
    
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith(("approve_", "reject_")))
async def handle_access_request(callback: CallbackQuery):
    """Ruxsat so'rovini qayta ishlash"""
    user_id = callback.from_user.id
    
    if user_id != ADMIN_ID:
        await callback.answer("Siz admin emassiz!", show_alert=True)
        return
    
    action, request_id = callback.data.split("_")
    request_id = int(request_id)
    
    if action == "approve":
        db.update_access_request(request_id, "approved", user_id)
        status_text = "✅ Ruxsat berildi"
        
        # Foydalanuvchiga xabar yuborish
        try:
            # Bu yerda request_id orqali user_id ni topishimiz kerak
            # Soddalik uchun hozircha xabar yubormaymiz
            pass
        except Exception as e:
            logger.error(f"User ga xabar yuborishda xatolik: {e}")
            
    else:  # reject
        db.update_access_request(request_id, "rejected", user_id)
        status_text = "❌ Rad etildi"
    
    await callback.message.edit_text(
        f"{callback.message.text}\n\n"
        f"**{status_text}** ✅",
        parse_mode=ParseMode.MARKDOWN
    )
    await callback.answer(status_text)

@router.callback_query(lambda c: c.data == "remove_user")
async def remove_user_start(callback: CallbackQuery):
    """Foydalanuvchini o'chirish boshlanishi"""
    users = db.get_all_users()
    
    if not users:
        await callback.answer("Foydalanuvchilar yo'q", show_alert=True)
        return
    
    keyboard = InlineKeyboardBuilder()
    
    for user in users:
        if user['user_id'] != ADMIN_ID:  # Adminni o'zini o'chirish mumkin emas
            keyboard.button(
                text=f"❌ {user['first_name']} (@{user['username']})",
                callback_data=f"remove_{user['user_id']}"
            )
    
    keyboard.button(text="⬅️ Orqaga", callback_data="back_to_users")
    keyboard.adjust(1)
    
    await callback.message.answer(
        "👤 O'chirish uchun foydalanuvchini tanlang:",
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("remove_"))
async def confirm_remove_user(callback: CallbackQuery):
    """Foydalanuvchini o'chirishni tasdiqlash"""
    user_id_to_remove = int(callback.data.split("_")[1])
    
    if user_id_to_remove == ADMIN_ID:
        await callback.answer("Adminni o'chirish mumkin emas!", show_alert=True)
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="✅ Ha, o'chirish", callback_data=f"confirm_remove_{user_id_to_remove}")
    keyboard.button(text="❌ Bekor qilish", callback_data="cancel_remove")
    
    await callback.message.answer(
        "⚠️ Rostdan ham bu foydalanuvchini o'chirmoqchimisiz?\n"
        "Bu amalni qaytarib bo'lmaydi!",
        reply_markup=keyboard.as_markup()
    )
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("confirm_remove_"))
async def execute_remove_user(callback: CallbackQuery):
    """Foydalanuvchini o'chirish"""
    user_id_to_remove = int(callback.data.split("_")[2])
    
    if user_id_to_remove == ADMIN_ID:
        await callback.answer("Adminni o'chirish mumkin emas!", show_alert=True)
        return
    
    db.remove_user(user_id_to_remove)
    
    await callback.message.answer("✅ Foydalanuvchi muvaffaqiyatli o'chirildi!")
    await callback.answer()

@router.callback_query(lambda c: c.data == "cancel_remove")
async def cancel_remove_user(callback: CallbackQuery):
    """Foydalanuvchini o'chirishni bekor qilish"""
    await callback.message.delete()
    await callback.answer("❌ O'chirish bekor qilindi")

async def broadcast_message_start(message: Message):
    """Barcha foydalanuvchilarga xabar yuborishni boshlash"""
    await message.answer(
        "📢 **Hammaga xabar yuborish**\n\n"
        "Istalgan matn, rasm, audio yoki video yuboring.\n"
        "Yuborgan postingiz barcha ruxsatli foydalanuvchilarga jo'natiladi.\n\n"
        "❌ Bekor qilish uchun /cancel yozing."
    )

@router.message(F.text == "/cancel")
async def cancel_broadcast(message: Message):
    """Habar yuborishni bekor qilish"""
    await message.answer("✅ Xabar yuborish bekor qilindi")
    await show_admin_menu(message)

# ========== Foydalanuvchi funksiyalari ==========

@router.message(Command("request_access"))
async def request_access_command(message: Message):
    """Foydalanuvchi ruxsat so'rashi"""
    user_id = message.from_user.id
    
    # Agar allaqachon ruxsat berilgan bo'lsa
    if db.is_user_allowed(user_id):
        await message.answer("✅ Sizga allaqachon ruxsat berilgan!")
        return
    
    # Agar allaqachon so'rov yuborilgan bo'lsa
    # (Soddalik uchun bu qismni keyinroq to'ldiramiz)
    
    # Ruxsat so'rovini qo'shish
    db.add_access_request(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    # Admin ga xabar yuborish
    admin_msg = (
        f"📨 **Yangi ruxsat so'rovi**\n\n"
        f"👤 Foydalanuvchi: {message.from_user.first_name}\n"
        f"📛 Username: @{message.from_user.username}\n"
        f"🆔 ID: `{user_id}`\n\n"
        f"✅ Ruxsat berish uchun /admin buyrug'idan foydalaning"
    )
    
    try:
        await bot.send_message(ADMIN_ID, admin_msg, parse_mode=ParseMode.MARKDOWN)
        await message.answer(
            "✅ Ruxsat so'rovingiz admin ga yuborildi.\n"
            "Javobni kuting. Rahmat!"
        )
    except Exception as e:
        logger.error(f"Admin ga xabar yuborishda xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi. Iltimos, keyinroq urunib ko'ring.")

# ========== Start va asosiy funksiya ==========

async def on_startup():
    """Bot ishga tushganda"""
    logger.info("Bot ishga tushmoqda...")
    
    # Database ni ishga tushirish
    db.init_db()
    
    # Adminni ro'yxatdan o'tkazish
    try:
        await bot.send_message(ADMIN_ID, "✅ Bot ishga tushdi!")
    except Exception as e:
        logger.error(f"Admin ga xabar yuborishda xatolik: {e}")

async def main():
    """Asosiy funksiya"""
    await on_startup()
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())