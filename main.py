import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F  # F ni import qo'shdik
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
import os

# Import qilish
from database import init_db, async_session, User
from sqlalchemy import select
from middlewares import AdminMiddleware, UserMiddleware
from keyboards import get_admin_main_menu, get_user_main_menu, get_approve_keyboard
from handlers.common import router as common_router
from handlers.admin import router as admin_router
from handlers.user import router as user_router
from utils import ensure_audio_dir
from handlers.test import router as test_router

# Logging sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Konfiguratsiyani yuklash
load_dotenv()

# Railway da DATABASE_URL avtomatik beriladi
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///database.db"  # fallback

# Audio fayllar uchun
AUDIO_PATH = os.getenv('AUDIO_PATH', 'data/audio')
if not os.path.exists(AUDIO_PATH):
    os.makedirs(AUDIO_PATH, exist_ok=True)

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

async def main():
    # Botni yaratish
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Middleware'lar
    dp.message.outer_middleware(AdminMiddleware())
    dp.message.outer_middleware(UserMiddleware())
    dp.callback_query.outer_middleware(AdminMiddleware())
    dp.callback_query.outer_middleware(UserMiddleware())
    
    # Database'ni ishga tushirish
    await init_db()
    ensure_audio_dir()  # Audio papkasini yaratish
    logger.info("Database initialized successfully")
    
    # Router'larni qo'shish
    dp.include_router(common_router)
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(test_router) 
    
    # Start komandasi
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message):
        try:
            logger.info(f"Start command from user_id: {message.from_user.id}")
            
            async with async_session() as session:
                result = await session.execute(
                    select(User).where(User.user_id == message.from_user.id)
                )
                existing_user = result.scalar_one_or_none()
                
                if not existing_user:
                    # Yangi foydalanuvchi
                    new_user = User(
                        user_id=message.from_user.id,
                        username=message.from_user.username,
                        first_name=message.from_user.first_name,
                        last_name=message.from_user.last_name,
                        is_active=False,
                        is_admin=(message.from_user.id == ADMIN_ID)
                    )
                    session.add(new_user)
                    await session.commit()
                    
                    existing_user = new_user
                    logger.info(f"New user created: {message.from_user.id}")
                
                if existing_user.is_admin:
                    await message.answer(
                        "👋 Salom Admin! Bot muvaffaqiyatli ishga tushdi.\n\n"
                        "Admin menyusi:",
                        reply_markup=get_admin_main_menu()
                    )
                    logger.info(f"Admin logged in: {message.from_user.id}")
                    
                elif existing_user.is_active:
                    await message.answer(
                        "👋 Salom! Audio Quiz botiga xush kelibsiz!\n\n"
                        "Foydalanuvchi menyusi:",
                        reply_markup=get_user_main_menu()
                    )
                    logger.info(f"Active user logged in: {message.from_user.id}")
                    
                else:
                    await message.answer(
                        "❌ Sizda hali ruxsat yo'q. Iltimos, admin bilan bog'laning.\n\n"
                        "So'rovingiz adminlarga yuborildi."
                    )
                    logger.info(f"New user awaiting approval: {message.from_user.id}")
                    
                    # Adminlarga bildirishnoma yuborish
                    admin_notification = (
                        f"🆕 Yangi foydalanuvchi:\n"
                        f"👤 Ism: {message.from_user.full_name}\n"
                        f"🆔 ID: {message.from_user.id}\n"
                        f"📛 Username: @{message.from_user.username}\n\n"
                        f"Ruxsat berasizmi?"
                    )
                    await bot.send_message(
                        ADMIN_ID,
                        admin_notification,
                        reply_markup=get_approve_keyboard(message.from_user.id)
                    )
                    
        except Exception as e:
            logger.error(f"Start command error: {e}")
            await message.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")
    
    # Callback handler for user approval
    @dp.callback_query(F.data.startswith("approve_user_"))
    async def approve_user_callback(callback: types.CallbackQuery):
        try:
            user_id = int(callback.data.split("_")[2])
            
            async with async_session() as session:
                result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    user.is_active = True
                    await session.commit()
                    
                    await callback.message.edit_text(
                        f"✅ Foydalanuvchi tasdiqlandi:\n"
                        f"👤 {user.first_name} {user.last_name}\n"
                        f"🆔 {user.user_id}"
                    )
                    
                    # Foydalanuvchiga xabar yuborish
                    await bot.send_message(
                        user_id,
                        "🎉 Tabriklaymiz! Sizga ruxsat berildi!\n\n"
                        "Endi botdan to'liq foydalanishingiz mumkin.\n"
                        "/start ni bosing.",
                        reply_markup=get_user_main_menu()
                    )
                    
        except Exception as e:
            logger.error(f"Approve user error: {e}")
            await callback.answer("Xatolik yuz berdi")
    
    @dp.callback_query(F.data.startswith("reject_user_"))
    async def reject_user_callback(callback: types.CallbackQuery):
        try:
            user_id = int(callback.data.split("_")[2])
            
            async with async_session() as session:
                result = await session.execute(
                    select(User).where(User.user_id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if user:
                    await session.delete(user)
                    await session.commit()
                    
                    await callback.message.edit_text(
                        f"❌ Foydalanuvchi rad etildi:\n"
                        f"👤 {user.first_name} {user.last_name}\n"
                        f"🆔 {user.user_id}"
                    )
                    
                    # Foydalanuvchiga xabar yuborish
                    await bot.send_message(
                        user_id,
                        "❌ Kechirasiz, sizga ruxsat berilmadi.\n"
                        "Agar bu xato deb o'ylasangiz, admin bilan bog'laning."
                    )
                    
        except Exception as e:
            logger.error(f"Reject user error: {e}")
            await callback.answer("Xatolik yuz berdi")
    
    logger.info("Bot starting...")
    # Botni ishga tushirish
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())