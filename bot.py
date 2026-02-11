import os
import logging
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.orm import Session

import config
import database
from keyboards import (
    admin_main_menu, user_main_menu, request_access_keyboard,
    user_approval_keyboard, test_creation_menu, back_to_admin_menu_keyboard,
    books_list_keyboard, units_list_keyboard, start_test_keyboard
)

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Bot va dispatcher yaratish
bot = Bot(token=config.BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Database initialization
database.init_db()

# ---------- STATES ----------
class AdminStates(StatesGroup):
    waiting_for_book_name = State()
    waiting_for_unit_name = State()
    waiting_for_question_audio = State()
    waiting_for_question_options = State()
    waiting_for_correct_answer = State()
    waiting_for_broadcast_message = State()

# ---------- HELPERS ----------
async def check_admin_access(user_id: int, db: Session) -> bool:
    """Foydalanuvchi admin yoki ruxsat berilganmi tekshirish"""
    if user_id == config.ADMIN_ID:
        return True
    
    user = db.query(database.User).filter(database.User.user_id == user_id).first()
    return user and user.is_active

async def check_group(message: Message):
    """Guruhda ishlatilishini bloklash"""
    if message.chat.type != "private":
        await message.answer("❌ Bu bot faqat shaxsiy suhbatlarda ishlatilishi mumkin!")
        return False
    return True

# ---------- A QADAM: START VA RUHSAT TEKSHIRISH ----------
@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Start komandasi"""
    # Guruhni tekshirish
    if not await check_group(message):
        return
    
    user_id = message.from_user.id
    db = next(database.get_db())
    
    # Admin IDsini tekshirish
    if user_id == config.ADMIN_ID:
        # Admin hisobini yaratish/yangilash
        admin_user = db.query(database.User).filter(database.User.user_id == user_id).first()
        if not admin_user:
            admin_user = database.User(
                user_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                is_admin=True,
                is_active=True
            )
            db.add(admin_user)
            db.commit()
        elif not admin_user.is_admin:
            admin_user.is_admin = True
            admin_user.is_active = True
            db.commit()
        
        await message.answer(
            "👑 Admin menyusiga xush kelibsiz!\n"
            "Kerakli bo'limni tanlang:",
            reply_markup=admin_main_menu()
        )
        await state.clear()
        return
    
    # Oddiy foydalanuvchilar uchun
    is_allowed = await check_admin_access(user_id, db)
    
    if is_allowed:
        await message.answer(
            "🎉 Botga xush kelibsiz!\n"
            "Test ishlashni boshlashingiz mumkin:",
            reply_markup=user_main_menu()
        )
        await state.clear()
    else:
        # Yangi foydalanuvchi qo'shish yoki mavjudini yangilash
        user = db.query(database.User).filter(database.User.user_id == user_id).first()
        
        if not user:
            user = database.User(
                user_id=user_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
                is_active=False,
                requested_access=False
            )
            db.add(user)
            db.commit()
        
        if user.requested_access:
            await message.answer(
                "⏳ Sizning so'rovingiz admin tomonidan ko'rib chiqilmoqda.\n"
                "Iltimos, javobni kuting..."
            )
        else:
            await message.answer(
                "👋 Assalomu alaykum! Bu bot faqat admin ruxsati bilan ishlatiladi.\n"
                "Test ishlash uchun ruxsat so'rang:",
                reply_markup=request_access_keyboard(user_id)
            )

# ---------- B QADAM: ADMIN MENYU HANDLERS ----------

# Test tuzish
@dp.message(F.text == "📝 Test tuzish")
async def handle_create_test(message: Message, state: FSMContext):
    """Test tuzish menyusi"""
    user_id = message.from_user.id
    db = next(database.get_db())
    
    if not await check_admin_access(user_id, db):
        await message.answer("❌ Sizda bu amalni bajarish uchun ruxsat yo'q!")
        return
    
    await message.answer("Test tuzish bo'limi. Tanlang:", reply_markup=test_creation_menu())

# Foydalanuvchilar ro'yxati
@dp.message(F.text == "👥 Foydalanuvchilar ro'yxati")
async def handle_users_list(message: Message):
    """Foydalanuvchilar ro'yxati"""
    user_id = message.from_user.id
    db = next(database.get_db())
    
    if not await check_admin_access(user_id, db):
        await message.answer("❌ Sizda bu amalni bajarish uchun ruxsat yo'q!")
        return
    
    # Barcha foydalanuvchilarni olish
    users = db.query(database.User).order_by(database.User.created_at.desc()).all()
    
    if not users:
        await message.answer("📭 Hozircha foydalanuvchilar ro'yxati bo'sh")
        return
    
    response = "📋 Foydalanuvchilar ro'yxati:\n\n"
    for i, user in enumerate(users, 1):
        status = "👑 Admin" if user.is_admin else "✅ Faol" if user.is_active else "⏳ Kutilmoqda" if user.requested_access else "❌ Faol emas"
        response += f"{i}. 👤 {user.first_name}"
        if user.username:
            response += f" (@{user.username})"
        response += f"\n   🆔 ID: {user.user_id}\n"
        response += f"   📅 {user.created_at.strftime('%Y-%m-%d')}\n"
        response += f"   🔧 {status}\n\n"
    
    # Xabarni qismlarga bo'lish (Telegram chegarasi uchun)
    max_length = 4000
    if len(response) > max_length:
        parts = [response[i:i+max_length] for i in range(0, len(response), max_length)]
        for part in parts:
            await message.answer(part)
    else:
        await message.answer(response)
    
    # Ruxsat so'raganlar uchun alohida xabar
    pending_users = db.query(database.User).filter(
        database.User.requested_access == True,
        database.User.is_active == False
    ).all()
    
    if pending_users:
        await message.answer("⏳ Ruxsat so'ragan foydalanuvchilar:")
        for user in pending_users:
            await message.answer(
                f"👤 {user.first_name} (@{user.username})\n"
                f"🆔 ID: {user.user_id}",
                reply_markup=user_approval_keyboard(user.user_id)
            )

# Habar yuborish
@dp.message(F.text == "📢 Habar yuborish")
async def handle_broadcast(message: Message, state: FSMContext):
    """Habar yuborish menyusi"""
    user_id = message.from_user.id
    
    if user_id != config.ADMIN_ID:
        await message.answer("❌ Faqat asosiy admin uchun!")
        return
    
    await message.answer(
        "📢 Barcha faol foydalanuvchilarga yubormoqchi bo'lgan habaringizni yuboring:\n"
        "(Matn, rasm, audio yoki video)\n\n"
        "❌ Bekor qilish: /cancel"
    )
    await state.set_state(AdminStates.waiting_for_broadcast_message)

@dp.message(AdminStates.waiting_for_broadcast_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Habar yuborishni amalga oshirish"""
    if message.text and message.text == "/cancel":
        await message.answer("✅ Habar yuborish bekor qilindi.", reply_markup=admin_main_menu())
        await state.clear()
        return
    
    db = next(database.get_db())
    active_users = db.query(database.User).filter(database.User.is_active == True).all()
    
    sent_count = 0
    failed_count = 0
    
    await message.answer(f"📤 Habar {len(active_users)} ta foydalanuvchiga yuborilmoqda...")
    
    for user in active_users:
        try:
            # Xabarni nusxalash
            if message.text:
                await bot.send_message(user.user_id, message.text)
            elif message.photo:
                await bot.send_photo(user.user_id, message.photo[-1].file_id, caption=message.caption)
            elif message.audio:
                await bot.send_audio(user.user_id, message.audio.file_id, caption=message.caption)
            elif message.video:
                await bot.send_video(user.user_id, message.video.file_id, caption=message.caption)
            elif message.document:
                await bot.send_document(user.user_id, message.document.file_id, caption=message.caption)
            
            sent_count += 1
        except Exception as e:
            logger.error(f"Foydalanuvchiga {user.user_id} habar yuborishda xatolik: {e}")
            failed_count += 1
    
    await message.answer(
        f"✅ Habar yuborish yakunlandi!\n\n"
        f"✅ Muvaffaqiyatli: {sent_count}\n"
        f"❌ Muvaffaqiyatsiz: {failed_count}",
        reply_markup=admin_main_menu()
    )
    await state.clear()

# Orqaga qaytish
@dp.message(F.text == "🔙 Orqaga")
async def handle_back(message: Message, state: FSMContext):
    """Orqaga qaytish"""
    await cmd_start(message, state)

# ---------- CALLBACK QUERY HANDLERS ----------

# Ruxsat so'rash
@dp.callback_query(F.data.startswith("request_access_"))
async def handle_request_access(callback: CallbackQuery):
    """Foydalanuvchi ruxsat so'rashi"""
    try:
        user_id = int(callback.data.split("_")[2])
    except:
        await callback.answer("❌ Xatolik yuz berdi!")
        return
    
    db = next(database.get_db())
    
    # Foydalanuvchini yangilash
    user = db.query(database.User).filter(database.User.user_id == user_id).first()
    if user:
        user.requested_access = True
        db.commit()
        
        # AdminRequest qo'shish
        request = database.AdminRequest(
            user_id=user_id,
            username=user.username,
            status="pending"
        )
        db.add(request)
        db.commit()
        
        # Adminlarga xabar yuborish
        admin_users = db.query(database.User).filter(database.User.is_admin == True).all()
        
        for admin in admin_users:
            try:
                await bot.send_message(
                    admin.user_id,
                    f"🆕 Yangi ruxsat so'rovi!\n\n"
                    f"👤 Foydalanuvchi: {user.first_name}\n"
                    f"📛 Username: @{user.username}\n"
                    f"🆔 ID: {user.user_id}\n"
                    f"📅 Vaqt: {request.requested_at.strftime('%Y-%m-%d %H:%M')}",
                    reply_markup=user_approval_keyboard(user_id)
                )
            except Exception as e:
                logger.error(f"Adminga {admin.user_id} xabar yuborishda xatolik: {e}")
        
        await callback.answer("✅ Ruxsat so'rovingiz adminlarga yuborildi!")
        await callback.message.edit_text(
            "✅ Ruxsat so'rovingiz adminlarga yuborildi.\n"
            "Javobni kuting..."
        )
    else:
        await callback.answer("❌ Foydalanuvchi topilmadi!")

# Ruxsat berish/rad etish
@dp.callback_query(F.data.startswith("approve_"))
async def handle_approve_user(callback: CallbackQuery):
    """Foydalanuvchiga ruxsat berish"""
    admin_id = callback.from_user.id
    if admin_id != config.ADMIN_ID:
        await callback.answer("❌ Siz admin emassiz!")
        return
    
    try:
        user_id = int(callback.data.split("_")[1])
    except:
        await callback.answer("❌ Xatolik yuz berdi!")
        return
    
    db = next(database.get_db())
    
    # Foydalanuvchini faollashtirish
    user = db.query(database.User).filter(database.User.user_id == user_id).first()
    if user:
        user.is_active = True
        user.requested_access = False
        db.commit()
        
        # AdminRequest yangilash
        request = db.query(database.AdminRequest).filter(
            database.AdminRequest.user_id == user_id,
            database.AdminRequest.status == "pending"
        ).first()
        
        if request:
            request.status = "approved"
            db.commit()
        
        # Foydalanuvchiga xabar yuborish
        try:
            await bot.send_message(
                user_id,
                "🎉 Tabriklaymiz! Sizga botdan foydalanish uchun ruxsat berildi!\n\n"
                "Endi quyidagi menyu orqali test ishlashni boshlashingiz mumkin:",
                reply_markup=user_main_menu()
            )
        except Exception as e:
            logger.error(f"Foydalanuvchiga {user_id} xabar yuborishda xatolik: {e}")
        
        await callback.answer("✅ Foydalanuvchiga ruxsat berildi!")
        await callback.message.edit_text(
            f"✅ {user.first_name} (@{user.username}) ga ruxsat berildi!"
        )
    else:
        await callback.answer("❌ Foydalanuvchi topilmadi!")

@dp.callback_query(F.data.startswith("reject_"))
async def handle_reject_user(callback: CallbackQuery):
    """Foydalanuvchini rad etish"""
    admin_id = callback.from_user.id
    if admin_id != config.ADMIN_ID:
        await callback.answer("❌ Siz admin emassiz!")
        return
    
    try:
        user_id = int(callback.data.split("_")[1])
    except:
        await callback.answer("❌ Xatolik yuz berdi!")
        return
    
    db = next(database.get_db())
    
    # Foydalanuvchini rad etish
    user = db.query(database.User).filter(database.User.user_id == user_id).first()
    if user:
        user.requested_access = False
        db.commit()
        
        # AdminRequest yangilash
        request = db.query(database.AdminRequest).filter(
            database.AdminRequest.user_id == user_id,
            database.AdminRequest.status == "pending"
        ).first()
        
        if request:
            request.status = "rejected"
            db.commit()
        
        # Foydalanuvchiga xabar yuborish
        try:
            await bot.send_message(
                user_id,
                "❌ Afsuski, sizning so'rovingiz rad etildi.\n"
                "Qo'shimcha ma'lumot uchun admin bilan bog'lanishingiz mumkin."
            )
        except Exception as e:
            logger.error(f"Foydalanuvchiga {user_id} xabar yuborishda xatolik: {e}")
        
        await callback.answer("❌ Foydalanuvchi rad etildi!")
        await callback.message.edit_text(
            f"❌ {user.first_name} (@{user.username}) rad etildi!"
        )
    else:
        await callback.answer("❌ Foydalanuvchi topilmadi!")

# Admin menyusiga qaytish
@dp.callback_query(F.data == "back_to_admin_menu")
async def handle_back_to_admin_menu(callback: CallbackQuery, state: FSMContext):
    """Admin menyusiga qaytish"""
    await callback.message.delete()
    await cmd_start(callback.message, state)

# Test yaratish bo'limi
@dp.callback_query(F.data == "existing_books")
async def handle_existing_books(callback: CallbackQuery):
    """Mavjud kitoblar ro'yxati"""
    db = next(database.get_db())
    books = db.query(database.Book).all()
    
    if not books:
        await callback.message.edit_text(
            "📚 Hozircha kitoblar mavjud emas.\n"
            "Yangi kitob qo'shing:",
            reply_markup=test_creation_menu()
        )
        return
    
    await callback.message.edit_text(
        "📚 Mavjud kitoblar. Tanlang:",
        reply_markup=books_list_keyboard(books)
    )

@dp.callback_query(F.data == "add_new_book")
async def handle_add_new_book(callback: CallbackQuery, state: FSMContext):
    """Yangi kitob qo'shish"""
    await callback.message.edit_text(
        "📖 Yangi kitob uchun nom kiriting:\n\n"
        "❌ Bekor qilish: /cancel"
    )
    await state.set_state(AdminStates.waiting_for_book_name)

@dp.message(AdminStates.waiting_for_book_name)
async def process_book_name(message: Message, state: FSMContext):
    """Kitob nomini qabul qilish"""
    if message.text == "/cancel":
        await message.answer("✅ Kitob qo'shish bekor qilindi.", reply_markup=admin_main_menu())
        await state.clear()
        return
    
    book_name = message.text.strip()
    
    if len(book_name) < 2:
        await message.answer("❌ Kitob nomi juda qisqa. Qayta kiriting:")
        return
    
    db = next(database.get_db())
    
    # Kitob mavjudligini tekshirish
    existing_book = db.query(database.Book).filter(database.Book.name == book_name).first()
    if existing_book:
        await message.answer(f"❌ '{book_name}' nomli kitob allaqachon mavjud. Boshqa nom kiriting:")
        return
    
    # Yangi kitob qo'shish
    new_book = database.Book(name=book_name)
    db.add(new_book)
    db.commit()
    
    await message.answer(
        f"✅ '{book_name}' nomli yangi kitob qo'shildi!\n\n"
        f"Kitob ID: {new_book.id}",
        reply_markup=admin_main_menu()
    )
    await state.clear()

# ---------- MAIN FUNCTION ----------
async def main():
    """Asosiy funksiya"""
    logger.info("Bot ishga tushmoqda...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())