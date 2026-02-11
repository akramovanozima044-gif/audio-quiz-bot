import os
import logging
import json
import sys
import asyncio
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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Token tekshirish
if not config.BOT_TOKEN:
    logger.error("❌ BOT_TOKEN environment variable not set!")
    sys.exit(1)

logger.info(f"🔧 Konfiguratsiya yuklandi:")
logger.info(f"   Bot ID: {config.BOT_TOKEN.split(':')[0] if ':' in config.BOT_TOKEN else 'Noma\'lum'}")
logger.info(f"   Admin ID: {config.ADMIN_ID}")
logger.info(f"   Database URL: {config.DATABASE_URL[:50]}..." if config.DATABASE_URL else "   Database URL: None")

# Bot va dispatcher yaratish
try:
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
except Exception as e:
    logger.error(f"❌ Failed to initialize bot: {e}")
    sys.exit(1)

# ---------- STATES ----------
class AdminStates(StatesGroup):
    waiting_for_book_name = State()
    waiting_for_unit_name = State()
    waiting_for_question_audio = State()
    waiting_for_question_options = State()
    waiting_for_correct_answer = State()
    waiting_for_broadcast_message = State()

# ---------- HELPERS ----------
def get_db_session():
    """Database session olish"""
    return next(database.get_db())

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
    try:
        # Guruhni tekshirish
        if not await check_group(message):
            return
        
        user_id = message.from_user.id
        
        # Database session olish
        db = get_db_session()
        
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
                logger.info(f"✅ Admin yaratildi: {user_id}")
            elif not admin_user.is_admin:
                admin_user.is_admin = True
                admin_user.is_active = True
                db.commit()
                logger.info(f"✅ Admin yangilandi: {user_id}")
            
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
                logger.info(f"✅ Yangi foydalanuvchi yaratildi: {user_id}")
            
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
    
    except Exception as e:
        logger.error(f"Database xatosi: {e}")
        await message.answer("❌ Texnik xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")

# ---------- B QADAM: ADMIN MENYU HANDLERS ----------

# Test tuzish
@dp.message(F.text == "📝 Test tuzish")
async def handle_create_test(message: Message, state: FSMContext):
    """Test tuzish menyusi"""
    try:
        user_id = message.from_user.id
        db = get_db_session()
        if not await check_admin_access(user_id, db):
            await message.answer("❌ Sizda bu amalni bajarish uchun ruxsat yo'q!")
            return
        
        await message.answer("Test tuzish bo'limi. Tanlang:", reply_markup=test_creation_menu())
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await message.answer("❌ Texnik xatolik yuz berdi.")

# Test yechish
@dp.message(F.text == "🧪 Test yechish")
async def handle_take_test(message: Message):
    """Test yechish menyusi"""
    try:
        user_id = message.from_user.id
        db = get_db_session()
        if not await check_admin_access(user_id, db):
            await message.answer("❌ Sizda bu amalni bajarish uchun ruxsat yo'q!")
            return
        
        # Kitoblarni olish
        books = db.query(database.Book).all()
        
        if not books:
            await message.answer("📚 Hozircha kitoblar mavjud emas. Avval test tuzing.")
            return
        
        await message.answer("📚 Test yechish uchun kitob tanlang:", reply_markup=books_list_keyboard(books))
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await message.answer("❌ Texnik xatolik yuz berdi.")

# Test formatlash/o'chirish
@dp.message(F.text == "🗑️ Test formatlash/o'chirish")
async def handle_format_test(message: Message):
    """Test formatlash menyusi"""
    try:
        user_id = message.from_user.id
        db = get_db_session()
        if not await check_admin_access(user_id, db):
            await message.answer("❌ Sizda bu amalni bajarish uchun ruxsat yo'q!")
            return
        
        await message.answer("⚠️ Bu funksiya hozircha ishlamaydi. Tez orada qo'shiladi.")
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await message.answer("❌ Texnik xatolik yuz berdi.")

# Foydalanuvchilar ro'yxati
@dp.message(F.text == "👥 Foydalanuvchilar ro'yxati")
async def handle_users_list(message: Message):
    """Foydalanuvchilar ro'yxati"""
    try:
        user_id = message.from_user.id
        db = get_db_session()
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
    
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await message.answer("❌ Texnik xatolik yuz berdi.")

# Habar yuborish
@dp.message(F.text == "📢 Habar yuborish")
async def handle_broadcast(message: Message, state: FSMContext):
    """Habar yuborish menyusi"""
    try:
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
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await message.answer("❌ Texnik xatolik yuz berdi.")

@dp.message(AdminStates.waiting_for_broadcast_message)
async def process_broadcast_message(message: Message, state: FSMContext):
    """Habar yuborishni amalga oshirish"""
    try:
        if message.text and message.text == "/cancel":
            await message.answer("✅ Habar yuborish bekor qilindi.", reply_markup=admin_main_menu())
            await state.clear()
            return
        
        db = get_db_session()
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
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await message.answer("❌ Habar yuborishda xatolik yuz berdi.")

# Umumiy natijalar
@dp.message(F.text == "📊 Umumiy natijalar")
async def handle_overall_results(message: Message):
    """Umumiy natijalar"""
    try:
        user_id = message.from_user.id
        db = get_db_session()
        if not await check_admin_access(user_id, db):
            await message.answer("❌ Sizda bu amalni bajarish uchun ruxsat yo'q!")
            return
        
        # Natijalarni olish
        results = db.query(database.QuizResult).all()
        
        if not results:
            await message.answer("📊 Hozircha hech qanday natija mavjud emas.")
            return
        
        # Statistikani hisoblash
        total_tests = len(results)
        total_questions = sum(r.total_questions for r in results)
        total_correct = sum(r.score for r in results)
        average_score = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        response = f"📊 Umumiy statistikalar:\n\n"
        response += f"📈 Jami testlar: {total_tests}\n"
        response += f"❓ Jami savollar: {total_questions}\n"
        response += f"✅ To'g'ri javoblar: {total_correct}\n"
        response += f"📊 O'rtacha natija: {average_score:.1f}%\n\n"
        
        # Eng yaxshi 5 natija
        response += "🏆 Eng yaxshi natijalar:\n"
        top_results = sorted(results, key=lambda x: (x.score/x.total_questions if x.total_questions > 0 else 0), reverse=True)[:5]
        
        for i, result in enumerate(top_results, 1):
            user = db.query(database.User).filter(database.User.id == result.user_id).first()
            username = f"@{user.username}" if user and user.username else user.first_name if user else "Noma'lum"
            percentage = (result.score / result.total_questions * 100) if result.total_questions > 0 else 0
            response += f"{i}. {username}: {result.score}/{result.total_questions} ({percentage:.1f}%)\n"
        
        await message.answer(response)
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await message.answer("❌ Texnik xatolik yuz berdi.")

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
    
    try:
        db = get_db_session()
        
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
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await callback.answer("❌ Xatolik yuz berdi!")

# Ruxsat berish
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
    
    try:
        db = get_db_session()
        
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
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await callback.answer("❌ Xatolik yuz berdi!")

# Rad etish
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
    
    try:
        db = get_db_session()
        
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
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await callback.answer("❌ Xatolik yuz berdi!")

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
    try:
        db = get_db_session()
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
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await callback.answer("❌ Xatolik yuz berdi!")

@dp.callback_query(F.data == "add_new_book")
async def handle_add_new_book(callback: CallbackQuery, state: FSMContext):
    """Yangi kitob qo'shish"""
    try:
        await callback.message.edit_text(
            "📖 Yangi kitob uchun nom kiriting:\n\n"
            "❌ Bekor qilish: /cancel"
        )
        await state.set_state(AdminStates.waiting_for_book_name)
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await callback.answer("❌ Xatolik yuz berdi!")

@dp.message(AdminStates.waiting_for_book_name)
async def process_book_name(message: Message, state: FSMContext):
    """Kitob nomini qabul qilish"""
    try:
        if message.text == "/cancel":
            await message.answer("✅ Kitob qo'shish bekor qilindi.", reply_markup=admin_main_menu())
            await state.clear()
            return
        
        book_name = message.text.strip()
        
        if len(book_name) < 2:
            await message.answer("❌ Kitob nomi juda qisqa. Qayta kiriting:")
            return
        
        db = get_db_session()
        
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
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await message.answer("❌ Xatolik yuz berdi!")

# Kitob tanlash
@dp.callback_query(F.data.startswith("book_"))
async def handle_select_book(callback: CallbackQuery):
    """Kitob tanlash"""
    try:
        book_id = int(callback.data.split("_")[1])
        db = get_db_session()
        
        book = db.query(database.Book).filter(database.Book.id == book_id).first()
        if not book:
            await callback.answer("❌ Kitob topilmadi!")
            return
        
        # Unitlarni olish
        units = db.query(database.Unit).filter(database.Unit.book_id == book_id).all()
        
        if not units:
            await callback.message.edit_text(
                f"📘 Kitob: {book.name}\n\n"
                f"📭 Hozircha unitlar mavjud emas.\n"
                f"Yangi unit qo'shing:",
                reply_markup=units_list_keyboard([])
            )
        else:
            await callback.message.edit_text(
                f"📘 Kitob: {book.name}\n\n"
                f"Unitlarni tanlang:",
                reply_markup=units_list_keyboard(units)
            )
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await callback.answer("❌ Xatolik yuz berdi!")

# Unit tanlash
@dp.callback_query(F.data.startswith("unit_"))
async def handle_select_unit(callback: CallbackQuery):
    """Unit tanlash"""
    try:
        unit_id = int(callback.data.split("_")[1])
        db = get_db_session()
        
        unit = db.query(database.Unit).filter(database.Unit.id == unit_id).first()
        if not unit:
            await callback.answer("❌ Unit topilmadi!")
            return
        
        await callback.message.edit_text(
            f"📝 Unit: {unit.name}\n\n"
            f"✅ Testni boshlashga tayyormisiz?",
            reply_markup=start_test_keyboard()
        )
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await callback.answer("❌ Xatolik yuz berdi!")

# Testni boshlash
@dp.callback_query(F.data == "start_test")
async def handle_start_test(callback: CallbackQuery, state: FSMContext):
    """Testni boshlash"""
    try:
        await callback.message.edit_text(
            "🧪 Test boshlandi!\n\n"
            "⚠️ Test ishlash funksiyasi tez orada qo'shiladi.\n"
            "Hozircha faqat test tuzish va foydalanuvchilarni boshqarish mumkin."
        )
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await callback.answer("❌ Xatolik yuz berdi!")

# ---------- FOYDALANUVCHI MENYU HANDLERS ----------

# Mening natijalarim
@dp.message(F.text == "📊 Mening natijalarim")
async def handle_my_results(message: Message):
    """Foydalanuvchining natijalari"""
    try:
        user_id = message.from_user.id
        db = get_db_session()
        
        # Foydalanuvchi mavjudligini tekshirish
        user = db.query(database.User).filter(database.User.user_id == user_id).first()
        if not user or not user.is_active:
            await message.answer("❌ Sizda bu amalni bajarish uchun ruxsat yo'q!")
            return
        
        # Natijalarni olish
        results = db.query(database.QuizResult).filter(database.QuizResult.user_id == user.id).all()
        
        if not results:
            await message.answer("📊 Siz hali hech qanday test ishlamagansiz.")
            return
        
        response = "📊 Sizning natijalaringiz:\n\n"
        total_score = 0
        total_questions = 0
        
        for i, result in enumerate(results, 1):
            # Kitob va unit nomlarini olish
            book = db.query(database.Book).filter(database.Book.id == result.book_id).first()
            unit = db.query(database.Unit).filter(database.Unit.id == result.unit_id).first()
            
            book_name = book.name if book else "Noma'lum kitob"
            unit_name = unit.name if unit else "Noma'lum unit"
            percentage = (result.score / result.total_questions * 100) if result.total_questions > 0 else 0
            
            response += f"{i}. {book_name} - {unit_name}\n"
            response += f"   📅 {result.completed_at.strftime('%Y-%m-%d %H:%M')}\n"
            response += f"   ✅ {result.score}/{result.total_questions} ({percentage:.1f}%)\n\n"
            
            total_score += result.score
            total_questions += result.total_questions
        
        # Umumiy statistikalar
        total_percentage = (total_score / total_questions * 100) if total_questions > 0 else 0
        response += f"📈 Umumiy statistikalar:\n"
        response += f"   • Jami testlar: {len(results)}\n"
        response += f"   • To'g'ri javoblar: {total_score}/{total_questions}\n"
        response += f"   • O'rtacha natija: {total_percentage:.1f}%\n"
        
        await message.answer(response)
    except Exception as e:
        logger.error(f"Xatolik: {e}")
        await message.answer("❌ Texnik xatolik yuz berdi.")

# ---------- MAIN FUNCTION ----------
async def main():
    """Asosiy funksiya"""
    logger.info("🤖 Bot ishga tushmoqda...")
    
    try:
        # Bot ma'lumotlarini olish
        me = await bot.get_me()
        logger.info(f"✅ Bot: @{me.username} (ID: {me.id})")
        
        # Eski updateslarni tozalash
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Old updates cleared")
        
        logger.info("📡 Polling ni boshlayapti...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"❌ Xatolik yuz berdi: {e}")
    finally:
        await bot.session.close()
        logger.info("👋 Bot to'xtadi")

if __name__ == "__main__":
    asyncio.run(main())