# bot.py
# bot.py - IMPORT qismi
import asyncio
import logging
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import FSInputFile, ReplyKeyboardRemove
from aiogram.enums import ParseMode
from sqlalchemy import select

from config import config
# ✅ TO'G'RI IMPORT:
from database import User, Book, Unit, Question, TestResult, init_db, get_session
from keyboards import (
    get_admin_menu, get_user_menu, get_confirm_keyboard,
    get_books_keyboard, get_test_create_menu, get_users_management_keyboard,
    get_test_finish_menu,
    get_books_for_create_keyboard,
    get_units_keyboard,
    get_add_question_keyboard,
    get_finish_creating_keyboard,
    get_cancel_keyboard,
    get_books_for_test_keyboard,
    get_units_for_test_keyboard,
    get_start_test_keyboard,
    get_answer_options_keyboard,
    get_test_complete_menu,
    get_format_menu_keyboard,
    get_books_manage_keyboard,
    get_book_manage_options,
    get_units_manage_keyboard,
    get_unit_manage_options,
    get_questions_manage_keyboard,
    get_question_manage_options,
    get_confirmation_keyboard,
    get_users_delete_keyboard,
    get_user_delete_confirmation_keyboard,
    get_user_menu_updated
)

# Logging sozlash
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot va dispatcher
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ... boshqa FSM va funksiyalar

# FSM holatlari
class AdminStates(StatesGroup):
    waiting_for_book_name = State()
    waiting_for_unit_name = State()
    waiting_for_audio = State()
    waiting_for_options = State()
    waiting_for_correct_answer = State()
    waiting_for_broadcast = State()

    # Yangi statelar C-qadam uchun
    waiting_for_new_book_name = State()
    waiting_for_new_unit_name = State()
    waiting_for_question_audio = State()
    waiting_for_question_options = State()
    waiting_for_correct_option = State()

class UserStates(StatesGroup):
    waiting_for_test_start = State()
    answering_question = State()

# FSM holatlari (bot.py da) - D-qadam uchun
class TestStates(StatesGroup):
    waiting_for_test_confirmation = State()
    answering_question = State()
    test_completed = State()

# FSM holatlari (bot.py da) - E-qadam uchun
class FormatStates(StatesGroup):
    waiting_for_new_book_name = State()
    waiting_for_new_unit_name = State()
    waiting_for_new_question_audio = State()
    waiting_for_new_question_options = State()
    waiting_for_new_correct_answer = State()    

# =================== A-QADAM: ASOSIY FUNKSIYALAR ===================

# Start command - ADMIN uchun
# bot.py - Start handler ni yangilaymiz

# bot.py - Start handler

# bot.py - To'g'rilangan start handler

@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    
    async_session = await get_session()
    async with async_session() as session:
        try:
            # Foydalanuvchini bazada qidirish (Telegram user_id bo'yicha)
            stmt = select(User).where(User.user_id == message.from_user.id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            logger.info(f"Start command: User search - Telegram ID: {message.from_user.id}, Found: {user.id if user else 'Not found'}")
            
            if not user:
                # Yangi foydalanuvchi qo'shish
                user = User(
                    user_id=message.from_user.id,
                    username=message.from_user.username,
                    first_name=message.from_user.first_name,
                    last_name=message.from_user.last_name,
                    is_admin=(message.from_user.id == config.ADMIN_ID)
                )
                session.add(user)
                await session.commit()
                logger.info(f"✅ Yangi foydalanuvchi qo'shildi: {message.from_user.id}")
            else:
                logger.info(f"✅ Foydalanuvchi allaqachon mavjud: {user.id}")
            
            # Agar admin bo'lsa
            if message.from_user.id == config.ADMIN_ID:
                await message.answer(
                    "👋 Salom, Admin!\n"
                    "Audio Quiz Botiga xush kelibsiz!",
                    reply_markup=get_admin_menu()
                )
            else:
                # Oddiy foydalanuvchi uchun
                if user.is_active:
                    await message.answer(
                        "👋 Botga xush kelibsiz!\n"
                        "Quyidagi funksiyalardan foydalanishingiz mumkin:",
                        reply_markup=get_user_menu()
                    )
                else:
                    # Admin dan ruxsat so'rash
                    await message.answer(
                        "Botdan foydalanish uchun admin ruxsati kerak.\n"
                        "Ruxsat so'rovi admin ga yuborildi."
                    )
                    
                    # Admin ga so'rov yuborish
                    admin_text = (
                        f"🔔 Yangi foydalanuvchi:\n"
                        f"ID: {message.from_user.id}\n"
                        f"Username: @{message.from_user.username}\n"
                        f"Ism: {message.from_user.first_name}\n"
                        f"Botdan foydalanishga ruxsat so'ramoqda."
                    )
                    await bot.send_message(
                        config.ADMIN_ID,
                        admin_text,
                        reply_markup=get_confirm_keyboard()
                    )
                    
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await message.answer("❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

# =================== B-QADAM: ADMIN MENU ===================

# Admin menyusi
@dp.message(F.text == "📝 Test tuzish")
async def admin_create_test(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return

    async_session = await get_session()
    await message.answer(
        "📝 Test tuzish bo'limi:\n"
        "Kerakli amalni tanlang:",
        reply_markup=get_test_create_menu()
    )

# bot.py da admin test yechish funksiyasini yangilash

@dp.message(F.text == "🧪 Test yechish")
async def admin_solve_test(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return
    
    async_session = await get_session()
    async with async_session() as session:
        stmt = select(Book)
        result = await session.execute(stmt)
        books_list = result.scalars().all()
        
        if not books_list:
            await message.answer("📭 Hozircha kitoblar mavjud emas.")
            return
            
        await message.answer(
            "📚 Test yechish uchun kitobni tanlang:",
            reply_markup=get_books_for_test_keyboard(books_list, "admin")
        )

# bot.py da menyularga qaytish

# User menyusiga qaytish
@dp.message(F.text == "🏠 User menyusi")
async def back_to_user_main(message: types.Message, state: FSMContext):
    await state.clear()
    
    async_session = await get_session()
    async with async_session() as session:
        # Foydalanuvchi aktivligini tekshirish
        stmt = select(User).where(User.user_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            await message.answer(
                "❌ Sizga botdan foydalanishga ruxsat berilmagan.\n"
                "Admin dan ruxsat so'rang."
            )
            return
    
    await message.answer("User menyusi:", reply_markup=get_user_menu())

# Admin menyusiga qaytish
@dp.message(F.text == "🏠 Admin menyusi")
async def back_to_admin_main_from_test(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Admin menyusi:", reply_markup=get_admin_menu())        



@dp.message(F.text == "👥 Foydalanuvchilar ro'yxati")
async def admin_users_list(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return
    
    await message.answer(
        "👥 Foydalanuvchilarni boshqarish:",
        reply_markup=get_users_management_keyboard()
    )

# Foydalanuvchilarni ko'rish
@dp.message(F.text == "👁️ Foydalanuvchilarni ko'rish")
async def view_users(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return
    
    async_session = await get_session()
    async with async_session() as session:
        stmt = select(User).where(User.is_admin == False)
        result = await session.execute(stmt)
        users_list = result.scalars().all()
        
        if not users_list:
            await message.answer("📭 Hozircha foydalanuvchilar yo'q.")
            return
        
        text = "📋 Foydalanuvchilar ro'yxati:\n\n"
        for user in users_list:
            status = "✅ Faol" if user.is_active else "❌ Nofaol"
            username = f"@{user.username}" if user.username else "Yo'q"
            text += f"👤 {user.first_name} ({username})\n"
            text += f"ID: {user.user_id}\n"
            text += f"Holat: {status}\n"
            text += f"Qo'shilgan: {user.created_at.strftime('%Y-%m-%d')}\n"
            text += "─" * 20 + "\n"
        
        await message.answer(text)

# Foydalanuvchini o'chirish (keyingi qadamda)
@dp.message(F.text == "❌ Foydalanuvchini o'chirish")
async def delete_user(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return
    
    await message.answer("⚠️ Bu funksiya F-qadamda qo'shiladi.")

@dp.message(F.text == "📢 Habar yuborish")
async def admin_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return
    
    await message.answer(
        "📢 Barcha foydalanuvchilarga habar yuborish:\n"
        "Yubormoqchi bo'lgan habaringizni yuboring:"
    )
    await state.set_state(AdminStates.waiting_for_broadcast)



# =================== CALLBACK HANDLERS ===================

# Foydalanuvchiga ruxsat berish/rad etish
@dp.callback_query(F.data.in_(["allow_user", "deny_user"]))
async def handle_user_permission(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    # User ID ni olish (matndan)
    message_text = callback.message.text
    lines = message_text.split('\n')
    user_id = None
    
    for line in lines:
        if 'ID:' in line:
            user_id = int(line.split(': ')[1])
            break
    
    if not user_id:
        await callback.answer("User ID topilmadi!", show_alert=True)
        return
    
    async with async_session() as session:
        # user_id bo'yicha qidirish
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
            return
        
        if callback.data == "allow_user":
            user.is_active = True
            await session.commit()
            
            await callback.message.edit_text(
                f"✅ Foydalanuvchi {user.first_name} ga ruxsat berildi."
            )
            
            # Foydalanuvchiga xabar yuborish
            try:
                await bot.send_message(
                    user_id,
                    "✅ Sizga botdan foydalanishga ruxsat berildi!\n"
                    "Endi /start ni bosing va test yechishni boshlang.",
                    reply_markup=get_user_menu()
                )
            except Exception as e:
                logger.error(f"Xatolik foydalanuvchiga xabar yuborishda: {e}")
        
        elif callback.data == "deny_user":
            await callback.message.edit_text(
                f"❌ Foydalanuvchi {user.first_name} rad etildi."
            )
            
            # Foydalanuvchiga xabar yuborish
            try:
                await bot.send_message(
                    user_id,
                    "❌ Sizga botdan foydalanishga ruxsat berilmadi."
                )
            except Exception as e:
                logger.error(f"Xatolik foydalanuvchiga xabar yuborishda: {e}")
    
    await callback.answer()

# Broadcast xabar yuborish
@dp.message(AdminStates.waiting_for_broadcast)
async def send_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        return
    
    async_session = await get_session()
    async with async_session() as session:
        stmt = select(User.user_id).where(
            (User.is_active == True) & 
            (User.is_admin == False)
        )
        result = await session.execute(stmt)
        active_users = result.scalars().all()
        
        sent = 0
        failed = 0
        
        await message.answer(f"📤 Habar {len(active_users)} ta foydalanuvchiga yuborilmoqda...")
        
        for user_id in active_users:
            try:
                await bot.send_message(user_id, message.text)
                sent += 1
                await asyncio.sleep(0.1)  # Rate limit uchun
            except Exception as e:
                logger.error(f"Xatolik {user_id} ga xabar yuborishda: {e}")
                failed += 1
        
        await message.answer(
            f"📊 Habar yuborish yakunlandi:\n"
            f"✅ Muvaffaqiyatli: {sent}\n"
            f"❌ Xatolik: {failed}"
        )
    
    await state.clear()
    await message.answer("Admin menyusi:", reply_markup=get_admin_menu())

# Orqaga tugmalari
@dp.callback_query(F.data == "back_to_admin_menu")
async def back_to_admin_menu(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    await callback.message.delete()
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_menu()
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_books")
async def back_to_books(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    async_session = await get_session()
    async with async_session() as session:
        stmt = select(Book)
        result = await session.execute(stmt)
        books_list = result.scalars().all()
        
        await callback.message.edit_text(
            "📚 Mavjud kitoblarni tanlang:",
            reply_markup=get_books_keyboard(books_list, "select")
        )
    await callback.answer()

# bot.py da test tuzish funksiyalarini qo'shamiz

# =================== C-QADAM: TEST TUZISH ===================

# Test tuzish menyusi
@dp.message(F.text == "📚 Mavjud kitoblar")
async def show_existing_books(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return
    
    async_session = await get_session()
    async with async_session() as session:
        stmt = select(Book)
        result = await session.execute(stmt)
        books_list = result.scalars().all()
        
        if not books_list:
            await message.answer(
                "📭 Hozircha kitoblar mavjud emas.\n"
                "Yangi kitob qo'shing.",
                reply_markup=get_test_create_menu()
            )
            return
            
        await message.answer(
            "📚 Mavjud kitoblarni tanlang:",
            reply_markup=get_books_for_create_keyboard(books_list)
        )

# Yangi kitob qo'shish
@dp.message(F.text == "➕ Yangi kitob qo'shish")
async def add_new_book_start(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return
    
    await message.answer(
        "📖 Yangi kitob qo'shish:\n"
        "Kitob nomini kiriting:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_new_book_name)

# Yangi kitob nomini qabul qilish
@dp.message(AdminStates.waiting_for_new_book_name)
async def process_new_book_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=get_test_create_menu())
        return
    
    async_session = await get_session()
    async with async_session() as session:
        # Kitobni bazaga qo'shish
        new_book = Book(
            name=message.text
        )
        session.add(new_book)
        await session.commit()
        
        await message.answer(
            f"✅ Kitob qo'shildi: {message.text}\n\n"
            f"Endi bu kitobga unit (bob) qo'shing.",
            reply_markup=get_test_create_menu()
        )
    
    await state.clear()

# Mavjud kitobni tanlash (test tuzish uchun)
@dp.callback_query(F.data.startswith("create_book_"))
async def select_book_for_create(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    book_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        # Kitobning unitlarini olish
        stmt = select(Unit).where(Unit.book_id == book_id)
        result = await session.execute(stmt)
        units_list = result.scalars().all()
        
        book = await session.get(Book, book_id)
        
        if not units_list:
            await callback.message.edit_text(
                f"📘 Kitob: {book.name}\n\n"
                f"Hozircha unitlar mavjud emas.\n"
                f"Yangi unit qo'shing:",
                reply_markup=get_units_keyboard([], book_id)
            )
        else:
            await callback.message.edit_text(
                f"📘 Kitob: {book.name}\n\n"
                f"Mavjud unitlar:",
                reply_markup=get_units_keyboard(units_list, book_id)
            )
    
    await callback.answer()

# Yangi kitob qo'shish (inline)
@dp.callback_query(F.data == "add_new_book_for_create")
async def add_new_book_inline(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "📖 Yangi kitob qo'shish:\n"
        "Kitob nomini kiriting:"
    )
    await state.set_state(AdminStates.waiting_for_new_book_name)
    await callback.answer()

# Yangi unit qo'shish
@dp.callback_query(F.data.startswith("add_unit_"))
async def add_new_unit_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    book_id = int(callback.data.split("_")[-1])
    
    # Book ID ni saqlab qo'yish
    await state.update_data(book_id=book_id)
    
    await callback.message.edit_text(
        "📝 Yangi unit (bob) qo'shish:\n"
        "Unit nomini kiriting:"
    )
    await state.set_state(AdminStates.waiting_for_new_unit_name)
    await callback.answer()

# Yangi unit nomini qabul qilish
@dp.message(AdminStates.waiting_for_new_unit_name)
async def process_new_unit_name(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    book_id = user_data.get('book_id')
    
    async_session = await get_session()
    async with async_session() as session:
        # Unitni bazaga qo'shish
        new_unit = Unit(
            book_id=book_id,
            name=message.text
        )
        session.add(new_unit)
        await session.commit()
        
        book = await session.get(Book, book_id)
        
        await message.answer(
            f"✅ Unit qo'shildi: {message.text}\n\n"
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {message.text}\n\n"
            f"Endi bu unitga savol qo'shing.",
            reply_markup=ReplyKeyboardRemove()
        )
        
        # Savol qo'shish tugmalarini ko'rsatish
        await message.answer(
            "Kerakli amalni tanlang:",
            reply_markup=get_add_question_keyboard(new_unit.id)
        )
    
    await state.clear()

# Mavjud unitni tanlash
@dp.callback_query(F.data.startswith("create_unit_"))
async def select_unit_for_create(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    unit_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        
        # Unitdagi savollarni sanash
        stmt = select(Question).where(Question.unit_id == unit_id)
        result = await session.execute(stmt)
        questions = result.scalars().all()
        
        await callback.message.edit_text(
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {unit.name}\n\n"
            f"📊 Savollar soni: {len(questions)}\n\n"
            f"Kerakli amalni tanlang:",
            reply_markup=get_add_question_keyboard(unit_id)
        )
    
    await callback.answer()

# Savol qo'shishni boshlash
@dp.callback_query(F.data.startswith("add_question_"))
async def add_question_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    unit_id = int(callback.data.split("_")[-1])
    
    # Unit ID ni saqlab qo'yish
    await state.update_data(unit_id=unit_id)
    
    await callback.message.edit_text(
        "🎵 1-qadam: Audio savol yuboring\n\n"
        "Iltimos, savol audiosini yuboring (MP3 yoki OGG formatda):"
    )
    await state.set_state(AdminStates.waiting_for_question_audio)
    await callback.answer()

# Audio qabul qilish
@dp.message(AdminStates.waiting_for_question_audio, F.audio | F.voice | F.document)
async def process_question_audio(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    unit_id = user_data.get('unit_id')
    
    # Audio fayl ma'lumotlarini saqlash
    if message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or "audio.mp3"
    elif message.voice:
        file_id = message.voice.file_id
        file_name = "voice.ogg"
    elif message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "audio.mp3"
    
    # Fayl ID sini saqlab qo'yish
    await state.update_data(audio_file_id=file_id, audio_file_name=file_name)
    
    await message.answer(
        f"✅ Audio qabul qilindi.\n\n"
        f"🎵 Fayl: {file_name}\n\n"
        f"2-qadam: Variantlarni kiriting\n\n"
        f"Variantlarni vergul bilan ajrating (masalan: A) Cat, B) Dog, C) Bird, D) Fish):"
    )
    await state.set_state(AdminStates.waiting_for_question_options)

# Variantlarni qabul qilish
@dp.message(AdminStates.waiting_for_question_options)
async def process_question_options(message: types.Message, state: FSMContext):
    options = message.text.split(',')
    options = [opt.strip() for opt in options if opt.strip()]
    
    if len(options) < 2:
        await message.answer(
            "❌ Kamida 2 ta variant kiriting!\n"
            "Variantlarni vergul bilan ajratib kiriting:"
        )
        return
    
    # Variantlarni saqlab qo'yish
    await state.update_data(options=options)
    
    # Variantlarni ko'rsatish
    options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    
    await message.answer(
        f"✅ Variantlar qabul qilindi:\n\n"
        f"{options_text}\n\n"
        f"3-qadam: To'g'ri javobni tanlang\n\n"
        f"To'g'ri javob raqamini kiriting (1 dan {len(options)} gacha):"
    )
    await state.set_state(AdminStates.waiting_for_correct_option)

# To'g'ri javobni qabul qilish
@dp.message(AdminStates.waiting_for_correct_option)
async def process_correct_option(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    unit_id = user_data.get('unit_id')
    options = user_data.get('options', [])
    
    try:
        correct_index = int(message.text) - 1
        
        if correct_index < 0 or correct_index >= len(options):
            await message.answer(
                f"❌ Noto'g'ri raqam! 1 dan {len(options)} gacha raqam kiriting:"
            )
            return
        
        correct_answer = options[correct_index]
        
        # Fayl ID sini olish
        audio_file_id = user_data.get('audio_file_id')
        
        async with async_session() as session:
            # Savolni bazaga qo'shish
            new_question = Question(
                unit_id=unit_id,
                audio_file=audio_file_id,  # Telegram file ID
                options=str(options),  # Listni stringga aylantiramiz
                correct_answer=correct_answer
            )
            session.add(new_question)
            await session.commit()
            
            unit = await session.get(Unit, unit_id)
            book = await session.get(Book, unit.book_id)
            
            await message.answer(
                f"✅ Savol muvaffaqiyatli qo'shildi!\n\n"
                f"📘 Kitob: {book.name}\n"
                f"📝 Unit: {unit.name}\n"
                f"🎵 Audio savol: ✅\n"
                f"📋 Variantlar: {len(options)} ta\n"
                f"✅ To'g'ri javob: {correct_answer}\n\n"
                f"Yana savol qo'shishni davom ettirishingiz mumkin:",
                reply_markup=get_finish_creating_keyboard(unit_id)
            )
    
    except ValueError:
        await message.answer("❌ Iltimos, raqam kiriting!")
        return
    
    await state.clear()

# Yana savol qo'shish
@dp.callback_query(F.data.startswith("add_more_question_"))
async def add_more_question(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    unit_id = int(callback.data.split("_")[-1])
    
    # Unit ID ni saqlab qo'yish
    await state.update_data(unit_id=unit_id)
    
    await callback.message.edit_text(
        "🎵 Yangi audio savol yuboring:\n\n"
        "Iltimos, savol audiosini yuboring (MP3 yoki OGG formatda):"
    )
    await state.set_state(AdminStates.waiting_for_question_audio)
    await callback.answer()

# Test yaratishni yakunlash
@dp.callback_query(F.data.startswith("finish_creating_"))
async def finish_creating(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    unit_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        
        # Unitdagi savollarni sanash
        stmt = select(Question).where(Question.unit_id == unit_id)
        result = await session.execute(stmt)
        questions = result.scalars().all()
        
        await callback.message.edit_text(
            f"✅ Test yaratish yakunlandi!\n\n"
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {unit.name}\n"
            f"📊 Jami savollar: {len(questions)} ta\n\n"
            f"Test muvaffaqiyatli saqlandi."
        )
        
        # Asosiy menyuga qaytish
        await callback.message.answer(
            "Asosiy menyu:",
            reply_markup=get_admin_menu()
        )
    
    await callback.answer()

# Orqaga tugmalari (yangi)
@dp.callback_query(F.data.startswith("back_to_units_"))
async def back_to_units(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    book_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        stmt = select(Unit).where(Unit.book_id == book_id)
        result = await session.execute(stmt)
        units_list = result.scalars().all()
        
        book = await session.get(Book, book_id)
        
        await callback.message.edit_text(
            f"📘 Kitob: {book.name}\n\n"
            f"Mavjud unitlar:",
            reply_markup=get_units_keyboard(units_list, book_id)
        )
    
    await callback.answer()

@dp.callback_query(F.data.startswith("back_to_books_"))
async def back_to_books_from_units(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    async_session = await get_session()
    async with async_session() as session:
        stmt = select(Book)
        result = await session.execute(stmt)
        books_list = result.scalars().all()
        
        await callback.message.edit_text(
            "📚 Mavjud kitoblarni tanlang:",
            reply_markup=get_books_for_create_keyboard(books_list)
        )
    
    await callback.answer()

@dp.callback_query(F.data == "back_to_test_create_menu")
async def back_to_test_create_menu(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    await callback.message.delete()
    await callback.message.answer(
        "📝 Test tuzish bo'limi:\n"
        "Kerakli amalni tanlang:",
        reply_markup=get_test_create_menu()
    )
    await callback.answer()

# Bekor qilish
@dp.message(F.text == "❌ Bekor qilish")
async def cancel_operation(message: types.Message, state: FSMContext):
    if message.from_user.id != config.ADMIN_ID:
        return
    
    await state.clear()
    await message.answer(
        "❌ Amal bekor qilindi.",
        reply_markup=get_test_create_menu()
    )    

# =================== ORQA MENYU ===================
@dp.message(F.text == "🔙 Orqaga")
async def back_to_admin_main(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        return
    
    await message.answer("Asosiy menyu:", reply_markup=get_admin_menu())


# bot.py da user menyusi funksiyalari

# User menyusi
@dp.message(F.text == "📚 Test yechish")
async def user_test_solve(message: types.Message):
    
    async_session = await get_session()
    async with async_session() as session:
        # Foydalanuvchi aktivligini tekshirish
        stmt = select(User).where(User.user_id == message.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            await message.answer(
                "❌ Sizga botdan foydalanishga ruxsat berilmagan.\n"
                "Admin dan ruxsat so'rang."
            )
            return
    
    # Kitoblarni ko'rsatish
    async with async_session() as session:
        stmt = select(Book)
        result = await session.execute(stmt)
        books_list = result.scalars().all()
        
        if not books_list:
            await message.answer("📭 Hozircha testlar mavjud emas.")
            return
            
        await message.answer(
            "📚 Test yechish uchun kitobni tanlang:",
            reply_markup=get_books_for_test_keyboard(books_list, "user")
        )

# bot.py da test yechish funksiyalari

# Kitobni tanlash (test yechish uchun)
@dp.callback_query(F.data.startswith("test_book_"))
async def select_book_for_test(callback: types.CallbackQuery):
    data_parts = callback.data.split("_")
    book_id = int(data_parts[2])
    user_type = data_parts[3]  # "admin" yoki "user"
    
    # User uchun ruxsatni tekshirish
    if user_type == "user":
        async_session = await get_session()
        async with async_session() as session:
            stmt = select(User).where(User.user_id == callback.from_user.id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                await callback.answer("❌ Sizga ruxsat yo'q!", show_alert=True)
                return
    
    async with async_session() as session:
        # Kitobning unitlarini olish
        stmt = select(Unit).where(Unit.book_id == book_id)
        result = await session.execute(stmt)
        units_list = result.scalars().all()
        
        book = await session.get(Book, book_id)
        
        if not units_list:
            await callback.message.edit_text(
                f"📘 Kitob: {book.name}\n\n"
                f"Hozircha testlar mavjud emas."
            )
        else:
            await callback.message.edit_text(
                f"📘 Kitob: {book.name}\n\n"
                f"Test yechish uchun unitni tanlang:",
                reply_markup=get_units_for_test_keyboard(units_list, book_id, user_type)
            )
    
    await callback.answer()

# Unitni tanlash (test yechish uchun)
@dp.callback_query(F.data.startswith("test_unit_"))
async def select_unit_for_test(callback: types.CallbackQuery):
    data_parts = callback.data.split("_")
    unit_id = int(data_parts[2])
    user_type = data_parts[3]
    
    # User uchun ruxsatni tekshirish
    if user_type == "user":
        async_session = await get_session()
        async with async_session() as session:
            stmt = select(User).where(User.user_id == callback.from_user.id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                await callback.answer("❌ Sizga ruxsat yo'q!", show_alert=True)
                return
    
    async with async_session() as session:
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        
        # Unitdagi savollarni sanash
        stmt = select(Question).where(Question.unit_id == unit_id)
        result = await session.execute(stmt)
        questions = result.scalars().all()
        
        if not questions:
            await callback.message.edit_text(
                f"📘 Kitob: {book.name}\n"
                f"📝 Unit: {unit.name}\n\n"
                f"❌ Bu unitda savollar mavjud emas."
            )
            return
        
        await callback.message.edit_text(
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {unit.name}\n\n"
            f"📊 Savollar soni: {len(questions)} ta\n"
            f"⏱️ Taxminiy vaqt: {len(questions) * 2} daqiqa\n\n"
            f"Testni boshlashga tayyormisiz?",
            reply_markup=get_start_test_keyboard(unit_id, user_type)
        )
    
    await callback.answer()

# Testni yakunlash
# bot.py - To'g'rilangan finish_test funksiyasi

# bot.py - To'g'rilangan finish_test funksiyasi

# bot.py - To'g'rilangan finish_test funksiyasi

async def finish_test(message: types.Message, state: FSMContext):
    """Testni yakunlash va natijalarni saqlash"""
    user_data = await state.get_data()
    
    score = user_data.get('score', 0)
    total_questions = user_data.get('total_questions', 0)
    unit_id = user_data.get('unit_id')
    book_id = user_data.get('book_id')
    user_type = user_data.get('user_type', 'user')
    
    logger.info(f"🔧 finish_test: User ID={message.from_user.id}, Score={score}/{total_questions}, Unit={unit_id}, Book={book_id}")
    
    # Foizni hisoblash
    percentage = (score / total_questions * 100) if total_questions > 0 else 0
    
    # Natijani bazaga saqlash
    async with async_session() as session:
        try:
            # 1. Foydalanuvchini Telegram user_id bo'yicha topish
            user_stmt = select(User).where(User.user_id == message.from_user.id)
            user_result = await session.execute(user_stmt)
            user = user_result.scalar_one_or_none()
            
            if not user:
                logger.error(f"❌ User not found for Telegram ID: {message.from_user.id}")
                await message.answer("❌ Foydalanuvchi topilmadi. Iltimos, /start ni bosing.")
                return
            
            logger.info(f"✅ User found: DB ID={user.id}, Telegram ID={user.user_id}")
            
            # 2. Test natijasini saqlash
            if unit_id and book_id:
                test_result = TestResult(
                    user_id=user.id,
                    book_id=book_id,
                    unit_id=unit_id,
                    score=score,
                    total_questions=total_questions
                )
                session.add(test_result)
                await session.commit()
                
                logger.info(f"✅ Test result SAVED: User ID={user.id}, TestResult ID={test_result.id}, Score={score}/{total_questions}")
                
                # 3. Saqlangan natijani tekshirish
                check_stmt = select(TestResult).where(TestResult.user_id == user.id)
                check_result = await session.execute(check_stmt)
                saved_results = check_result.scalars().all()
                
                logger.info(f"📊 User now has {len(saved_results)} test results in database")
                
                for res in saved_results:
                    logger.info(f"   - TestResult ID: {res.id}, Score: {res.score}/{res.total_questions}, Date: {res.completed_at}")
                
            else:
                logger.error(f"❌ Missing data: unit_id={unit_id}, book_id={book_id}")
                await message.answer("❌ Test ma'lumotlari to'liq emas.")
                
        except Exception as e:
            logger.error(f"❌ Error saving test result: {e}", exc_info=True)
            await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
    
    # Natijani ko'rsatish
    result_text = (
        f"🎉 Test yakunlandi!\n\n"
        f"📊 Natijangiz:\n"
        f"✅ To'g'ri javoblar: {score}/{total_questions}\n"
        f"📈 Foiz: {percentage:.1f}%\n\n"
    )
    
    if percentage >= 80:
        result_text += "🏆 A'lo natija! Tabriklaymiz! 🎯\n"
    elif percentage >= 60:
        result_text += "👍 Yaxshi natija! Davom eting! 💪\n"
    elif percentage >= 40:
        result_text += "📚 O'rtacha natija. Yana mashq qiling! 📖\n"
    else:
        result_text += "📝 Qaytadan urinib ko'ring. Siz qila olasiz! ✨\n"
    
    await message.answer(
        result_text,
        reply_markup=get_test_complete_menu(user_type)
    )
    
    await state.clear()

# Testni boshlash
@dp.callback_query(F.data.startswith("start_test_"))
async def start_test(callback: types.CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    unit_id = int(data_parts[2])
    user_type = data_parts[3]
    
    # User uchun ruxsatni tekshirish
    if user_type == "user":
        async_session = await get_session()
        async with async_session() as session:
            stmt = select(User).where(User.user_id == callback.from_user.id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user or not user.is_active:
                await callback.answer("❌ Sizga ruxsat yo'q!", show_alert=True)
                return
    
    async with async_session() as session:
        # Unit va savollarni olish
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        
        stmt = select(Question).where(Question.unit_id == unit_id)
        result = await session.execute(stmt)
        questions = result.scalars().all()
        
        if not questions:
            await callback.answer("❌ Savollar topilmadi!", show_alert=True)
            return
        
        # Foydalanuvchini aniqlash
        user_stmt = select(User).where(User.user_id == callback.from_user.id)
        user_result = await session.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        
        # Test ma'lumotlarini saqlash
        await state.update_data(
            unit_id=unit_id,
            book_id=book.id,
            user_id=user.id if user else None,
            questions=questions,
            current_question_index=0,
            score=0,
            total_questions=len(questions),
            user_type=user_type,
            user_answers=[],
            start_time=callback.message.date
        )
        
        # Birinchi savolni yuborish
        await send_question(callback.message, state, 0)
    
    await callback.answer()

# Savolni yuborish funksiyasi
async def send_question(message: types.Message, state: FSMContext, question_index: int):
    user_data = await state.get_data()
    questions = user_data.get('questions', [])
    
    if question_index >= len(questions):
        await finish_test(message, state)
        return
    
    question = questions[question_index]
    
    try:
        # Variantlarni olish
        import ast
        options = ast.literal_eval(question.options) if isinstance(question.options, str) else question.options
    except:
        options = ["A", "B", "C", "D"]  # Default variantlar
    
    # Audio yuborish
    await message.answer_audio(
        audio=question.audio_file,
        caption=f"Savol {question_index + 1}/{len(questions)}"
    )
    
    # Variantlarni yuborish
    await message.answer(
        f"❓ Savol {question_index + 1}: Javob variantlarini tanlang:",
        reply_markup=get_answer_options_keyboard(options, question_index)
    )
    
    # Holatni yangilash
    await state.set_state(TestStates.answering_question)
    await state.update_data(current_question_index=question_index)

# Javobni qabul qilish


# Testni yakunlash
# bot.py - finish_test funksiyasi (taxminiy 600-700 qator oralig'ida)



@dp.callback_query(F.data.startswith("answer_"))
async def process_answer(callback: types.CallbackQuery, state: FSMContext):
    data_parts = callback.data.split("_")
    answer_index = int(data_parts[1])
    question_index = int(data_parts[2])
    
    user_data = await state.get_data()
    questions = user_data.get('questions', [])
    current_index = user_data.get('current_question_index', 0)
    
    # Agar hozirgi savol emas boshqa savolga javob bersa
    if question_index != current_index:
        await callback.answer("Bu savolga allaqachon javob berdingiz!", show_alert=True)
        return
    
    if question_index >= len(questions):
        await callback.answer("Test yakunlandi!", show_alert=True)
        return
    
    question = questions[question_index]
    
    try:
        # Variantlarni olish
        import ast
        options = ast.literal_eval(question.options) if isinstance(question.options, str) else question.options
    except:
        options = ["A", "B", "C", "D"]
    
    # Javobni tekshirish
    user_answer = options[answer_index] if answer_index < len(options) else ""
    is_correct = (user_answer == question.correct_answer)
    
    # Javoblarni saqlash
    user_answers = user_data.get('user_answers', [])
    user_answers.append({
        'question_id': question.id,
        'user_answer': user_answer,
        'correct_answer': question.correct_answer,
        'is_correct': is_correct
    })
    
    # Ballarni hisoblash
    score = user_data.get('score', 0)
    if is_correct:
        score += 1
    
    await state.update_data(
        score=score,
        user_answers=user_answers,
        current_question_index=question_index + 1
    )
    
    # Javob haqida bildirish
    if is_correct:
        await callback.message.answer(f"✅ To'g'ri! Javob: {question.correct_answer}")
    else:
        await callback.message.answer(f"❌ Noto'g'ri! To'g'ri javob: {question.correct_answer}")
    
    # Keyingi savolga o'tish yoki testni yakunlash
    next_index = question_index + 1
    if next_index < len(questions):
        await asyncio.sleep(1)  # Kichik pauza
        await send_question(callback.message, state, next_index)
    else:
        await finish_test(callback.message, state)
    
    await callback.answer()

# Testni qayta boshlash
@dp.message(F.text == "🔄 Testni qayta boshlash")
async def restart_test(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    unit_id = user_data.get('unit_id')
    user_type = user_data.get('user_type', 'user')
    
    if not unit_id:
        await message.answer("❌ Test ma'lumotlari topilmadi.")
        return
    
    # Unit ma'lumotlarini olish
    async_session = await get_session()
    async with async_session() as session:
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        
        stmt = select(Question).where(Question.unit_id == unit_id)
        result = await session.execute(stmt)
        questions = result.scalars().all()
        
        if not questions:
            await message.answer("❌ Savollar topilmadi!")
            return
        
        # Test ma'lumotlarini yangilash
        await state.update_data(
            questions=questions,
            current_question_index=0,
            score=0,
            total_questions=len(questions),
            user_answers=[]
        )
        
        # Birinchi savolni yuborish
        await send_question(message, state, 0)

# Orqaga tugmalari (test yechish uchun)
@dp.callback_query(F.data.startswith("back_to_test_units_"))
async def back_to_test_units_from_start(callback: types.CallbackQuery):
    data_parts = callback.data.split("_")
    unit_id = int(data_parts[-2])
    user_type = data_parts[-1]
    
    async_session = await get_session()
    async with async_session() as session:
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        
        # Unitdagi savollarni sanash
        stmt = select(Question).where(Question.unit_id == unit_id)
        result = await session.execute(stmt)
        questions = result.scalars().all()
        
        await callback.message.edit_text(
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {unit.name}\n\n"
            f"📊 Savollar soni: {len(questions)} ta\n"
            f"⏱️ Taxminiy vaqt: {len(questions) * 2} daqiqa\n\n"
            f"Testni boshlashga tayyormisiz?",
            reply_markup=get_start_test_keyboard(unit_id, user_type)
        )
    
    await callback.answer()

@dp.callback_query(F.data.startswith("back_to_test_books_"))
async def back_to_test_books(callback: types.CallbackQuery):
    user_type = callback.data.split("_")[-1]
    
    async_session = await get_session()
    async with async_session() as session:
        stmt = select(Book)
        result = await session.execute(stmt)
        books_list = result.scalars().all()
        
        await callback.message.edit_text(
            "📚 Test yechish uchun kitobni tanlang:",
            reply_markup=get_books_for_test_keyboard(books_list, user_type)
        )
    
    await callback.answer()

@dp.callback_query(F.data == "back_to_user_menu")
async def back_to_user_menu(callback: types.CallbackQuery):
    async_session = await get_session()
    async with async_session() as session:
        # Foydalanuvchi aktivligini tekshirish
        stmt = select(User).where(User.user_id == callback.from_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            await callback.answer("❌ Sizga ruxsat yo'q!", show_alert=True)
            return
    
    await callback.message.delete()
    await callback.message.answer(
        "User menyusi:",
        reply_markup=get_user_menu()
    )
    await callback.answer()      

# bot.py da formatlash funksiyalari

# =================== E-QADAM: TESTNI FORMATLASH/O'CHIRISH ===================

# Formatlash menyusi
@dp.message(F.text == "🗑️ Test formatlash/o'chirish")
async def format_test_menu(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return
    
    await message.answer(
        "🗑️ Test formatlash/o'chirish bo'limi:\n\n"
        "Kerakli amalni tanlang:",
        reply_markup=get_format_menu_keyboard()
    )

# Kitoblarni boshqarish
@dp.message(F.text == "📚 Kitoblarni boshqarish")
async def manage_books(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return

    async_session = await get_session()
    async with async_session() as session:
        stmt = select(Book)
        result = await session.execute(stmt)
        books_list = result.scalars().all()
        
        if not books_list:
            await message.answer("📭 Hozircha kitoblar mavjud emas.")
            return
            
        await message.answer(
            "📚 Mavjud kitoblar:\n"
            "O'zgartirmoqchi bo'lgan kitobni tanlang:",
            reply_markup=get_books_manage_keyboard(books_list)
        )

# Unitlarni boshqarish
@dp.message(F.text == "📝 Unitlarni boshqarish")
async def manage_units_menu(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return
    
    async_session = await get_session()
    async with async_session() as session:
        # Kitoblarni ko'rsatish
        stmt = select(Book)
        result = await session.execute(stmt)
        books_list = result.scalars().all()
        
        if not books_list:
            await message.answer("📭 Hozircha kitoblar mavjud emas.")
            return
        
        text = "📚 Avval kitobni tanlang:\n\n"
        for book in books_list:
            # Har bir kitobdagi unitlar soni
            unit_stmt = select(Unit).where(Unit.book_id == book.id)
            unit_result = await session.execute(unit_stmt)
            units_count = len(unit_result.scalars().all())
            
            text += f"📘 {book.name} ({units_count} unit)\n"
        
        await message.answer(
            text,
            reply_markup=get_books_manage_keyboard(books_list)
        )

# Savollarni boshqarish
@dp.message(F.text == "❓ Savollarni boshqarish")
async def manage_questions_menu(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return
    
    async_session = await get_session()
    async with async_session() as session:
        # Kitoblarni ko'rsatish
        stmt = select(Book)
        result = await session.execute(stmt)
        books_list = result.scalars().all()
        
        if not books_list:
            await message.answer("📭 Hozircha kitoblar mavjud emas.")
            return
        
        text = "📚 Avval kitobni tanlang:\n\n"
        for book in books_list:
            # Har bir kitobdagi savollar soni
            question_stmt = select(Question).join(Unit).where(Unit.book_id == book.id)
            question_result = await session.execute(question_stmt)
            questions_count = len(question_result.scalars().all())
            
            text += f"📘 {book.name} ({questions_count} savol)\n"
        
        await message.answer(
            text,
            reply_markup=get_books_manage_keyboard(books_list)
        )

# Kitobni boshqarish
@dp.callback_query(F.data.startswith("manage_book_"))
async def manage_book(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    book_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        book = await session.get(Book, book_id)
        
        # Unitlar soni
        unit_stmt = select(Unit).where(Unit.book_id == book_id)
        unit_result = await session.execute(unit_stmt)
        units_count = len(unit_result.scalars().all())
        
        # Savollar soni
        question_stmt = select(Question).join(Unit).where(Unit.book_id == book_id)
        question_result = await session.execute(question_stmt)
        questions_count = len(question_result.scalars().all())
        
        await callback.message.edit_text(
            f"📘 Kitob: {book.name}\n\n"
            f"📊 Ma'lumotlar:\n"
            f"• Unitlar soni: {units_count}\n"
            f"• Savollar soni: {questions_count}\n"
            f"• Yaratilgan: {book.created_at.strftime('%Y-%m-%d')}\n\n"
            f"Kerakli amalni tanlang:",
            reply_markup=get_book_manage_options(book_id)
        )
    
    await callback.answer()

# Kitob nomini o'zgartirish
@dp.callback_query(F.data.startswith("edit_book_name_"))
async def edit_book_name_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    book_id = int(callback.data.split("_")[-1])
    
    await state.update_data(book_id=book_id, action="edit_book_name")
    
    await callback.message.edit_text(
        f"✏️ Kitob nomini o'zgartirish:\n\n"
        f"Yangi nomni kiriting:"
    )
    await state.set_state(FormatStates.waiting_for_new_book_name)
    await callback.answer()

# Kitob nomini yangilash
@dp.message(FormatStates.waiting_for_new_book_name)
async def process_new_book_name_update(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    book_id = user_data.get('book_id')
    
    async_session = await get_session()
    async with async_session() as session:
        book = await session.get(Book, book_id)
        old_name = book.name
        book.name = message.text
        await session.commit()
        
        await message.answer(
            f"✅ Kitob nomi muvaffaqiyatli o'zgartirildi:\n"
            f"Eski nom: {old_name}\n"
            f"Yangi nom: {book.name}",
            reply_markup=get_book_manage_options(book_id)
        )
    
    await state.clear()

# Kitobni o'chirish so'rovi
@dp.callback_query(F.data.startswith("delete_book_"))
async def delete_book_confirmation(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    book_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        book = await session.get(Book, book_id)
        
        # Unitlar soni
        unit_stmt = select(Unit).where(Unit.book_id == book_id)
        unit_result = await session.execute(unit_stmt)
        units_count = len(unit_result.scalars().all())
        
        # Savollar soni
        question_stmt = select(Question).join(Unit).where(Unit.book_id == book_id)
        question_result = await session.execute(question_stmt)
        questions_count = len(question_result.scalars().all())
        
        warning_text = ""
        if units_count > 0 or questions_count > 0:
            warning_text = (
                f"⚠️ DIQQAT! Bu kitobni o'chirish bilan:\n"
                f"• {units_count} ta unit\n"
                f"• {questions_count} ta savol\n"
                f"HAMMA o'chib ketadi!\n\n"
            )
        
        await callback.message.edit_text(
            f"{warning_text}"
            f"🗑️ Kitobni o'chirish:\n"
            f"Kitob: {book.name}\n\n"
            f"Rostan ham o'chirmoqchimisiz?",
            reply_markup=get_confirmation_keyboard("delete_book", book_id)
        )
    
    await callback.answer()

# Kitobni o'chirishni tasdiqlash
@dp.callback_query(F.data.startswith("confirm_delete_book_"))
async def confirm_delete_book(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    book_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        book = await session.get(Book, book_id)
        book_name = book.name
        
        # Kitob bilan bog'liq barcha ma'lumotlarni o'chirish
        # 1. Unitlarni o'chirish (savollar ham avtomatik o'chadi)
        unit_stmt = select(Unit).where(Unit.book_id == book_id)
        unit_result = await session.execute(unit_stmt)
        units = unit_result.scalars().all()
        
        units_deleted = 0
        questions_deleted = 0
        
        for unit in units:
            # Unitdagi savollarni sanash
            question_stmt = select(Question).where(Question.unit_id == unit.id)
            question_result = await session.execute(question_stmt)
            questions = question_result.scalars().all()
            questions_deleted += len(questions)
            
            # Savollarni o'chirish
            await session.execute(
                Question.__table__.delete().where(Question.unit_id == unit.id)
            )
        
        # Unitlarni o'chirish
        await session.execute(
            Unit.__table__.delete().where(Unit.book_id == book_id)
        )
        units_deleted = len(units)
        
        # Test natijalarini o'chirish
        await session.execute(
            TestResult.__table__.delete().where(TestResult.book_id == book_id)
        )
        
        # Kitobni o'chirish
        await session.delete(book)
        await session.commit()
        
        await callback.message.edit_text(
            f"✅ Kitob muvaffaqiyatli o'chirildi:\n"
            f"Kitob: {book_name}\n"
            f"O'chirilgan unitlar: {units_deleted} ta\n"
            f"O'chirilgan savollar: {questions_deleted} ta\n\n"
            f"Barcha bog'liq ma'lumotlar o'chirildi."
        )
    
    await callback.answer()

# Unitlarni ko'rish
@dp.callback_query(F.data.startswith("view_units_"))
async def view_units_of_book(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    book_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        book = await session.get(Book, book_id)
        
        stmt = select(Unit).where(Unit.book_id == book_id)
        result = await session.execute(stmt)
        units_list = result.scalars().all()
        
        if not units_list:
            await callback.message.edit_text(
                f"📘 Kitob: {book.name}\n\n"
                f"❌ Bu kitobda unitlar mavjud emas."
            )
            return
        
        text = f"📘 Kitob: {book.name}\n\n"
        text += "📝 Mavjud unitlar:\n\n"
        
        for unit in units_list:
            # Unitdagi savollar soni
            question_stmt = select(Question).where(Question.unit_id == unit.id)
            question_result = await session.execute(question_stmt)
            questions_count = len(question_result.scalars().all())
            
            text += f"• {unit.name} ({questions_count} savol)\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_units_manage_keyboard(units_list, book_id)
        )
    
    await callback.answer()

# Unitni boshqarish
@dp.callback_query(F.data.startswith("manage_unit_"))
async def manage_unit(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    unit_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        
        # Savollar soni
        question_stmt = select(Question).where(Question.unit_id == unit_id)
        question_result = await session.execute(question_stmt)
        questions_count = len(question_result.scalars().all())
        
        await callback.message.edit_text(
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {unit.name}\n\n"
            f"📊 Ma'lumotlar:\n"
            f"• Savollar soni: {questions_count}\n"
            f"• Yaratilgan: {unit.created_at.strftime('%Y-%m-%d')}\n\n"
            f"Kerakli amalni tanlang:",
            reply_markup=get_unit_manage_options(unit_id)
        )
    
    await callback.answer()

# Unit nomini o'zgartirish
@dp.callback_query(F.data.startswith("edit_unit_name_"))
async def edit_unit_name_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    unit_id = int(callback.data.split("_")[-1])
    
    await state.update_data(unit_id=unit_id, action="edit_unit_name")
    
    await callback.message.edit_text(
        f"✏️ Unit nomini o'zgartirish:\n\n"
        f"Yangi nomni kiriting:"
    )
    await state.set_state(FormatStates.waiting_for_new_unit_name)
    await callback.answer()

# Unit nomini yangilash
@dp.message(FormatStates.waiting_for_new_unit_name)
async def process_new_unit_name_update(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    unit_id = user_data.get('unit_id')
    
    async_session = await get_session()
    async with async_session() as session:
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        old_name = unit.name
        unit.name = message.text
        await session.commit()
        
        await message.answer(
            f"✅ Unit nomi muvaffaqiyatli o'zgartirildi:\n"
            f"📘 Kitob: {book.name}\n"
            f"📝 Eski nom: {old_name}\n"
            f"📝 Yangi nom: {unit.name}",
            reply_markup=get_unit_manage_options(unit_id)
        )
    
    await state.clear()

# Unitni o'chirish so'rovi
@dp.callback_query(F.data.startswith("delete_unit_"))
async def delete_unit_confirmation(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    unit_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        
        # Savollar soni
        question_stmt = select(Question).where(Question.unit_id == unit_id)
        question_result = await session.execute(question_stmt)
        questions_count = len(question_result.scalars().all())
        
        warning_text = ""
        if questions_count > 0:
            warning_text = (
                f"⚠️ DIQQAT! Bu unitni o'chirish bilan:\n"
                f"• {questions_count} ta savol\n"
                f"HAMMA o'chib ketadi!\n\n"
            )
        
        await callback.message.edit_text(
            f"{warning_text}"
            f"🗑️ Unitni o'chirish:\n"
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {unit.name}\n\n"
            f"Rostan ham o'chirmoqchimisiz?",
            reply_markup=get_confirmation_keyboard("delete_unit", unit_id)
        )
    
    await callback.answer()

# Unitni o'chirishni tasdiqlash
@dp.callback_query(F.data.startswith("confirm_delete_unit_"))
async def confirm_delete_unit(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    unit_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        unit_name = unit.name
        
        # Unitdagi savollarni sanash
        question_stmt = select(Question).where(Question.unit_id == unit_id)
        question_result = await session.execute(question_stmt)
        questions = question_result.scalars().all()
        questions_deleted = len(questions)
        
        # Savollarni o'chirish
        await session.execute(
            Question.__table__.delete().where(Question.unit_id == unit_id)
        )
        
        # Test natijalarini o'chirish
        await session.execute(
            TestResult.__table__.delete().where(TestResult.unit_id == unit_id)
        )
        
        # Unitni o'chirish
        await session.delete(unit)
        await session.commit()
        
        await callback.message.edit_text(
            f"✅ Unit muvaffaqiyatli o'chirildi:\n"
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {unit_name}\n"
            f"O'chirilgan savollar: {questions_deleted} ta\n\n"
            f"Barcha bog'liq ma'lumotlar o'chirildi.",
            reply_markup=get_units_manage_keyboard([], book.id)
        )
    
    await callback.answer()

# Savollarni ko'rish
@dp.callback_query(F.data.startswith("view_questions_"))
async def view_questions_of_unit(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    unit_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        
        stmt = select(Question).where(Question.unit_id == unit_id)
        result = await session.execute(stmt)
        questions_list = result.scalars().all()
        
        if not questions_list:
            await callback.message.edit_text(
                f"📘 Kitob: {book.name}\n"
                f"📝 Unit: {unit.name}\n\n"
                f"❌ Bu unitda savollar mavjud emas."
            )
            return
        
        text = f"📘 Kitob: {book.name}\n"
        text += f"📝 Unit: {unit.name}\n\n"
        text += f"❓ Mavjud savollar ({len(questions_list)} ta):\n\n"
        
        for i, question in enumerate(questions_list, 1):
            try:
                import ast
                options = ast.literal_eval(question.options) if isinstance(question.options, str) else question.options
                options_text = ", ".join(options[:2]) + ("..." if len(options) > 2 else "")
            except:
                options_text = "Variantlar"
            
            text += f"{i}. {options_text}\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_questions_manage_keyboard(questions_list, unit_id)
        )
    
    await callback.answer()

# Savolni boshqarish
@dp.callback_query(F.data.startswith("manage_question_"))
async def manage_question(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    question_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        question = await session.get(Question, question_id)
        unit = await session.get(Unit, question.unit_id)
        book = await session.get(Book, unit.book_id)
        
        try:
            import ast
            options = ast.literal_eval(question.options) if isinstance(question.options, str) else question.options
            options_text = "\n".join([f"  {i+1}. {opt}" for i, opt in enumerate(options)])
        except:
            options = []
            options_text = "❌ Variantlarni o'qib bo'lmadi"
        
        await callback.message.edit_text(
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {unit.name}\n"
            f"🎵 Savol ID: {question.id}\n\n"
            f"📋 Variantlar:\n{options_text}\n\n"
            f"✅ To'g'ri javob: {question.correct_answer}\n"
            f"📅 Yaratilgan: {question.created_at.strftime('%Y-%m-%d')}\n\n"
            f"Kerakli amalni tanlang:",
            reply_markup=get_question_manage_options(question_id)
        )
    
    await callback.answer()

# Savol audiosini o'zgartirish
@dp.callback_query(F.data.startswith("edit_question_audio_"))
async def edit_question_audio_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    question_id = int(callback.data.split("_")[-1])
    
    await state.update_data(question_id=question_id, action="edit_question_audio")
    
    await callback.message.edit_text(
        f"🎵 Savol audiosini o'zgartirish:\n\n"
        f"Yangi audio faylini yuboring (MP3, OGG yoki voice):"
    )
    await state.set_state(FormatStates.waiting_for_new_question_audio)
    await callback.answer()

# Yangi audio qabul qilish
@dp.message(FormatStates.waiting_for_new_question_audio, F.audio | F.voice | F.document)
async def process_new_question_audio(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    question_id = user_data.get('question_id')
    
    # Audio fayl ma'lumotlarini saqlash
    if message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name or "audio.mp3"
    elif message.voice:
        file_id = message.voice.file_id
        file_name = "voice.ogg"
    elif message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "audio.mp3"
    
    async_session = await get_session()
    async with async_session() as session:
        question = await session.get(Question, question_id)
        unit = await session.get(Unit, question.unit_id)
        book = await session.get(Book, unit.book_id)
        
        question.audio_file = file_id
        await session.commit()
        
        await message.answer(
            f"✅ Savol audiosi muvaffaqiyatli yangilandi!\n\n"
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {unit.name}\n"
            f"🎵 Audio fayl: {file_name}\n"
            f"📊 Fayl ID: {file_id[:20]}...",
            reply_markup=get_question_manage_options(question_id)
        )
    
    await state.clear()

# Variantlarni o'zgartirish
@dp.callback_query(F.data.startswith("edit_question_options_"))
async def edit_question_options_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    question_id = int(callback.data.split("_")[-1])
    
    await state.update_data(question_id=question_id, action="edit_question_options")
    
    async_session = await get_session()
    async with async_session() as session:
        question = await session.get(Question, question_id)
        
        try:
            import ast
            old_options = ast.literal_eval(question.options) if isinstance(question.options, str) else question.options
            old_options_text = ", ".join(old_options)
        except:
            old_options_text = "Eski variantlar"
    
    await callback.message.edit_text(
        f"📋 Savol variantlarini o'zgartirish:\n\n"
        f"Eski variantlar: {old_options_text}\n\n"
        f"Yangi variantlarni kiriting (vergul bilan ajrating):\n"
        f"Masalan: A) Cat, B) Dog, C) Bird, D) Fish"
    )
    await state.set_state(FormatStates.waiting_for_new_question_options)
    await callback.answer()

# Yangi variantlarni qabul qilish
@dp.message(FormatStates.waiting_for_new_question_options)
async def process_new_question_options(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    question_id = user_data.get('question_id')
    
    options = message.text.split(',')
    options = [opt.strip() for opt in options if opt.strip()]
    
    if len(options) < 2:
        await message.answer(
            "❌ Kamida 2 ta variant kiriting!\n"
            "Variantlarni vergul bilan ajratib kiriting:"
        )
        return
    
    async_session = await get_session()
    async with async_session() as session:
        question = await session.get(Question, question_id)
        unit = await session.get(Unit, question.unit_id)
        book = await session.get(Book, unit.book_id)
        
        question.options = str(options)
        await session.commit()
        
        options_text = "\n".join([f"  {i+1}. {opt}" for i, opt in enumerate(options)])
        
        await message.answer(
            f"✅ Savol variantlari muvaffaqiyatli yangilandi!\n\n"
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {unit.name}\n"
            f"📋 Yangi variantlar:\n{options_text}\n\n"
            f"Endi to'g'ri javobni tanlang.",
            reply_markup=get_question_manage_options(question_id)
        )
    
    await state.clear()

# To'g'ri javobni o'zgartirish
@dp.callback_query(F.data.startswith("edit_question_answer_"))
async def edit_question_answer_start(callback: types.CallbackQuery, state: FSMContext):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    question_id = int(callback.data.split("_")[-1])
    
    await state.update_data(question_id=question_id, action="edit_question_answer")
    
    async_session = await get_session()
    async with async_session() as session:
        question = await session.get(Question, question_id)
        unit = await session.get(Unit, question.unit_id)
        book = await session.get(Book, unit.book_id)
        
        try:
            import ast
            options = ast.literal_eval(question.options) if isinstance(question.options, str) else question.options
            options_text = "\n".join([f"  {i+1}. {opt}" for i, opt in enumerate(options)])
        except:
            options = []
            options_text = "❌ Variantlarni o'qib bo'lmadi"
    
    await callback.message.edit_text(
        f"✅ To'g'ri javobni o'zgartirish:\n\n"
        f"📘 Kitob: {book.name}\n"
        f"📝 Unit: {unit.name}\n"
        f"🎵 Savol ID: {question.id}\n\n"
        f"📋 Variantlar:\n{options_text}\n\n"
        f"Eski to'g'ri javob: {question.correct_answer}\n\n"
        f"Yangi to'g'ri javob raqamini kiriting (1 dan {len(options)} gacha):"
    )
    await state.set_state(FormatStates.waiting_for_new_correct_answer)
    await callback.answer()

# Yangi to'g'ri javobni qabul qilish
@dp.message(FormatStates.waiting_for_new_correct_answer)
async def process_new_correct_answer(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    question_id = user_data.get('question_id')
    
    try:
        async_session = await get_session()
        async with async_session() as session:
            question = await session.get(Question, question_id)
            unit = await session.get(Unit, question.unit_id)
            book = await session.get(Book, unit.book_id)
            
            try:
                import ast
                options = ast.literal_eval(question.options) if isinstance(question.options, str) else question.options
            except:
                options = []
            
            if not options:
                await message.answer("❌ Variantlar topilmadi!")
                return
            
            correct_index = int(message.text) - 1
            
            if correct_index < 0 or correct_index >= len(options):
                await message.answer(
                    f"❌ Noto'g'ri raqam! 1 dan {len(options)} gacha raqam kiriting:"
                )
                return
            
            old_answer = question.correct_answer
            question.correct_answer = options[correct_index]
            await session.commit()
            
            await message.answer(
                f"✅ To'g'ri javob muvaffaqiyatli yangilandi!\n\n"
                f"📘 Kitob: {book.name}\n"
                f"📝 Unit: {unit.name}\n"
                f"🎵 Savol ID: {question.id}\n\n"
                f"📋 Eski to'g'ri javob: {old_answer}\n"
                f"✅ Yangi to'g'ri javob: {question.correct_answer}",
                reply_markup=get_question_manage_options(question_id)
            )
    
    except ValueError:
        await message.answer("❌ Iltimos, raqam kiriting!")
        return
    
    await state.clear()

# Savolni o'chirish so'rovi
@dp.callback_query(F.data.startswith("delete_question_"))
async def delete_question_confirmation(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    question_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        question = await session.get(Question, question_id)
        unit = await session.get(Unit, question.unit_id)
        book = await session.get(Book, unit.book_id)
        
        await callback.message.edit_text(
            f"🗑️ Savolni o'chirish:\n\n"
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {unit.name}\n"
            f"🎵 Savol ID: {question.id}\n\n"
            f"To'g'ri javob: {question.correct_answer}\n\n"
            f"Rostan ham o'chirmoqchimisiz?",
            reply_markup=get_confirmation_keyboard("delete_question", question_id)
        )
    
    await callback.answer()

# Savolni o'chirishni tasdiqlash
@dp.callback_query(F.data.startswith("confirm_delete_question_"))
async def confirm_delete_question(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    question_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        question = await session.get(Question, question_id)
        unit = await session.get(Unit, question.unit_id)
        book = await session.get(Book, unit.book_id)
        
        await session.delete(question)
        await session.commit()
        
        # Qolgan savollarni olish
        stmt = select(Question).where(Question.unit_id == unit.id)
        result = await session.execute(stmt)
        remaining_questions = len(result.scalars().all())
        
        await callback.message.edit_text(
            f"✅ Savol muvaffaqiyatli o'chirildi!\n\n"
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {unit.name}\n"
            f"📊 Unitda qolgan savollar: {remaining_questions} ta",
            reply_markup=get_questions_manage_keyboard([], unit.id)
        )
    
    await callback.answer()

# bot.py da orqaga tugmalari

# Formatlash menyusiga qaytish
@dp.callback_query(F.data == "back_to_format_menu")
async def back_to_format_menu(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    await callback.message.delete()
    await callback.message.answer(
        "🗑️ Test formatlash/o'chirish bo'limi:\n\n"
        "Kerakli amalni tanlang:",
        reply_markup=get_format_menu_keyboard()
    )
    await callback.answer()

# Kitoblarni boshqarishga qaytish
@dp.callback_query(F.data == "back_to_books_manage")
async def back_to_books_manage(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    async_session = await get_session()
    async with async_session() as session:
        stmt = select(Book)
        result = await session.execute(stmt)
        books_list = result.scalars().all()
        
        if not books_list:
            await callback.message.edit_text("📭 Hozircha kitoblar mavjud emas.")
            return
            
        await callback.message.edit_text(
            "📚 Mavjud kitoblar:\n"
            "O'zgartirmoqchi bo'lgan kitobni tanlang:",
            reply_markup=get_books_manage_keyboard(books_list)
        )
    
    await callback.answer()

# Kitob boshqarishga qaytish
@dp.callback_query(F.data.startswith("back_to_book_manage_"))
async def back_to_book_manage(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    book_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        book = await session.get(Book, book_id)
        
        # Unitlar soni
        unit_stmt = select(Unit).where(Unit.book_id == book_id)
        unit_result = await session.execute(unit_stmt)
        units_count = len(unit_result.scalars().all())
        
        # Savollar soni
        question_stmt = select(Question).join(Unit).where(Unit.book_id == book_id)
        question_result = await session.execute(question_stmt)
        questions_count = len(question_result.scalars().all())
        
        await callback.message.edit_text(
            f"📘 Kitob: {book.name}\n\n"
            f"📊 Ma'lumotlar:\n"
            f"• Unitlar soni: {units_count}\n"
            f"• Savollar soni: {questions_count}\n"
            f"• Yaratilgan: {book.created_at.strftime('%Y-%m-%d')}\n\n"
            f"Kerakli amalni tanlang:",
            reply_markup=get_book_manage_options(book_id)
        )
    
    await callback.answer()

# Unitlarni boshqarishga qaytish
@dp.callback_query(F.data.startswith("back_to_units_manage_"))
async def back_to_units_manage(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    unit_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        
        stmt = select(Unit).where(Unit.book_id == book.id)
        result = await session.execute(stmt)
        units_list = result.scalars().all()
        
        await callback.message.edit_text(
            f"📘 Kitob: {book.name}\n\n"
            f"📝 Mavjud unitlar:",
            reply_markup=get_units_manage_keyboard(units_list, book.id)
        )
    
    await callback.answer()

# Unit boshqarishga qaytish
@dp.callback_query(F.data.startswith("back_to_unit_manage_"))
async def back_to_unit_manage(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    unit_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        
        # Savollar soni
        question_stmt = select(Question).where(Question.unit_id == unit_id)
        question_result = await session.execute(question_stmt)
        questions_count = len(question_result.scalars().all())
        
        await callback.message.edit_text(
            f"📘 Kitob: {book.name}\n"
            f"📝 Unit: {unit.name}\n\n"
            f"📊 Ma'lumotlar:\n"
            f"• Savollar soni: {questions_count}\n"
            f"• Yaratilgan: {unit.created_at.strftime('%Y-%m-%d')}\n\n"
            f"Kerakli amalni tanlang:",
            reply_markup=get_unit_manage_options(unit_id)
        )
    
    await callback.answer()

# Savollarni boshqarishga qaytish
@dp.callback_query(F.data.startswith("back_to_questions_manage_"))
async def back_to_questions_manage(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    unit_id = int(callback.data.split("_")[-1])
    
    async_session = await get_session()
    async with async_session() as session:
        unit = await session.get(Unit, unit_id)
        book = await session.get(Book, unit.book_id)
        
        stmt = select(Question).where(Question.unit_id == unit_id)
        result = await session.execute(stmt)
        questions_list = result.scalars().all()
        
        if not questions_list:
            await callback.message.edit_text(
                f"📘 Kitob: {book.name}\n"
                f"📝 Unit: {unit.name}\n\n"
                f"❌ Bu unitda savollar mavjud emas."
            )
            return
        
        text = f"📘 Kitob: {book.name}\n"
        text += f"📝 Unit: {unit.name}\n\n"
        text += f"❓ Mavjud savollar ({len(questions_list)} ta):\n\n"
        
        for i, question in enumerate(questions_list, 1):
            try:
                import ast
                options = ast.literal_eval(question.options) if isinstance(question.options, str) else question.options
                options_text = ", ".join(options[:2]) + ("..." if len(options) > 2 else "")
            except:
                options_text = "Variantlar"
            
            text += f"{i}. {options_text}\n"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_questions_manage_keyboard(questions_list, unit_id)
        )
    
    await callback.answer()

# Bekor qilish tugmalari
@dp.callback_query(F.data.startswith("cancel_"))
async def cancel_action(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    data_parts = callback.data.split("_")
    action = data_parts[1]
    item_id = int(data_parts[2])
    
    if action == "delete_book":
        await back_to_book_manage(callback)
    elif action == "delete_unit":
        unit_id = item_id
        async_session = await get_session()
        async with async_session() as session:
            unit = await session.get(Unit, unit_id)
            book = await session.get(Book, unit.book_id)
            
            stmt = select(Unit).where(Unit.book_id == book.id)
            result = await session.execute(stmt)
            units_list = result.scalars().all()
            
            await callback.message.edit_text(
                f"📘 Kitob: {book.name}\n\n"
                f"📝 Mavjud unitlar:",
                reply_markup=get_units_manage_keyboard(units_list, book.id)
            )
    elif action == "delete_question":
        await back_to_questions_manage(callback)
    
    await callback.answer()

# Bekor qilish (formatlash holatida)
@dp.message(FormatStates.waiting_for_new_book_name)
@dp.message(FormatStates.waiting_for_new_unit_name)
@dp.message(FormatStates.waiting_for_new_question_audio)
@dp.message(FormatStates.waiting_for_new_question_options)
@dp.message(FormatStates.waiting_for_new_correct_answer)
async def cancel_format_operation(message: types.Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer(
            "❌ Amal bekor qilindi.",
            reply_markup=get_format_menu_keyboard()
        )
    else:
        # Agar bekorma qilish bo'lmasa, turli holatlarga mos ravishda ishlov berish
        await message.answer("Iltimos, kerakli ma'lumotni kiriting yoki '❌ Bekor qilish' tugmasini bosing.")                  

# bot.py - F-QADAM funksiyalari

# =================== F-QADAM: FOYDALANUVCHINI O'CHIRISH ===================

# Foydalanuvchini o'chirish menyusi
@dp.message(F.text == "❌ Foydalanuvchini o'chirish")
async def delete_user_menu(message: types.Message):
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return
    
    async_session = await get_session()
    async with async_session() as session:
        # Faqat oddiy foydalanuvchilarni olish (adminlarni emas)
        stmt = select(User).where(
            (User.is_admin == False) & 
            (User.is_active == True)  # Faqat faol foydalanuvchilar
        )
        result = await session.execute(stmt)
        users_list = result.scalars().all()
        
        if not users_list:
            await message.answer(
                "📭 Hozircha faol foydalanuvchilar yo'q.\n"
                "Barcha foydalanuvchilar ro'yxatini ko'rish uchun '👁️ Foydalanuvchilarni ko'rish' tugmasini bosing."
            )
            return
        
        text = "❌ Foydalanuvchini o'chirish:\n\n"
        text += "O'chirmoqchi bo'lgan foydalanuvchini tanlang:\n\n"
        
        for i, user in enumerate(users_list, 1):
            username = f"@{user.username}" if user.username else "Yo'q"
            text += f"{i}. {user.first_name} ({username})\n"
        
        await message.answer(
            text,
            reply_markup=get_users_delete_keyboard(users_list)
        )

# Foydalanuvchini o'chirishni boshlash
@dp.callback_query(F.data.startswith("delete_user_"))
async def delete_user_start(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[-1])
    
    # Adminni o'zini o'chirishni oldini olish
    if user_id == config.ADMIN_ID:
        await callback.answer("❌ Siz o'zingizni o'chira olmaysiz!", show_alert=True)
        return
    
    async_session = await get_session()
    async with async_session() as session:
        # Foydalanuvchini topish
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("❌ Foydalanuvchi topilmadi!", show_alert=True)
            return
        
        # Foydalanuvchi ma'lumotlarini olish
        username = f"@{user.username}" if user.username else "Yo'q"
        
        # Test natijalarini sanash
        stmt_results = select(TestResult).where(TestResult.user_id == user.id)
        result_results = await session.execute(stmt_results)
        test_results = result_results.scalars().all()
        
        await callback.message.edit_text(
            f"❌ Foydalanuvchini o'chirish:\n\n"
            f"👤 Foydalanuvchi:\n"
            f"• Ism: {user.first_name}\n"
            f"• Username: {username}\n"
            f"• ID: {user.user_id}\n"
            f"• Qo'shilgan: {user.created_at.strftime('%Y-%m-%d')}\n"
            f"• Test natijalari: {len(test_results)} ta\n\n"
            f"⚠️ DIQQAT! Foydalanuvchi o'chirilsa:\n"
            f"• Uning barcha test natijalari o'chib ketadi\n"
            f"• Botdan foydalana olmaydi\n"
            f"• Qayta ro'yxatdan o'tishi kerak\n\n"
            f"Rostan ham o'chirmoqchimisiz?",
            reply_markup=get_user_delete_confirmation_keyboard(user_id)
        )
    
    await callback.answer()

# Foydalanuvchini o'chirishni tasdiqlash
@dp.callback_query(F.data.startswith("confirm_delete_user_"))
async def confirm_delete_user(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    user_id = int(callback.data.split("_")[-1])
    
    # Adminni o'zini o'chirishni oldini olish
    if user_id == config.ADMIN_ID:
        await callback.answer("❌ Siz o'zingizni o'chira olmaysiz!", show_alert=True)
        return
    
    async_session = await get_session()
    async with async_session() as session:
        # Foydalanuvchini topish
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("❌ Foydalanuvchi topilmadi!", show_alert=True)
            return
        
        # Foydalanuvchi ma'lumotlarini saqlash (xabarda ko'rsatish uchun)
        user_name = user.first_name
        username = f"@{user.username}" if user.username else "Yo'q"
        
        # Test natijalarini sanash
        stmt_results = select(TestResult).where(TestResult.user_id == user.id)
        result_results = await session.execute(stmt_results)
        test_results = result_results.scalars().all()
        test_count = len(test_results)
        
        # Test natijalarini o'chirish
        if test_results:
            await session.execute(
                TestResult.__table__.delete().where(TestResult.user_id == user.id)
            )
        
        # Foydalanuvchini o'chirish
        await session.delete(user)
        await session.commit()
        
        # Foydalanuvchiga xabar yuborish (agar muvaffaqiyatli bo'lsa)
        try:
            await bot.send_message(
                user_id,
                "❌ Sizning hisobingiz admin tomonidan o'chirildi.\n\n"
                "Agar qayta foydalanmoqchi bo'lsangiz, yangi so'rov yuboring."
            )
        except Exception as e:
            logger.error(f"Foydalanuvchiga xabar yuborishda xatolik: {e}")
        
        await callback.message.edit_text(
            f"✅ Foydalanuvchi muvaffaqiyatli o'chirildi!\n\n"
            f"👤 O'chirilgan foydalanuvchi:\n"
            f"• Ism: {user_name}\n"
            f"• Username: {username}\n"
            f"• ID: {user_id}\n"
            f"• O'chirilgan test natijalari: {test_count} ta\n\n"
            f"Foydalanuvchi endi botdan foydalana olmaydi."
        )
    
    await callback.answer()

# Foydalanuvchini o'chirishni bekor qilish
@dp.callback_query(F.data == "cancel_delete_user")
async def cancel_delete_user(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    await callback.message.edit_text(
        "❌ Foydalanuvchini o'chirish bekor qilindi."
    )
    
    async_session = await get_session()# Foydalanuvchilar ro'yxatiga qaytish
    async with async_session() as session:
        stmt = select(User).where(User.user_id != config.ADMIN_ID)
        result = await session.execute(stmt)
        users_list = result.scalars().all()
        
        if users_list:
            await callback.message.answer(
                "❌ Foydalanuvchini o'chirish:\n\n"
                "O'chirmoqchi bo'lgan foydalanuvchini tanlang:",
                reply_markup=get_users_delete_keyboard(users_list)
            )
    
    await callback.answer()

# Foydalanuvchilarni boshqarish menyusiga qaytish
@dp.callback_query(F.data == "back_to_users_manage")
async def back_to_users_manage(callback: types.CallbackQuery):
    if callback.from_user.id != config.ADMIN_ID:
        await callback.answer("Sizga ruxsat yo'q!", show_alert=True)
        return
    
    await callback.message.delete()
    await callback.message.answer(
        "👥 Foydalanuvchilarni boshqarish:",
        reply_markup=get_users_management_keyboard()
    )
    await callback.answer()

# bot.py - G-QADAM funksiyalari

# =================== G-QADAM: USER MENYUSI ===================

# User menyusini yangilaymiz


## bot.py - TO'G'RILANGAN HANDLERLAR

# =================== USER: Mening natijalarim ===================

# bot.py - "Mening natijalarim" funksiyasini to'g'rilaymiz

# bot.py - To'g'rilangan user_my_results funksiyasi

# bot.py - TO'G'RILANGAN HANDLERLAR

# =================== USER: Mening natijalarim ===================

# bot.py - To'g'rilangan user_my_results funksiyasi

@dp.message(F.text == "📊 Mening natijalarim")
async def user_my_results(message: types.Message):
    logger.info(f"🔧 user_my_results called by Telegram ID: {message.from_user.id}")
    
    # Faqat oddiy foydalanuvchilar uchun
    if message.from_user.id == config.ADMIN_ID:
        await message.answer("Bu funksiya faqat oddiy foydalanuvchilar uchun.")
        return
    
    async_session = await get_session()
    async with async_session() as session:
        try:
            # 1. Foydalanuvchini topish
            stmt_user = select(User).where(User.user_id == message.from_user.id)
            result_user = await session.execute(stmt_user)
            user = result_user.scalar_one_or_none()
            
            if not user:
                await message.answer("❌ Foydalanuvchi topilmadi. Iltimos, /start ni bosing.")
                return
            
            if not user.is_active:
                await message.answer(
                    "❌ Sizga botdan foydalanishga ruxsat berilmagan.\n"
                    "Admin dan ruxsat so'rang."
                )
                return
            
            logger.info(f"✅ User found: DB ID={user.id}")
            
            # 2. Foydalanuvchining test natijalarini olish
            stmt_results = select(
                TestResult, Book, Unit
            ).join(
                Book, TestResult.book_id == Book.id
            ).join(
                Unit, TestResult.unit_id == Unit.id
            ).where(
                TestResult.user_id == user.id  # User jadvalidagi asosiy id
            ).order_by(
                TestResult.completed_at.desc()
            )
            
            result_results = await session.execute(stmt_results)
            test_results = result_results.all()
            
            logger.info(f"📊 Found {len(test_results)} test results for user ID {user.id}")
            
            if not test_results:
                # Database ni tekshirish
                all_results_stmt = select(TestResult)
                all_results = await session.execute(all_results_stmt)
                total_results = len(all_results.scalars().all())
                
                logger.info(f"📊 Total test results in database: {total_results}")
                
                await message.answer(
                    f"📭 Siz hali test ishlamagansiz.\n\n"
                    f"📊 Ma'lumot: Bazada jami {total_results} ta test natijasi mavjud.\n"
                    f"Avval '📚 Test yechish' tugmasi orqali test ishlang!"
                )
                return
            
            text = "📊 Mening test natijalarim:\n\n"
            
            for i, (test_result, book, unit) in enumerate(test_results, 1):
                if i > 10:  # Faqat oxirgi 10 tasini ko'rsatish
                    text += f"\n... va yana {len(test_results) - 10} ta test natijasi"
                    break
                
                percentage = (test_result.score / test_result.total_questions * 100) if test_result.total_questions > 0 else 0
                
                text += f"{i}. 📘 {book.name}\n"
                text += f"   📝 {unit.name}\n"
                text += f"   ✅ {test_result.score}/{test_result.total_questions}\n"
                text += f"   📈 {percentage:.1f}%\n"
                text += f"   🕐 {test_result.completed_at.strftime('%d.%m.%Y %H:%M')}\n"
                text += "   ─────────────\n"
            
            # Umumiy statistika
            total_tests = len(test_results)
            total_correct = sum([tr.score for tr, _, _ in test_results])
            total_questions = sum([tr.total_questions for tr, _, _ in test_results])
            overall_percentage = (total_correct / total_questions * 100) if total_questions > 0 else 0
            
            text += f"\n📈 Umumiy statistika:\n"
            text += f"• Jami testlar: {total_tests}\n"
            text += f"• To'g'ri javoblar: {total_correct}/{total_questions}\n"
            text += f"• O'rtacha natija: {overall_percentage:.1f}%\n"
            
            logger.info(f"📈 Stats: {total_tests} tests, {total_correct}/{total_questions} correct, {overall_percentage:.1f}% average")
            
            await message.answer(text)
            
        except Exception as e:
            logger.error(f"❌ Error in user_my_results: {e}", exc_info=True)
            await message.answer("❌ Xatolik yuz berdi. Iltimos, keyinroq urinib ko'ring.")

# =================== ADMIN: Umumiy natijalar ===================

@dp.message(F.text == "📊 Umumiy natijalar")
async def admin_general_results(message: types.Message):
    logger.info(f"admin_general_results called by user_id: {message.from_user.id}")
    
    # Faqat admin uchun
    if message.from_user.id != config.ADMIN_ID:
        await message.answer("Sizga ruxsat yo'q!")
        return
    
    async_session = await get_session()
    async with async_session() as session:
        try:
            # 1. Barcha foydalanuvchilar bo'yicha umumiy statistika
            stmt_total = select(
                User.first_name,
                User.username,
                func.count(TestResult.id).label('test_count'),
                func.sum(TestResult.score).label('total_score'),
                func.sum(TestResult.total_questions).label('total_questions')
            ).select_from(
                User
            ).outerjoin(
                TestResult, User.id == TestResult.user_id
            ).where(
                User.is_admin == False
            ).group_by(
                User.id, User.first_name, User.username
            ).order_by(
                func.coalesce(func.sum(TestResult.score), 0).desc()
            )
            
            result_total = await session.execute(stmt_total)
            users_stats = result_total.all()
            
            logger.info(f"Users stats found: {len(users_stats)}")
            
            # Foydalanuvchilarni tekshirish
            stmt_all_users = select(User).where(User.is_admin == False)
            result_all_users = await session.execute(stmt_all_users)
            all_users = result_all_users.scalars().all()
            logger.info(f"All users count: {len(all_users)}")
            
            # Test natijalarini tekshirish
            stmt_all_results = select(TestResult)
            result_all_results = await session.execute(stmt_all_results)
            all_test_results = result_all_results.scalars().all()
            logger.info(f"All test results count: {len(all_test_results)}")
            
            if not users_stats or all(stats.test_count == 0 or stats.test_count is None for stats in users_stats):
                if not all_test_results:
                    await message.answer("📭 Hozircha test natijalari mavjud emas.")
                else:
                    await message.answer("📭 Foydalanuvchilar bo'yicha test natijalari topilmadi.")
                return
            
            text = "📊 Barcha foydalanuvchilar bo'yicha statistika:\n\n"
            
            for stats in users_stats:
                if stats.test_count == 0 or stats.test_count is None:
                    continue
                    
                username = f"@{stats.username}" if stats.username else "Yo'q"
                percentage = (stats.total_score / stats.total_questions * 100) if stats.total_questions and stats.total_questions > 0 else 0
                
                text += f"👤 {stats.first_name} ({username})\n"
                text += f"   📊 Testlar: {stats.test_count}\n"
                text += f"   ✅ To'g'ri: {stats.total_score}/{stats.total_questions}\n"
                text += f"   📈 Foiz: {percentage:.1f}%\n"
                text += "   ─────────────\n"
            
            # 2. Eng yaxshi 5 ta natija
            stmt_best = select(
                User.first_name,
                Book.name.label('book_name'),
                Unit.name.label('unit_name'),
                TestResult.score,
                TestResult.total_questions,
                TestResult.completed_at
            ).select_from(
                TestResult
            ).join(
                User, TestResult.user_id == User.id
            ).join(
                Book, TestResult.book_id == Book.id
            ).join(
                Unit, TestResult.unit_id == Unit.id
            ).order_by(
                (TestResult.score / TestResult.total_questions).desc()
            ).limit(5)
            
            result_best = await session.execute(stmt_best)
            best_results = result_best.all()
            
            if best_results:
                text += "\n🏆 Eng yaxshi 5 ta natija:\n\n"
                
                for i, result in enumerate(best_results, 1):
                    percentage = (result.score / result.total_questions * 100) if result.total_questions and result.total_questions > 0 else 0
                    
                    text += f"{i}. {result.first_name}\n"
                    text += f"   📘 {result.book_name} - {result.unit_name}\n"
                    text += f"   ✅ {result.score}/{result.total_questions} ({percentage:.1f}%)\n"
                    text += f"   🕐 {result.completed_at.strftime('%d.%m.%Y')}\n"
                    text += "   ─────────────\n"
            
            # 3. Umumiy raqamlar
            stmt_overall = select(
                func.count(TestResult.id).label('total_tests'),
                func.sum(TestResult.score).label('total_correct'),
                func.sum(TestResult.total_questions).label('total_questions'),
                func.count(distinct(TestResult.user_id)).label('active_users')
            ).select_from(
                TestResult
            )
            
            result_overall = await session.execute(stmt_overall)
            overall = result_overall.first()
            
            if overall and overall.total_tests and overall.total_tests > 0:
                overall_percentage = (overall.total_correct / overall.total_questions * 100) if overall.total_questions and overall.total_questions > 0 else 0
                
                text += "\n📈 Umumiy raqamlar:\n"
                text += f"• Jami testlar: {overall.total_tests}\n"
                text += f"• Faol foydalanuvchilar: {overall.active_users}\n"
                text += f"• To'g'ri javoblar: {overall.total_correct}/{overall.total_questions}\n"
                text += f"• O'rtacha natija: {overall_percentage:.1f}%\n"
            else:
                text += "\n⚠️ Umumiy raqamlar topilmadi.\n"
            
            # Xabarni bo'laklarga ajratish (agar uzun bo'lsa)
            if len(text) > 4000:
                parts = []
                current_part = ""
                lines = text.split('\n')
                
                for line in lines:
                    if len(current_part) + len(line) + 1 < 4000:
                        current_part += line + '\n'
                    else:
                        parts.append(current_part)
                        current_part = line + '\n'
                
                if current_part:
                    parts.append(current_part)
                
                for i, part in enumerate(parts, 1):
                    if i == 1:
                        await message.answer(part)
                    else:
                        await message.answer(f"(davomi {i}/{len(parts)})\n{part}")
            else:
                await message.answer(text)
                
        except Exception as e:
            logger.error(f"Error in admin_general_results: {e}")
            await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")

# bot.py - Debug uchun funksiya

# bot.py - Yangilangan debug funksiya

@dp.message(F.text == "/testdebug")
async def test_debug(message: types.Message):
    
    async_session = await get_session()"""Test debug ma'lumotlari"""
    async with async_session() as session:
        # Foydalanuvchini topish
        stmt_user = select(User).where(User.user_id == message.from_user.id)
        result_user = await session.execute(stmt_user)
        user = result_user.scalar_one_or_none()
        
        if not user:
            text = "❌ Foydalanuvchi bazada topilmadi!"
        else:
            text = f"✅ Foydalanuvchi topildi:\n"
            text += f"• DB ID: {user.id}\n"
            text += f"• Telegram ID: {user.user_id}\n"
            text += f"• Ism: {user.first_name}\n"
            text += f"• Faol: {user.is_active}\n\n"
            
            # Test natijalari
            stmt_results = select(TestResult).where(TestResult.user_id == user.id)
            result_results = await session.execute(stmt_results)
            user_results = result_results.scalars().all()
            
            text += f"📊 Test natijalari: {len(user_results)} ta\n"
            
            for i, result in enumerate(user_results, 1):
                text += f"{i}. ID: {result.id}, Book: {result.book_id}, Unit: {result.unit_id}, Score: {result.score}/{result.total_questions}\n"
        
        # Umumiy statistika
        stmt_all_results = select(TestResult)
        all_results = await session.execute(stmt_all_results)
        total_results = len(all_results.scalars().all())
        
        stmt_all_users = select(User)
        all_users = await session.execute(stmt_all_users)
        total_users = len(all_users.scalars().all())
        
        text += f"\n📈 Umumiy statistika:\n"
        text += f"• Jami foydalanuvchilar: {total_users}\n"
        text += f"• Jami test natijalari: {total_results}\n"
        
        await message.answer(text)

async def on_startup(bot: Bot):
    # Webhook URL ni aniqlash
    webhook_url = os.getenv("RAILWAY_STATIC_URL", "") + "/webhook"
    
    if webhook_url:
        await bot.set_webhook(webhook_url)
        logger.info(f"Webhook set to: {webhook_url}")
    else:
        logger.info("Using polling mode")

async def on_shutdown(bot: Bot):
    if os.getenv("RAILWAY_STATIC_URL"):
        await bot.delete_webhook()
    logger.info("Bot shutdown")

# Asosiy funksiyani yangilash
async def main_webhook():
    # Webhook yoki polling ni aniqlash
    webhook_url = os.getenv("RAILWAY_STATIC_URL")
    
    if webhook_url:
        # Webhook mode
        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path="/webhook")
        setup_application(app, dp, bot=bot)
        
        port = int(os.getenv("PORT", 8000))
        web.run_app(app, host="0.0.0.0", port=port)
    else:
        # Polling mode
        await init_db()
        await dp.start_polling(bot)

# =================== MAIN FUNCTION ===================
# bot.py - ASOSIY FUNKSIYA (oxiri)

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass  # Loglarni chiqarmaslik

def run_health_server():
    port = int(os.getenv("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    logger.info(f"✅ Health server running on port {port}")
    server.serve_forever()

async def main_bot():
    try:
        # Database yaratish
        await init_db()
        logger.info("✅ Database initialized")
        
        # Botni ishga tushirish
        logger.info("🚀 Bot starting...")
        
        # Configni tekshirish
        config.validate()
        logger.info("✅ Config validated")
        
        # Polling ni boshlash
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
        
    except Exception as e:
        logger.error(f"❌ Bot failed to start: {e}")
        raise

if __name__ == "__main__":
    # Health serverni alohida threadda ishga tushirish
    health_thread = threading.Thread(target=run_health_server, daemon=True)
    health_thread.start()
    
    # Botni ishga tushirish
    try:
        asyncio.run(main_bot())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")