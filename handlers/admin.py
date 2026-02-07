# handlers/admin.py - TO'LIQ YANGI VERSIYA
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
import os
import json
import uuid
from database import async_session, Book, Unit, Question
from sqlalchemy import select, func
from keyboards import (
    get_admin_main_menu, 
    get_books_management_keyboard,
    get_units_management_keyboard,
    get_cancel_keyboard
)
from states import AdminStates
from database import User
from sqlalchemy import select

from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
import os
import json
import uuid
import asyncio

from database import async_session, Book, Unit, Question, User
from sqlalchemy import select, func
from keyboards import (
    get_admin_main_menu, 
    get_books_management_keyboard,
    get_units_management_keyboard,
    get_cancel_keyboard
)
from states import AdminStates
from database import UserResult  # <-- Shu qatorni qo'shing
from sqlalchemy import distinct

router = Router()

# ========== TEST TUZISH ==========

@router.message(F.text == "📝 Test tuzish")
async def create_test_start(message: types.Message):
    """Test tuzishni boshlash"""
    async with async_session() as session:
        result = await session.execute(select(Book))
        books = result.scalars().all()
        
        if not books:
            await message.answer(
                "📚 Hozircha kitoblar yo'q.\n"
                "Yangi kitob yaratish uchun uning nomini kiriting:",
                reply_markup=get_cancel_keyboard()
            )
            await message.answer.state.set_state(AdminStates.waiting_for_book_name)
        else:
            await message.answer(
                "📚 Mavjud kitoblardan birini tanlang yoki yangi kitob yarating:",
                reply_markup=get_books_management_keyboard(books)
            )

@router.callback_query(F.data == "create_new_book")
async def create_new_book_callback(callback: types.CallbackQuery, state: FSMContext):
    """Yangi kitob yaratish"""
    await callback.message.answer(
        "📖 Yangi kitob uchun nom kiriting:",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_book_name)

@router.message(AdminStates.waiting_for_book_name)
async def process_book_name(message: types.Message, state: FSMContext):
    """Kitob nomini qabul qilish"""
    book_name = message.text.strip()
    
    if book_name == "❌ Bekor qilish":
        await message.answer("❌ Amal bekor qilindi.", reply_markup=get_admin_main_menu())
        await state.clear()
        return
    
    async with async_session() as session:
        # Kitob mavjudligini tekshirish
        result = await session.execute(
            select(Book).where(func.lower(Book.name) == func.lower(book_name))
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            await message.answer(f"❌ '{book_name}' nomli kitob allaqachon mavjud.")
            return
        
        # Yangi kitob yaratish
        new_book = Book(name=book_name)
        session.add(new_book)
        await session.commit()
        
        await message.answer(
            f"✅ '{book_name}' kitobi yaratildi!\n\n"
            f"Endi bu kitobga unit qo'shishingiz mumkin.",
            reply_markup=get_admin_main_menu()
        )
        
        # Kitob ID sini state ga saqlash
        await state.update_data(book_id=new_book.id, book_name=book_name)
        
        # Unit yaratishga o'tish
        await message.answer(
            f"'{book_name}' kitobi uchun unit nomini kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AdminStates.waiting_for_unit_name)

@router.callback_query(F.data.startswith("manage_book_"))
async def manage_book_callback(callback: types.CallbackQuery, state: FSMContext):
    """Kitobni boshqarish (unitlarni ko'rish)"""
    book_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Kitobni olish
        result = await session.execute(
            select(Book).where(Book.id == book_id)
        )
        book = result.scalar_one()
        
        # Kitobdagi unitlarni olish
        units_result = await session.execute(
            select(Unit).where(Unit.book_id == book_id)
        )
        units = units_result.scalars().all()
        
        await callback.message.answer(
            f"📖 Kitob: {book.name}\n\n"
            f"📋 Mavjud unitlar: {len(units)} ta\n\n"
            f"Unit tanlang yoki yangi unit yarating:",
            reply_markup=get_units_management_keyboard(units, book_id)
        )
        
        # Kitob ID sini state ga saqlash
        await state.update_data(book_id=book_id, book_name=book.name)

@router.callback_query(F.data.startswith("add_unit_to_"))
async def add_unit_to_book(callback: types.CallbackQuery, state: FSMContext):
    """Kitobga yangi unit qo'shish"""
    book_id = int(callback.data.split("_")[3])
    
    async with async_session() as session:
        result = await session.execute(
            select(Book).where(Book.id == book_id)
        )
        book = result.scalar_one()
        
        await callback.message.answer(
            f"📝 '{book.name}' kitobi uchun yangi unit nomini kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        
        await state.update_data(book_id=book_id, book_name=book.name)
        await state.set_state(AdminStates.waiting_for_unit_name)

@router.message(AdminStates.waiting_for_unit_name)
async def process_unit_name(message: types.Message, state: FSMContext):
    """Unit nomini qabul qilish"""
    unit_name = message.text.strip()
    data = await state.get_data()
    book_id = data.get('book_id')
    
    if unit_name == "❌ Bekor qilish":
        await message.answer("❌ Amal bekor qilindi.", reply_markup=get_admin_main_menu())
        await state.clear()
        return
    
    async with async_session() as session:
        # Unit mavjudligini tekshirish
        result = await session.execute(
            select(Unit).where(
                (Unit.book_id == book_id) & 
                (func.lower(Unit.name) == func.lower(unit_name))
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            await message.answer(f"❌ '{unit_name}' nomli unit allaqachon mavjud.")
            return
        
        # Yangi unit yaratish
        new_unit = Unit(name=unit_name, book_id=book_id)
        session.add(new_unit)
        await session.commit()
        
        # Kitob nomini olish
        book_result = await session.execute(
            select(Book).where(Book.id == book_id)
        )
        book = book_result.scalar_one()
        
        await message.answer(
            f"✅ '{unit_name}' uniti '{book.name}' kitobiga qo'shildi!\n\n"
            f"Endi bu unitga savollar qo'shishingiz mumkin.",
            reply_markup=get_admin_main_menu()
        )
        
        # Unit ID sini state ga saqlash
        await state.update_data(unit_id=new_unit.id, unit_name=unit_name)
        
        # Savol qo'shishga o'tish
        await message.answer(
            f"🎵 '{unit_name}' unitiga savol qo'shish uchun audio fayl yuboring (MP3 formatida):",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AdminStates.waiting_for_audio)

@router.callback_query(F.data.startswith("manage_unit_"))
async def manage_unit_callback(callback: types.CallbackQuery, state: FSMContext):
    """Unitni boshqarish (savol qo'shish)"""
    unit_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Unitni olish
        result = await session.execute(
            select(Unit).where(Unit.id == unit_id)
        )
        unit = result.scalar_one()
        
        # Unitdagi savollarni sanash
        questions_result = await session.execute(
            select(func.count(Question.id)).where(Question.unit_id == unit_id)
        )
        questions_count = questions_result.scalar()
        
        await callback.message.answer(
            f"📄 Unit: {unit.name}\n"
            f"📊 Savollar soni: {questions_count}\n\n"
            f"Bu unitga savol qo'shish uchun audio fayl yuboring:"
        )
        
        # Unit ma'lumotlarini state ga saqlash
        await state.update_data(unit_id=unit_id, unit_name=unit.name)
        await state.set_state(AdminStates.waiting_for_audio)

@router.message(AdminStates.waiting_for_audio, F.audio)
async def receive_audio_for_question(message: types.Message, state: FSMContext):
    """Savol uchun audio faylni qabul qilish"""
    try:
        # Audio papkasini yaratish
        audio_dir = "data/audio"
        os.makedirs(audio_dir, exist_ok=True)
        
        # Fayl nomi
        if message.audio.file_name:
            file_ext = message.audio.file_name.split('.')[-1]
        else:
            file_ext = 'mp3'
        
        file_name = f"{uuid.uuid4()}.{file_ext}"
        file_path = os.path.join(audio_dir, file_name)
        
        # Audio faylni yuklash
        await message.bot.download(
            message.audio.file_id,
            destination=file_path
        )
        
        # Audio yo'lini state ga saqlash
        await state.update_data(audio_path=file_path)
        
        await message.answer(
            f"✅ Audio saqlandi: {file_name}\n\n"
            f"📝 Endi savol variantlarini kiriting (4 ta variant, vergul bilan ajrating):\n"
            f"Masalan: Apple, Banana, Orange, Mango",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AdminStates.waiting_for_options)
        
    except Exception as e:
        print(f"Audio saqlash xatosi: {e}")
        await message.answer("❌ Audio saqlashda xatolik. Qaytadan urinib ko'ring.")

@router.message(AdminStates.waiting_for_options)
async def receive_options_for_question(message: types.Message, state: FSMContext):
    """Savol variantlarini qabul qilish"""
    options_text = message.text.strip()
    
    if options_text == "❌ Bekor qilish":
        await message.answer("❌ Amal bekor qilindi.", reply_markup=get_admin_main_menu())
        await state.clear()
        return
    
    # Variantlarni ajratish
    options = [opt.strip() for opt in options_text.split(",")]
    
    if len(options) != 4:
        await message.answer(
            "❌ Iltimos, aynan 4 ta variant kiriting.\n"
            "Qaytadan kiriting (vergul bilan ajrating):"
        )
        return
    
    # Variantlarni state ga saqlash
    await state.update_data(options=options)
    
    # Variantlarni ko'rsatish
    options_list = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
    
    await message.answer(
        f"📋 Variantlar:\n{options_list}\n\n"
        f"✅ To'g'ri javobning raqamini kiriting (1, 2, 3 yoki 4):",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_correct_answer)

@router.message(AdminStates.waiting_for_correct_answer)
async def receive_correct_answer(message: types.Message, state: FSMContext):
    """To'g'ri javobni qabul qilish va savolni saqlash"""
    answer_text = message.text.strip()
    
    if answer_text == "❌ Bekor qilish":
        await message.answer("❌ Amal bekor qilindi.", reply_markup=get_admin_main_menu())
        await state.clear()
        return
    
    # To'g'ri javobni tekshirish
    if answer_text not in ['1', '2', '3', '4']:
        await message.answer("❌ Iltimos, 1, 2, 3 yoki 4 raqamlaridan birini kiriting.")
        return
    
    correct_index = int(answer_text) - 1  # 0-based index
    
    # Ma'lumotlarni state dan olish
    data = await state.get_data()
    unit_id = data.get('unit_id')
    audio_path = data.get('audio_path')
    options = data.get('options')
    unit_name = data.get('unit_name', 'Noma\'lum')
    
    # Savolni saqlash
    async with async_session() as session:
        try:
            new_question = Question(
                unit_id=unit_id,
                audio_path=audio_path,
                options=json.dumps(options, ensure_ascii=False),
                correct_answer=correct_index
            )
            session.add(new_question)
            await session.commit()
            
            await message.answer(
                f"✅ Savol muvaffaqiyatli qo'shildi!\n\n"
                f"📄 Unit: {unit_name}\n"
                f"🎵 Audio fayl: {os.path.basename(audio_path)}\n"
                f"✅ To'g'ri javob: {options[correct_index]}\n\n"
                f"Yana savol qo'shish uchun unitni tanlang.",
                reply_markup=get_admin_main_menu()
            )
            
        except Exception as e:
            print(f"Savol saqlash xatosi: {e}")
            await message.answer("❌ Savol saqlashda xatolik. Qaytadan urinib ko'ring.")
    
    await state.clear()

# ========== BEKOR QILISH ==========

@router.message(F.text == "❌ Bekor qilish")
async def cancel_action(message: types.Message, state: FSMContext):
    """Har qanday amalni bekor qilish"""
    await state.clear()
    await message.answer(
        "❌ Amal bekor qilindi.",
        reply_markup=get_admin_main_menu()
    )

@router.callback_query(F.data == "back_to_books")
async def back_to_books(callback: types.CallbackQuery):
    """Kitoblar menyusiga qaytish"""
    async with async_session() as session:
        result = await session.execute(select(Book))
        books = result.scalars().all()
        
        await callback.message.edit_text(
            "📚 Mavjud kitoblar:",
            reply_markup=get_books_management_keyboard(books)
        )

@router.callback_query(F.data == "cancel")
async def cancel_callback(callback: types.CallbackQuery, state: FSMContext):
    """Callback orqali bekor qilish"""
    await state.clear()
    await callback.message.edit_text("❌ Amal bekor qilindi.")
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )

# ========== QOLGAN ADMIN FUNKSIYALARI (O'ZGARMAYDI) ==========

# handlers/admin.py faylining OXIRIGA qo'shing:



# ========== XABAR YUBORISH FUNKSIYASI ==========

@router.message(F.text == "📢 Xabar yuborish")
async def start_broadcast(message: types.Message, state: FSMContext):
    """Xabar yuborishni boshlash"""
    await message.answer(
        "📢 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni yuboring:\n\n"
        "📝 Matn, 📷 Rasm, 🎵 Audio yoki 📹 Video yuborishingiz mumkin.\n\n"
        "❌ Bekor qilish uchun /cancel yoki '❌ Bekor qilish' tugmasini bosing.",
        reply_markup=get_cancel_keyboard()
    )
    await state.set_state(AdminStates.waiting_for_broadcast_message)

@router.message(AdminStates.waiting_for_broadcast_message, F.text == "❌ Bekor qilish")
async def cancel_broadcast(message: types.Message, state: FSMContext):
    """Xabar yuborishni bekor qilish"""
    await state.clear()
    await message.answer(
        "❌ Xabar yuborish bekor qilindi.",
        reply_markup=get_admin_main_menu()
    )

@router.message(AdminStates.waiting_for_broadcast_message, F.text)
async def receive_broadcast_text(message: types.Message, state: FSMContext):
    """Matnli xabarni qabul qilish va yuborish"""
    broadcast_text = message.text
    
    # Tasdiqlash keyboard
    confirm_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="confirm_broadcast"),
                types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
            ]
        ]
    )
    
    await state.update_data(broadcast_text=broadcast_text, broadcast_type="text")
    
    # Foydalanuvchilar sonini hisoblash
    async with async_session() as session:
        users_result = await session.execute(
            select(User).where(User.is_active == True)
        )
        active_users = users_result.scalars().all()
        users_count = len(active_users)
    
    await message.answer(
        f"📢 Xabar tasdiqlash:\n\n"
        f"📋 Xabar matni:\n{broadcast_text}\n\n"
        f"👥 Yuboriladigan foydalanuvchilar: {users_count} ta\n\n"
        f"Xabarni yuborishni tasdiqlaysizmi?",
        reply_markup=confirm_keyboard
    )

@router.message(AdminStates.waiting_for_broadcast_message, F.photo)
async def receive_broadcast_photo(message: types.Message, state: FSMContext):
    """Rasmli xabarni qabul qilish"""
    photo_id = message.photo[-1].file_id
    caption = message.caption or ""
    
    # Tasdiqlash keyboard
    confirm_keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="confirm_broadcast"),
                types.InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
            ]
        ]
    )
    
    await state.update_data(
        broadcast_photo=photo_id,
        broadcast_caption=caption,
        broadcast_type="photo"
    )
    
    # Foydalanuvchilar sonini hisoblash
    async with async_session() as session:
        users_result = await session.execute(
            select(User).where(User.is_active == True)
        )
        active_users = users_result.scalars().all()
        users_count = len(active_users)
    
    await message.answer(
        f"📷 Rasmli xabar tasdiqlash:\n\n"
        f"📋 Izoh: {caption if caption else '(Izohsiz)'}\n\n"
        f"👥 Yuboriladigan foydalanuvchilar: {users_count} ta\n\n"
        f"Xabarni yuborishni tasdiqlaysizmi?",
        reply_markup=confirm_keyboard
    )

@router.callback_query(F.data == "confirm_broadcast")
async def confirm_broadcast_callback(callback: types.CallbackQuery, state: FSMContext):
    """Xabarni yuborishni tasdiqlash"""
    data = await state.get_data()
    broadcast_type = data.get('broadcast_type')
    
    # Yuborish jarayonini boshlash
    await callback.message.edit_text("🔄 Xabar foydalanuvchilarga yuborilmoqda...")
    
    async with async_session() as session:
        users_result = await session.execute(
            select(User).where(User.is_active == True)
        )
        active_users = users_result.scalars().all()
    
    total_users = len(active_users)
    successful = 0
    failed = 0
    
    # Har bir foydalanuvchiga xabar yuborish
    for user in active_users:
        try:
            if broadcast_type == "text":
                text = data.get('broadcast_text')
                await callback.bot.send_message(
                    chat_id=user.user_id,
                    text=text
                )
                successful += 1
                
            elif broadcast_type == "photo":
                photo_id = data.get('broadcast_photo')
                caption = data.get('broadcast_caption', '')
                await callback.bot.send_photo(
                    chat_id=user.user_id,
                    photo=photo_id,
                    caption=caption
                )
                successful += 1
            
            # Kichik kutish (spamdan saqlash uchun)
            await asyncio.sleep(0.1)
            
        except Exception as e:
            print(f"Xabar yuborish xatosi (user_id: {user.user_id}): {e}")
            failed += 1
    
    # Natijani ko'rsatish
    result_text = (
        f"✅ Xabar yuborish yakunlandi!\n\n"
        f"📊 Natijalar:\n"
        f"👥 Jami foydalanuvchilar: {total_users} ta\n"
        f"✅ Muvaffaqiyatli: {successful} ta\n"
        f"❌ Xatolik bilan: {failed} ta\n\n"
        f"Agar ko'p xatolik bo'lsa, ba'zi foydalanuvchilar botni bloklagan bo'lishi mumkin."
    )
    
    await callback.message.edit_text(result_text)
    await state.clear()
    
    # Admin menyusiga qaytish
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )

@router.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast_callback(callback: types.CallbackQuery, state: FSMContext):
    """Xabar yuborishni bekor qilish (callback)"""
    await state.clear()
    await callback.message.edit_text("❌ Xabar yuborish bekor qilindi.")
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )

# handlers/admin.py fayliga qo'shing:

# ========== TESTNI O'CHIRISH FUNKSIYASI ==========

@router.message(F.text == "🗑️ Testni o'chirish")
async def start_delete_test(message: types.Message):
    """Testni o'chirishni boshlash"""
    async with async_session() as session:
        result = await session.execute(select(Book))
        books = result.scalars().all()
        
        if not books:
            await message.answer("❌ Hozircha o'chirish uchun testlar mavjud emas.")
            return
        
        # Kitoblarni o'chirish uchun keyboard
        builder = InlineKeyboardBuilder()
        for book in books:
            builder.add(InlineKeyboardButton(
                text=f"📖 {book.name}",
                callback_data=f"delete_book_{book.id}"
            ))
        
        builder.add(InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="back_to_main"
        ))
        
        builder.adjust(1)
        
        await message.answer(
            "🗑️ O'chirmoqchi bo'lgan test elementini tanlang:\n\n"
            "1. 📖 Kitob - butun kitob va uning ichidagi hamma narsa o'chadi\n"
            "2. 📄 Unit - faqat unit va uning savollari o'chadi\n"
            "3. ❓ Savol - faqat bitta savol o'chadi\n\n"
            "O'chirmoqchi bo'lgan kitobni tanlang:",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("delete_book_"))
async def confirm_delete_book(callback: types.CallbackQuery):
    """Kitobni o'chirishni tasdiqlash"""
    book_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Kitobni olish
        book_result = await session.execute(
            select(Book).where(Book.id == book_id)
        )
        book = book_result.scalar_one()
        
        # Kitobdagi unit va savollarni sanash
        units_result = await session.execute(
            select(func.count(Unit.id)).where(Unit.book_id == book_id)
        )
        units_count = units_result.scalar()
        
        questions_result = await session.execute(
            select(func.count(Question.id))
            .join(Unit, Question.unit_id == Unit.id)
            .where(Unit.book_id == book_id)
        )
        questions_count = questions_result.scalar()
        
        # Tasdiqlash keyboard
        confirm_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_delete_book_{book_id}"),
                    InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_delete")
                ],
                [
                    InlineKeyboardButton(text="📄 Unitlarni ko'rish", callback_data=f"view_units_{book_id}")
                ]
            ]
        )
        
        await callback.message.edit_text(
            f"⚠️ KITOBNI O'CHIRISH\n\n"
            f"📖 Kitob nomi: {book.name}\n"
            f"📄 Unitlar soni: {units_count} ta\n"
            f"❓ Savollar soni: {questions_count} ta\n\n"
            f"❌ Bu kitobni o'chirsangiz, uning ichidagi BARCHA unitlar va savollar ham o'chadi!\n\n"
            f"Rostdan ham o'chirmoqchimisiz?",
            reply_markup=confirm_keyboard
        )

@router.callback_query(F.data.startswith("view_units_"))
async def view_units_for_deletion(callback: types.CallbackQuery):
    """Kitobdagi unitlarni o'chirish uchun ko'rsatish"""
    book_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Kitobni olish
        book_result = await session.execute(
            select(Book).where(Book.id == book_id)
        )
        book = book_result.scalar_one()
        
        # Kitobdagi unitlarni olish
        units_result = await session.execute(
            select(Unit).where(Unit.book_id == book_id)
        )
        units = units_result.scalars().all()
        
        if not units:
            await callback.message.edit_text(
                f"❌ '{book.name}' kitobida unitlar mavjud emas."
            )
            return
        
        # Unitlarni o'chirish uchun keyboard
        builder = InlineKeyboardBuilder()
        for unit in units:
            # Unitdagi savollarni sanash
            questions_result = await session.execute(
                select(func.count(Question.id)).where(Question.unit_id == unit.id)
            )
            questions_count = questions_result.scalar()
            
            builder.add(InlineKeyboardButton(
                text=f"📄 {unit.name} ({questions_count} savol)",
                callback_data=f"delete_unit_{unit.id}"
            ))
        
        builder.add(InlineKeyboardButton(
            text="⬅️ Kitoblarga qaytish",
            callback_data="back_to_delete_menu"
        ))
        
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"🗑️ Kitob: {book.name}\n\n"
            f"O'chirmoqchi bo'lgan unitni tanlang:",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("delete_unit_"))
async def confirm_delete_unit(callback: types.CallbackQuery):
    """Unitni o'chirishni tasdiqlash"""
    unit_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Unitni olish
        unit_result = await session.execute(
            select(Unit).where(Unit.id == unit_id)
        )
        unit = unit_result.scalar_one()
        
        # Kitobni olish
        book_result = await session.execute(
            select(Book).where(Book.id == unit.book_id)
        )
        book = book_result.scalar_one()
        
        # Unitdagi savollarni sanash
        questions_result = await session.execute(
            select(func.count(Question.id)).where(Question.unit_id == unit_id)
        )
        questions_count = questions_result.scalar()
        
        # Tasdiqlash keyboard
        confirm_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_delete_unit_{unit_id}"),
                    InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_delete")
                ],
                [
                    InlineKeyboardButton(text="❓ Savollarni ko'rish", callback_data=f"view_questions_{unit_id}")
                ]
            ]
        )
        
        await callback.message.edit_text(
            f"⚠️ UNITNI O'CHIRISH\n\n"
            f"📖 Kitob: {book.name}\n"
            f"📄 Unit nomi: {unit.name}\n"
            f"❓ Savollar soni: {questions_count} ta\n\n"
            f"❌ Bu unitni o'chirsangiz, uning ichidagi BARCHA savollar ham o'chadi!\n\n"
            f"Rostdan ham o'chirmoqchimisiz?",
            reply_markup=confirm_keyboard
        )

@router.callback_query(F.data.startswith("view_questions_"))
async def view_questions_for_deletion(callback: types.CallbackQuery):
    """Unitdagi savollarni o'chirish uchun ko'rsatish"""
    unit_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Unitni olish
        unit_result = await session.execute(
            select(Unit).where(Unit.id == unit_id)
        )
        unit = unit_result.scalar_one()
        
        # Kitobni olish
        book_result = await session.execute(
            select(Book).where(Book.id == unit.book_id)
        )
        book = book_result.scalar_one()
        
        # Unitdagi savollarni olish
        questions_result = await session.execute(
            select(Question).where(Question.unit_id == unit_id)
        )
        questions = questions_result.scalars().all()
        
        if not questions:
            await callback.message.edit_text(
                f"❌ '{unit.name}' unitida savollar mavjud emas."
            )
            return
        
        # Savollarni o'chirish uchun keyboard
        builder = InlineKeyboardBuilder()
        for question in questions:
            # Audio fayl nomini olish
            audio_name = os.path.basename(question.audio_path) if question.audio_path else "Noma'lum"
            
            builder.add(InlineKeyboardButton(
                text=f"🎵 {audio_name[:20]}...",
                callback_data=f"delete_question_{question.id}"
            ))
        
        builder.add(InlineKeyboardButton(
            text="⬅️ Unitlarga qaytish",
            callback_data=f"view_units_{unit.book_id}"
        ))
        
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"🗑️ Kitob: {book.name}\n"
            f"Unit: {unit.name}\n\n"
            f"O'chirmoqchi bo'lgan savolni tanlang:",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("delete_question_"))
async def confirm_delete_question(callback: types.CallbackQuery):
    """Savolni o'chirishni tasdiqlash"""
    question_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Savolni olish
        question_result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = question_result.scalar_one()
        
        # Unitni olish
        unit_result = await session.execute(
            select(Unit).where(Unit.id == question.unit_id)
        )
        unit = unit_result.scalar_one()
        
        # Kitobni olish
        book_result = await session.execute(
            select(Book).where(Book.id == unit.book_id)
        )
        book = book_result.scalar_one()
        
        # Variantlarni olish
        try:
            options = json.loads(question.options)
            correct_answer = options[question.correct_answer]
        except:
            options = []
            correct_answer = "Noma'lum"
        
        # Tasdiqlash keyboard
        confirm_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_delete_question_{question_id}"),
                    InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_delete")
                ]
            ]
        )
        
        await callback.message.edit_text(
            f"⚠️ SAVOLNI O'CHIRISH\n\n"
            f"📖 Kitob: {book.name}\n"
            f"📄 Unit: {unit.name}\n"
            f"🎵 Audio fayl: {os.path.basename(question.audio_path)}\n"
            f"✅ To'g'ri javob: {correct_answer}\n\n"
            f"Rostdan ham o'chirmoqchimisiz?",
            reply_markup=confirm_keyboard
        )

@router.callback_query(F.data.startswith("confirm_delete_book_"))
async def execute_delete_book(callback: types.CallbackQuery):
    """Kitobni o'chirishni amalga oshirish"""
    book_id = int(callback.data.split("_")[3])
    
    async with async_session() as session:
        try:
            # Kitobni olish (o'chirishdan oldin)
            book_result = await session.execute(
                select(Book).where(Book.id == book_id)
            )
            book = book_result.scalar_one()
            book_name = book.name
            
            # Kitobni o'chirish (cascade delete ishlaydi)
            await session.delete(book)
            await session.commit()
            
            # Audio fayllarni ham o'chirish (agar kerak bo'lsa)
            # ...
            
            await callback.message.edit_text(
                f"✅ '{book_name}' kitobi va uning ichidagi hamma ma'lumotlar muvaffaqiyatli o'chirildi!"
            )
            
        except Exception as e:
            await session.rollback()
            await callback.message.edit_text(
                f"❌ Kitobni o'chirishda xatolik: {e}"
            )
    
    # Asosiy menyuga qaytish
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )

@router.callback_query(F.data.startswith("confirm_delete_unit_"))
async def execute_delete_unit(callback: types.CallbackQuery):
    """Unitni o'chirishni amalga oshirish"""
    unit_id = int(callback.data.split("_")[3])
    
    async with async_session() as session:
        try:
            # Unitni olish (o'chirishdan oldin)
            unit_result = await session.execute(
                select(Unit).where(Unit.id == unit_id)
            )
            unit = unit_result.scalar_one()
            unit_name = unit.name
            
            # Kitobni olish
            book_result = await session.execute(
                select(Book).where(Book.id == unit.book_id)
            )
            book = book_result.scalar_one()
            
            # Unitni o'chirish (cascade delete ishlaydi)
            await session.delete(unit)
            await session.commit()
            
            await callback.message.edit_text(
                f"✅ '{unit_name}' uniti va uning {book.name} kitobidagi barcha savollar muvaffaqiyatli o'chirildi!"
            )
            
        except Exception as e:
            await session.rollback()
            await callback.message.edit_text(
                f"❌ Unitni o'chirishda xatolik: {e}"
            )
    
    # Asosiy menyuga qaytish
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )

@router.callback_query(F.data.startswith("confirm_delete_question_"))
async def execute_delete_question(callback: types.CallbackQuery):
    """Savolni o'chirishni amalga oshirish"""
    question_id = int(callback.data.split("_")[3])
    
    async with async_session() as session:
        try:
            # Savolni olish (o'chirishdan oldin)
            question_result = await session.execute(
                select(Question).where(Question.id == question_id)
            )
            question = question_result.scalar_one()
            
            # Unitni olish
            unit_result = await session.execute(
                select(Unit).where(Unit.id == question.unit_id)
            )
            unit = unit_result.scalar_one()
            
            # Audio fayl yo'lini olish
            audio_path = question.audio_path
            
            # Savolni o'chirish
            await session.delete(question)
            await session.commit()
            
            # Audio faylni ham o'chirish (agar kerak bo'lsa)
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except:
                    pass
            
            await callback.message.edit_text(
                f"✅ Savol '{unit.name}' unitidan muvaffaqiyatli o'chirildi!"
            )
            
        except Exception as e:
            await session.rollback()
            await callback.message.edit_text(
                f"❌ Savolni o'chirishda xatolik: {e}"
            )
    
    # Asosiy menyuga qaytish
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )

@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: types.CallbackQuery):
    """O'chirishni bekor qilish"""
    await callback.message.edit_text("❌ O'chirish bekor qilindi.")
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )

@router.callback_query(F.data == "back_to_delete_menu")
async def back_to_delete_menu(callback: types.CallbackQuery):
    """O'chirish menyusiga qaytish"""
    await start_delete_test(callback.message)

@router.callback_query(F.data == "back_to_main")
async def back_to_main_from_delete(callback: types.CallbackQuery):
    """Asosiy menyuga qaytish"""
    await callback.message.edit_text("Asosiy menyu:")
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )

# handlers/admin.py fayliga qo'shing:

# ========== FOYDALANUVCHINI O'CHIRISH FUNKSIYASI ==========

@router.message(F.text == "❌ Foydalanuvchilarni o'chirish")
async def start_delete_users(message: types.Message):
    """Foydalanuvchilarni o'chirishni boshlash"""
    async with async_session() as session:
        # Faqat faol foydalanuvchilarni olish (adminlarni chiqarmaslik)
        result = await session.execute(
            select(User).where(
                (User.is_active == True) & 
                (User.is_admin == False)  # Adminlarni chiqarmaymiz
            ).order_by(User.created_at.desc())
        )
        users = result.scalars().all()
        
        if not users:
            await message.answer("❌ Hozircha o'chirish uchun foydalanuvchilar mavjud emas.")
            return
        
        # Foydalanuvchilarni o'chirish uchun keyboard
        builder = InlineKeyboardBuilder()
        for user in users:
            # Foydalanuvchi nomini tayyorlash
            user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            if not user_name:
                user_name = f"User_{user.user_id}"
            
            # Username mavjud bo'lsa
            username_display = f" @{user.username}" if user.username else ""
            
            builder.add(InlineKeyboardButton(
                text=f"👤 {user_name}{username_display}",
                callback_data=f"delete_user_{user.user_id}"
            ))
        
        builder.add(InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="back_to_main_menu"
        ))
        
        builder.adjust(1)
        
        await message.answer(
            "👥 FOYDALANUVCHILARNI O'CHIRISH\n\n"
            "O'chirmoqchi bo'lgan foydalanuvchini tanlang:\n\n"
            "⚠️ Eslatma: Foydalanuvchini o'chirganda:\n"
            "• ✅ Botdan bloklanadi (qayta kirish imkoni bo'lmaydi)\n"
            "• ✅ Barcha test natijalari o'chadi\n"
            "• ✅ Ma'lumotlar bazasidan to'liq o'chadi",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("delete_user_"))
async def confirm_delete_user(callback: types.CallbackQuery):
    """Foydalanuvchini o'chirishni tasdiqlash"""
    user_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Foydalanuvchini olish
        user_result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            await callback.message.edit_text("❌ Foydalanuvchi topilmadi.")
            return
        
        # Foydalanuvchi statistikasini hisoblash
        results_result = await session.execute(
            select(func.count(UserResult.id)).where(UserResult.user_id == user_id)
        )
        results_count = results_result.scalar()
        
        # O'rtacha ballni hisoblash
        avg_result = await session.execute(
            select(func.avg(UserResult.score)).where(UserResult.user_id == user_id)
        )
        avg_score = avg_result.scalar() or 0
        
        # Foydalanuvchi nomini tayyorlash
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        if not user_name:
            user_name = f"User_{user.user_id}"
        
        # Tasdiqlash keyboard
        confirm_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Ha, o'chirish", callback_data=f"confirm_delete_user_{user_id}"),
                    InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_user_delete")
                ],
                [
                    InlineKeyboardButton(text="📊 Natijalarni ko'rish", callback_data=f"view_user_results_{user_id}")
                ]
            ]
        )
        
        await callback.message.edit_text(
            f"⚠️ FOYDALANUVCHINI O'CHIRISH\n\n"
            f"👤 Foydalanuvchi: {user_name}\n"
            f"🆔 ID: {user.user_id}\n"
            f"📛 Username: @{user.username if user.username else 'yoq'}\n"
            f"📅 Ro'yxatdan: {user.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            f"📊 Statistika:\n"
            f"• 📈 Testlar soni: {results_count} ta\n"
            f"• 🏆 O'rtacha ball: {avg_score:.1f}%\n\n"
            f"❌ Bu foydalanuvchini o'chirsangiz:\n"
            f"• Botdan butunlay chiqariladi\n"
            f"• Barcha natijalari o'chadi\n"
            f"• Qayta kirish imkoni bo'lmaydi\n\n"
            f"Rostdan ham o'chirmoqchimisiz?",
            reply_markup=confirm_keyboard
        )

@router.callback_query(F.data.startswith("view_user_results_"))
async def view_user_results(callback: types.CallbackQuery):
    """Foydalanuvchi natijalarini ko'rish"""
    user_id = int(callback.data.split("_")[3])
    
    async with async_session() as session:
        # Foydalanuvchini olish
        user_result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user_result.scalar_one()
        
        # Foydalanuvchi natijalarini olish
        results_result = await session.execute(
            select(UserResult)
            .where(UserResult.user_id == user_id)
            .order_by(UserResult.completed_at.desc())
            .limit(10)
        )
        results = results_result.scalars().all()
        
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        if not user_name:
            user_name = f"User_{user.user_id}"
        
        if not results:
            results_text = "📭 Hozircha test natijalari mavjud emas."
        else:
            results_text = f"📊 {user_name}ning so'nggi 10 ta natijasi:\n\n"
            
            for i, res in enumerate(results, 1):
                # Kitob nomini olish
                book_result = await session.execute(
                    select(Book).where(Book.id == res.book_id)
                )
                book = book_result.scalar_one_or_none()
                book_name = book.name if book else "Noma'lum"
                
                # Unit nomini olish
                unit_result = await session.execute(
                    select(Unit).where(Unit.id == res.unit_id)
                )
                unit = unit_result.scalar_one_or_none()
                unit_name = unit.name if unit else "Noma'lum"
                
                results_text += (
                    f"{i}. {book_name} - {unit_name}\n"
                    f"   ✅ {res.correct_answers}/{res.total_questions}\n"
                    f"   📈 {res.score}%\n"
                    f"   📅 {res.completed_at.strftime('%d.%m.%Y %H:%M')}\n\n"
                )
        
        # Keyboard
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="⬅️ Orqaga", callback_data=f"delete_user_{user_id}")
                ]
            ]
        )
        
        await callback.message.edit_text(
            results_text,
            reply_markup=keyboard
        )

@router.callback_query(F.data.startswith("confirm_delete_user_"))
async def execute_delete_user(callback: types.CallbackQuery):
    """Foydalanuvchini o'chirishni amalga oshirish"""
    user_id = int(callback.data.split("_")[3])
    
    async with async_session() as session:
        try:
            # Foydalanuvchini olish (o'chirishdan oldin)
            user_result = await session.execute(
                select(User).where(User.user_id == user_id)
            )
            user = user_result.scalar_one()
            
            user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            if not user_name:
                user_name = f"User_{user.user_id}"
            
            # Foydalanuvchiga xabar yuborish (agar muvaffaqiyatli bo'lsa)
            try:
                await callback.bot.send_message(
                    user_id,
                    "❌ Sizning hisobingiz admin tomonidan o'chirildi.\n\n"
                    "Endi siz botdan foydalana olmaysiz.\n"
                    "Agar bu xato deb o'ylasangiz, admin bilan bog'laning."
                )
            except:
                pass  # Foydalanuvchi botni bloklagan bo'lishi mumkin
            
            # Foydalanuvchini o'chirish (cascade delete ishlaydi - natijalar ham o'chadi)
            await session.delete(user)
            await session.commit()
            
            await callback.message.edit_text(
                f"✅ '{user_name}' foydalanuvchisi muvaffaqiyatli o'chirildi!\n\n"
                f"📊 Barcha test natijalari ham o'chirildi."
            )
            
        except Exception as e:
            await session.rollback()
            await callback.message.edit_text(
                f"❌ Foydalanuvchini o'chirishda xatolik: {e}"
            )
    
    # Asosiy menyuga qaytish
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )

@router.callback_query(F.data == "cancel_user_delete")
async def cancel_user_delete(callback: types.CallbackQuery):
    """Foydalanuvchini o'chirishni bekor qilish"""
    await callback.message.edit_text("❌ Foydalanuvchini o'chirish bekor qilindi.")
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )

@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_from_users(callback: types.CallbackQuery):
    """Asosiy menyuga qaytish"""
    await callback.message.edit_text("Asosiy menyu:")
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )


# admin.py dagi mavjud users_list funksiyasini YANGILANG:

@router.message(F.text == "👥 Foydalanuvchilar ro'yxati")
async def users_list(message: types.Message):
    """Foydalanuvchilar ro'yxatini ko'rsatish (yaxshilangan)"""
    async with async_session() as session:
        # Barcha faol foydalanuvchilarni olish
        result = await session.execute(
            select(User).where(User.is_active == True).order_by(User.created_at.desc())
        )
        users = result.scalars().all()
        
        if not users:
            await message.answer("❌ Hozircha faol foydalanuvchilar yo'q.")
            return
        
        # Statistikani hisoblash
        total_users = len(users)
        
        # Har bir foydalanuvchi uchun testlar sonini hisoblash
        users_with_stats = []
        for user in users:
            results_result = await session.execute(
                select(func.count(UserResult.id)).where(UserResult.user_id == user.user_id)
            )
            tests_count = results_result.scalar()
            
            avg_result = await session.execute(
                select(func.avg(UserResult.score)).where(UserResult.user_id == user.user_id)
            )
            avg_score = avg_result.scalar() or 0
            
            users_with_stats.append({
                'user': user,
                'tests_count': tests_count,
                'avg_score': avg_score
            })
        
        # Ro'yxatni ko'rsatish (inline keyboard bilan)
        builder = InlineKeyboardBuilder()
        
        for stats in users_with_stats:
            user = stats['user']
            user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            if not user_name:
                user_name = f"User_{user.user_id}"
            
            username_display = f" @{user.username}" if user.username else ""
            
            builder.add(InlineKeyboardButton(
                text=f"👤 {user_name}{username_display}",
                callback_data=f"view_user_details_{user.user_id}"
            ))
        
        builder.add(InlineKeyboardButton(
            text="🗑️ Foydalanuvchini o'chirish",
            callback_data="go_to_delete_users"
        ))
        
        builder.adjust(1)
        
        await message.answer(
            f"👥 FOYDALANUVCHILAR RO'YXATI\n\n"
            f"📊 Jami faol foydalanuvchilar: {total_users} ta\n\n"
            f"Har bir foydalanuvchi haqida batafsil ma'lumot olish uchun tanlang:",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("view_user_details_"))
async def view_user_details(callback: types.CallbackQuery):
    """Foydalanuvchi haqida batafsil ma'lumot"""
    user_id = int(callback.data.split("_")[3])
    
    async with async_session() as session:
        # Foydalanuvchini olish
        user_result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        user = user_result.scalar_one()
        
        # Foydalanuvchi statistikasini hisoblash
        results_result = await session.execute(
            select(UserResult).where(UserResult.user_id == user_id)
        )
        all_results = results_result.scalars().all()
        
        total_tests = len(all_results)
        total_correct = sum([r.correct_answers for r in all_results])
        total_questions = sum([r.total_questions for r in all_results])
        avg_score = sum([r.score for r in all_results]) / total_tests if total_tests > 0 else 0
        
        # Eng yaxshi natijani topish
        best_result = max(all_results, key=lambda x: x.score) if all_results else None
        
        # Foydalanuvchi nomini tayyorlash
        user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        if not user_name:
            user_name = f"User_{user.user_id}"
        
        # Ma'lumotlar matni
        details_text = (
            f"👤 FOYDALANUVCHI MA'LUMOTLARI\n\n"
            f"📛 Ism: {user_name}\n"
            f"🆔 ID: {user.user_id}\n"
            f"📧 Username: @{user.username if user.username else 'yoq'}\n"
            f"📅 Ro'yxatdan: {user.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"✅ Status: {'Admin' if user.is_admin else 'Faol foydalanuvchi'}\n\n"
            f"📊 STATISTIKA:\n"
            f"• 📈 Testlar soni: {total_tests} ta\n"
            f"• ✅ To'g'ri javoblar: {total_correct}/{total_questions}\n"
            f"• 🏆 O'rtacha ball: {avg_score:.1f}%\n"
        )
        
        if best_result:
            # Eng yaxshi natijani ko'rsatish
            book_result = await session.execute(
                select(Book).where(Book.id == best_result.book_id)
            )
            book = book_result.scalar_one()
            
            unit_result = await session.execute(
                select(Unit).where(Unit.id == best_result.unit_id)
            )
            unit = unit_result.scalar_one()
            
            details_text += (
                f"• 🥇 Eng yaxshi natija: {best_result.score}%\n"
                f"  📖 ({book.name} - {unit.name})\n"
            )
        
        # Keyboard
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"delete_user_{user_id}"),
                    InlineKeyboardButton(text="📊 Natijalar", callback_data=f"view_user_results_{user_id}")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Ro'yxatga qaytish", callback_data="back_to_users_list")
                ]
            ]
        )
        
        await callback.message.edit_text(
            details_text,
            reply_markup=keyboard
        )

@router.callback_query(F.data == "go_to_delete_users")
async def go_to_delete_users(callback: types.CallbackQuery):
    """Foydalanuvchini o'chirish sahifasiga o'tish"""
    await start_delete_users(callback.message)

@router.callback_query(F.data == "back_to_users_list")
async def back_to_users_list(callback: types.CallbackQuery):
    """Foydalanuvchilar ro'yxatiga qaytish"""
    await users_list(callback.message)    

# handlers/admin.py fayliga qo'shing:

# ========== TEST FORMATLASH FUNKSIYASI ==========

@router.message(F.text == "🔄 Test formatlash")
async def start_edit_test(message: types.Message):
    """Test formatlashni boshlash"""
    async with async_session() as session:
        result = await session.execute(select(Book))
        books = result.scalars().all()
        
        if not books:
            await message.answer("❌ Hozircha formatlash uchun testlar mavjud emas.")
            return
        
        # Kitoblarni formatlash uchun keyboard
        builder = InlineKeyboardBuilder()
        for book in books:
            builder.add(InlineKeyboardButton(
                text=f"📖 {book.name}",
                callback_data=f"edit_book_{book.id}"
            ))
        
        builder.add(InlineKeyboardButton(
            text="⬅️ Orqaga",
            callback_data="back_to_main_from_edit"
        ))
        
        builder.adjust(1)
        
        await message.answer(
            "🔄 TEST FORMATLASH\n\n"
            "O'zgartirmoqchi bo'lgan test elementini tanlang:\n\n"
            "1. 📖 Kitob nomini o'zgartirish\n"
            "2. 📄 Unit nomini o'zgartirish\n"
            "3. ❓ Savol variantlarini o'zgartirish\n\n"
            "O'zgartirmoqchi bo'lgan kitobni tanlang:",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("edit_book_"))
async def edit_book_options(callback: types.CallbackQuery):
    """Kitobni o'zgartirish variantlari"""
    book_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Kitobni olish
        book_result = await session.execute(
            select(Book).where(Book.id == book_id)
        )
        book = book_result.scalar_one()
        
        # Kitobdagi unitlarni olish
        units_result = await session.execute(
            select(Unit).where(Unit.book_id == book_id)
        )
        units = units_result.scalars().all()
        
        # Keyboard
        builder = InlineKeyboardBuilder()
        
        # Kitob nomini o'zgartirish
        builder.add(InlineKeyboardButton(
            text=f"✏️ Kitob nomini o'zgartirish: {book.name}",
            callback_data=f"rename_book_{book_id}"
        ))
        
        # Unitlarni o'zgartirish
        for unit in units:
            builder.add(InlineKeyboardButton(
                text=f"📄 {unit.name}",
                callback_data=f"edit_unit_{unit.id}"
            ))
        
        builder.add(InlineKeyboardButton(
            text="➕ Yangi unit qo'shish",
            callback_data=f"add_unit_to_book_{book_id}"
        ))
        
        builder.add(InlineKeyboardButton(
            text="⬅️ Kitoblarga qaytish",
            callback_data="back_to_edit_menu"
        ))
        
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"🔄 Kitob: {book.name}\n\n"
            f"O'zgartirmoqchi bo'lgan elementni tanlang:",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("rename_book_"))
async def rename_book_start(callback: types.CallbackQuery, state: FSMContext):
    """Kitob nomini o'zgartirishni boshlash"""
    book_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Kitobni olish
        book_result = await session.execute(
            select(Book).where(Book.id == book_id)
        )
        book = book_result.scalar_one()
        
        # Eski nomni state ga saqlash
        await state.update_data(
            book_id=book_id,
            old_book_name=book.name
        )
        
        await callback.message.answer(
            f"✏️ Kitob nomini o'zgartirish\n\n"
            f"Eski nom: {book.name}\n\n"
            f"Yangi nomni kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AdminStates.editing_book_name)

@router.message(AdminStates.editing_book_name)
async def process_book_rename(message: types.Message, state: FSMContext):
    """Kitob yangi nomini qabul qilish"""
    new_name = message.text.strip()
    data = await state.get_data()
    book_id = data.get('book_id')
    old_name = data.get('old_book_name')
    
    if new_name == "❌ Bekor qilish":
        await message.answer("❌ O'zgartirish bekor qilindi.", reply_markup=get_admin_main_menu())
        await state.clear()
        return
    
    if not new_name or new_name == old_name:
        await message.answer("❌ Yangi nom eski nom bilan bir xil yoki bo'sh.")
        return
    
    async with async_session() as session:
        # Yangi nomning boshqa kitobda mavjudligini tekshirish
        result = await session.execute(
            select(Book).where(
                (func.lower(Book.name) == func.lower(new_name)) &
                (Book.id != book_id)
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            await message.answer(f"❌ '{new_name}' nomli kitob allaqachon mavjud.")
            return
        
        # Kitob nomini yangilash
        book_result = await session.execute(
            select(Book).where(Book.id == book_id)
        )
        book = book_result.scalar_one()
        book.name = new_name
        await session.commit()
        
        await message.answer(
            f"✅ Kitob nomi muvaffaqiyatli o'zgartirildi!\n\n"
            f"📖 Eski nom: {old_name}\n"
            f"📖 Yangi nom: {new_name}",
            reply_markup=get_admin_main_menu()
        )
    
    await state.clear()

@router.callback_query(F.data.startswith("edit_unit_"))
async def edit_unit_options(callback: types.CallbackQuery):
    """Unitni o'zgartirish variantlari"""
    unit_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Unitni olish
        unit_result = await session.execute(
            select(Unit).where(Unit.id == unit_id)
        )
        unit = unit_result.scalar_one()
        
        # Kitobni olish
        book_result = await session.execute(
            select(Book).where(Book.id == unit.book_id)
        )
        book = book_result.scalar_one()
        
        # Unitdagi savollarni olish
        questions_result = await session.execute(
            select(Question).where(Question.unit_id == unit_id)
        )
        questions = questions_result.scalars().all()
        
        # Keyboard
        builder = InlineKeyboardBuilder()
        
        # Unit nomini o'zgartirish
        builder.add(InlineKeyboardButton(
            text=f"✏️ Unit nomini o'zgartirish: {unit.name}",
            callback_data=f"rename_unit_{unit_id}"
        ))
        
        # Savollarni o'zgartirish
        for question in questions:
            # Audio fayl nomini olish
            audio_name = os.path.basename(question.audio_path) if question.audio_path else "Noma'lum"
            
            builder.add(InlineKeyboardButton(
                text=f"🎵 {audio_name[:20]}...",
                callback_data=f"edit_question_{question.id}"
            ))
        
        builder.add(InlineKeyboardButton(
            text="➕ Yangi savol qo'shish",
            callback_data=f"add_question_to_unit_{unit_id}"
        ))
        
        builder.add(InlineKeyboardButton(
            text="⬅️ Kitobga qaytish",
            callback_data=f"edit_book_{book.id}"
        ))
        
        builder.adjust(1)
        
        await callback.message.edit_text(
            f"🔄 Kitob: {book.name}\n"
            f"Unit: {unit.name}\n"
            f"Savollar soni: {len(questions)} ta\n\n"
            f"O'zgartirmoqchi bo'lgan elementni tanlang:",
            reply_markup=builder.as_markup()
        )

@router.callback_query(F.data.startswith("rename_unit_"))
async def rename_unit_start(callback: types.CallbackQuery, state: FSMContext):
    """Unit nomini o'zgartirishni boshlash"""
    unit_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Unitni olish
        unit_result = await session.execute(
            select(Unit).where(Unit.id == unit_id)
        )
        unit = unit_result.scalar_one()
        
        # Kitobni olish
        book_result = await session.execute(
            select(Book).where(Book.id == unit.book_id)
        )
        book = book_result.scalar_one()
        
        # Eski nomni state ga saqlash
        await state.update_data(
            unit_id=unit_id,
            old_unit_name=unit.name,
            book_id=unit.book_id
        )
        
        await callback.message.answer(
            f"✏️ Unit nomini o'zgartirish\n\n"
            f"📖 Kitob: {book.name}\n"
            f"📄 Eski nom: {unit.name}\n\n"
            f"Yangi nomni kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AdminStates.editing_unit_name)

@router.message(AdminStates.editing_unit_name)
async def process_unit_rename(message: types.Message, state: FSMContext):
    """Unit yangi nomini qabul qilish"""
    new_name = message.text.strip()
    data = await state.get_data()
    unit_id = data.get('unit_id')
    old_name = data.get('old_unit_name')
    book_id = data.get('book_id')
    
    if new_name == "❌ Bekor qilish":
        await message.answer("❌ O'zgartirish bekor qilindi.", reply_markup=get_admin_main_menu())
        await state.clear()
        return
    
    if not new_name or new_name == old_name:
        await message.answer("❌ Yangi nom eski nom bilan bir xil yoki bo'sh.")
        return
    
    async with async_session() as session:
        # Yangi nomning boshqa unitda mavjudligini tekshirish
        result = await session.execute(
            select(Unit).where(
                (func.lower(Unit.name) == func.lower(new_name)) &
                (Unit.book_id == book_id) &
                (Unit.id != unit_id)
            )
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            await message.answer(f"❌ '{new_name}' nomli unit allaqachon mavjud.")
            return
        
        # Unit nomini yangilash
        unit_result = await session.execute(
            select(Unit).where(Unit.id == unit_id)
        )
        unit = unit_result.scalar_one()
        unit.name = new_name
        await session.commit()
        
        # Kitob nomini olish
        book_result = await session.execute(
            select(Book).where(Book.id == book_id)
        )
        book = book_result.scalar_one()
        
        await message.answer(
            f"✅ Unit nomi muvaffaqiyatli o'zgartirildi!\n\n"
            f"📖 Kitob: {book.name}\n"
            f"📄 Eski nom: {old_name}\n"
            f"📄 Yangi nom: {new_name}",
            reply_markup=get_admin_main_menu()
        )
    
    await state.clear()

@router.callback_query(F.data.startswith("edit_question_"))
async def edit_question_start(callback: types.CallbackQuery):
    """Savolni o'zgartirish variantlari"""
    question_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Savolni olish
        question_result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = question_result.scalar_one()
        
        # Unitni olish
        unit_result = await session.execute(
            select(Unit).where(Unit.id == question.unit_id)
        )
        unit = unit_result.scalar_one()
        
        # Kitobni olish
        book_result = await session.execute(
            select(Book).where(Book.id == unit.book_id)
        )
        book = book_result.scalar_one()
        
        # Variantlarni olish
        try:
            options = json.loads(question.options)
        except:
            options = ["Variant 1", "Variant 2", "Variant 3", "Variant 4"]
        
        correct_answer = options[question.correct_answer]
        audio_name = os.path.basename(question.audio_path) if question.audio_path else "Noma'lum"
        
        # Keyboard
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(text="📝 Variantlarni o'zgartirish", callback_data=f"edit_options_{question_id}")
                ],
                [
                    InlineKeyboardButton(text="✅ To'g'ri javobni o'zgartirish", callback_data=f"edit_correct_{question_id}")
                ],
                [
                    InlineKeyboardButton(text="🎵 Audio faylni almashtirish", callback_data=f"replace_audio_{question_id}")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Unitga qaytish", callback_data=f"edit_unit_{unit.id}")
                ]
            ]
        )
        
        # Variantlarni ko'rsatish
        options_text = "\n".join([f"{i+1}. {opt}" + (" ✅" if i == question.correct_answer else "") 
                                 for i, opt in enumerate(options)])
        
        await callback.message.edit_text(
            f"🔄 SAVOLNI O'ZGARTIRISH\n\n"
            f"📖 Kitob: {book.name}\n"
            f"📄 Unit: {unit.name}\n"
            f"🎵 Audio fayl: {audio_name}\n\n"
            f"📋 Variantlar:\n{options_text}\n\n"
            f"Nimani o'zgartirmoqchisiz?",
            reply_markup=keyboard
        )

@router.callback_query(F.data.startswith("edit_options_"))
async def edit_question_options_start(callback: types.CallbackQuery, state: FSMContext):
    """Savol variantlarini o'zgartirishni boshlash"""
    question_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Savolni olish
        question_result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = question_result.scalar_one()
        
        # Eski variantlarni olish
        try:
            old_options = json.loads(question.options)
            old_options_text = ", ".join(old_options)
        except:
            old_options = ["Variant 1", "Variant 2", "Variant 3", "Variant 4"]
            old_options_text = ", ".join(old_options)
        
        # Question ID sini state ga saqlash
        await state.update_data(
            question_id=question_id,
            old_options=old_options
        )
        
        await callback.message.answer(
            f"📝 Savol variantlarini o'zgartirish\n\n"
            f"Eski variantlar: {old_options_text}\n\n"
            f"Yangi variantlarni kiriting (4 ta variant, vergul bilan ajrating):\n"
            f"Masalan: Apple, Banana, Orange, Mango",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AdminStates.editing_question)

@router.message(AdminStates.editing_question)
async def process_question_edit(message: types.Message, state: FSMContext):
    """Savol yangi variantlarini qabul qilish"""
    options_text = message.text.strip()
    data = await state.get_data()
    question_id = data.get('question_id')
    old_options = data.get('old_options', [])
    
    if options_text == "❌ Bekor qilish":
        await message.answer("❌ O'zgartirish bekor qilindi.", reply_markup=get_admin_main_menu())
        await state.clear()
        return
    
    # Variantlarni ajratish
    options = [opt.strip() for opt in options_text.split(",")]
    
    if len(options) != 4:
        await message.answer(
            "❌ Iltimos, aynan 4 ta variant kiriting.\n"
            "Qaytadan kiriting (vergul bilan ajrating):"
        )
        return
    
    async with async_session() as session:
        # Savolni yangilash
        question_result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = question_result.scalar_one()
        
        # Eski variantlarni matn ko'rinishida olish
        old_options_text = ", ".join(old_options)
        
        # Yangi variantlarni saqlash
        question.options = json.dumps(options, ensure_ascii=False)
        
        # Agar to'g'ri javob indeksi yangi variantlar sonidan katta bo'lsa, 0 ga o'rnatish
        if question.correct_answer >= len(options):
            question.correct_answer = 0
        
        await session.commit()
        
        # Unit va kitob nomlarini olish
        unit_result = await session.execute(
            select(Unit).where(Unit.id == question.unit_id)
        )
        unit = unit_result.scalar_one()
        
        book_result = await session.execute(
            select(Book).where(Book.id == unit.book_id)
        )
        book = book_result.scalar_one()
        
        await message.answer(
            f"✅ Savol variantlari muvaffaqiyatli o'zgartirildi!\n\n"
            f"📖 Kitob: {book.name}\n"
            f"📄 Unit: {unit.name}\n\n"
            f"📋 Eski variantlar:\n{old_options_text}\n\n"
            f"📋 Yangi variantlar:\n{', '.join(options)}",
            reply_markup=get_admin_main_menu()
        )
    
    await state.clear()

@router.callback_query(F.data.startswith("edit_correct_"))
async def edit_correct_answer_start(callback: types.CallbackQuery, state: FSMContext):
    """To'g'ri javobni o'zgartirishni boshlash"""
    question_id = int(callback.data.split("_")[2])
    
    async with async_session() as session:
        # Savolni olish
        question_result = await session.execute(
            select(Question).where(Question.id == question_id)
        )
        question = question_result.scalar_one()
        
        # Variantlarni olish
        try:
            options = json.loads(question.options)
        except:
            options = ["Variant 1", "Variant 2", "Variant 3", "Variant 4"]
        
        # Eski to'g'ri javob
        old_correct = options[question.correct_answer]
        
        # Variantlarni ko'rsatish
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
        
        # Question ID sini state ga saqlash
        await state.update_data(
            question_id=question_id,
            options=options,
            old_correct_index=question.correct_answer
        )
        
        await callback.message.answer(
            f"✅ To'g'ri javobni o'zgartirish\n\n"
            f"Hozirgi to'g'ri javob: {old_correct}\n\n"
            f"Variantlar:\n{options_text}\n\n"
            f"Yangi to'g'ri javobning raqamini kiriting (1, 2, 3 yoki 4):",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(AdminStates.waiting_for_correct_answer)

# ========== QOSHIMCHA FUNKSIYALAR ==========

@router.callback_query(F.data.startswith("add_unit_to_book_"))
async def add_unit_to_book_edit(callback: types.CallbackQuery, state: FSMContext):
    """Formatlash menyusidan yangi unit qo'shish"""
    book_id = int(callback.data.split("_")[4])
    
    async with async_session() as session:
        result = await session.execute(
            select(Book).where(Book.id == book_id)
        )
        book = result.scalar_one()
        
        await callback.message.answer(
            f"📝 '{book.name}' kitobi uchun yangi unit nomini kiriting:",
            reply_markup=get_cancel_keyboard()
        )
        
        await state.update_data(book_id=book_id, book_name=book.name)
        await state.set_state(AdminStates.waiting_for_unit_name)

@router.callback_query(F.data.startswith("add_question_to_unit_"))
async def add_question_to_unit_edit(callback: types.CallbackQuery, state: FSMContext):
    """Formatlash menyusidan yangi savol qo'shish"""
    unit_id = int(callback.data.split("_")[4])
    
    async with async_session() as session:
        result = await session.execute(
            select(Unit).where(Unit.id == unit_id)
        )
        unit = result.scalar_one()
        
        await callback.message.answer(
            f"🎵 '{unit.name}' unitiga savol qo'shish uchun audio fayl yuboring:"
        )
        
        await state.update_data(unit_id=unit_id, unit_name=unit.name)
        await state.set_state(AdminStates.waiting_for_audio)

@router.callback_query(F.data == "back_to_edit_menu")
async def back_to_edit_menu(callback: types.CallbackQuery):
    """Formatlash menyusiga qaytish"""
    await start_edit_test(callback.message)

@router.callback_query(F.data == "back_to_main_from_edit")
async def back_to_main_from_edit(callback: types.CallbackQuery):
    """Asosiy menyuga qaytish"""
    await callback.message.edit_text("Asosiy menyu:")
    await callback.message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )








# handlers/admin.py fayliga qo'shing:

# handlers/admin.py ga qo'shing:

# ========== UMUMIY NATIJALAR (SODDA VERSIYA) ==========

@router.message(F.text == "📊 Umumiy natijalar")
async def total_results(message: types.Message):
    """Admin uchun umumiy test natijalari statistikasi"""
    # Yuklanmoqda xabari
    loading_msg = await message.answer("📊 Statistika hisoblanmoqda...")
    
    async with async_session() as session:
        # 1. UMUMIY STATISTIKA
        total_stats = await session.execute(
            select(
                func.count(UserResult.id).label('total_tests'),
                func.sum(UserResult.correct_answers).label('total_correct'),
                func.sum(UserResult.total_questions).label('total_questions'),
                func.avg(UserResult.score).label('avg_score'),
                func.count(distinct(UserResult.user_id)).label('unique_users')
            )
        )
        stats = total_stats.one()
        
        total_tests, total_correct, total_questions, avg_score, unique_users = stats
        
        # 2. KITOBLAR BO'YICHA STATISTIKA
        books_stats = await session.execute(
            select(
                Book.name,
                func.count(UserResult.id).label('test_count'),
                func.avg(UserResult.score).label('avg_score'),
                func.count(distinct(UserResult.user_id)).label('user_count')
            )
            .join(UserResult, Book.id == UserResult.book_id, isouter=True)
            .group_by(Book.id, Book.name)
            .order_by(func.count(UserResult.id).desc())
            .limit(10)  # Eng ko'p test ishlangan 10 ta kitob
        )
        
        # 3. ENG FAOL FOYDALANUVCHILAR (top 10)
        active_users = await session.execute(
            select(
                User.first_name,
                User.last_name,
                User.username,
                func.count(UserResult.id).label('test_count'),
                func.avg(UserResult.score).label('avg_score'),
                func.max(UserResult.score).label('best_score')
            )
            .join(UserResult, User.user_id == UserResult.user_id)
            .where(User.is_active == True)
            .group_by(User.user_id, User.first_name, User.last_name, User.username)
            .order_by(func.count(UserResult.id).desc())
            .limit(10)
        )
        
        # 4. ENG YAXSHI NATIJALAR (top 10)
        best_results = await session.execute(
            select(
                User.first_name,
                User.last_name,
                Book.name,
                Unit.name,
                UserResult.score,
                UserResult.correct_answers,
                UserResult.total_questions,
                UserResult.completed_at
            )
            .join(User, User.user_id == UserResult.user_id)
            .join(Book, Book.id == UserResult.book_id)
            .join(Unit, Unit.id == UserResult.unit_id)
            .where(User.is_active == True)
            .order_by(UserResult.score.desc())
            .limit(10)
        )
        
        # NATIJALARNI KO'RSATISH
        results_text = "📊 BOT UMUMIY STATISTIKASI\n\n"
        
        # 1. UMUMIY STATISTIKA
        results_text += "🔢 UMUMIY KO'RSATKICHLAR:\n"
        results_text += f"• 📈 Testlar soni: {total_tests or 0} ta\n"
        results_text += f"• 👥 Foydalanuvchilar: {unique_users or 0} ta\n"
        results_text += f"• ✅ To'g'ri javoblar: {total_correct or 0}/{total_questions or 0}\n"
        results_text += f"• 🏆 O'rtacha ball: {(avg_score or 0):.1f}%\n\n"
        
        # 2. KITOBLAR STATISTIKASI
        results_text += "📚 KITOBLAR BO'YICHA (top 10):\n"
        books_data = books_stats.all()
        
        if books_data:
            for i, (book_name, test_count, book_avg, user_count) in enumerate(books_data, 1):
                if book_name:  # Kitob nomi bo'lsa
                    results_text += f"{i}. {book_name}\n"
                    results_text += f"   📊 Testlar: {test_count or 0} ta\n"
                    results_text += f"   👥 Foydalanuvchilar: {user_count or 0} ta\n"
                    results_text += f"   🏆 O'rtacha: {(book_avg or 0):.1f}%\n"
        else:
            results_text += "   Hozircha ma'lumot yo'q\n"
        
        results_text += "\n"
        
        # 3. ENG FAOL FOYDALANUVCHILAR
        results_text += "👑 ENG FAOL FOYDALANUVCHILAR (top 10):\n"
        users_data = active_users.all()
        
        if users_data:
            for i, (first_name, last_name, username, test_count, user_avg, best_score) in enumerate(users_data, 1):
                name = f"{first_name or ''} {last_name or ''}".strip()
                if not name:
                    name = "Noma'lum"
                
                username_display = f" @{username}" if username else ""
                
                results_text += f"{i}. {name}{username_display}\n"
                results_text += f"   📊 Testlar: {test_count or 0} ta\n"
                results_text += f"   🏆 O'rtacha: {(user_avg or 0):.1f}%\n"
                if best_score:
                    results_text += f"   ⭐ Eng yaxshi: {best_score}%\n"
        else:
            results_text += "   Hozircha ma'lumot yo'q\n"
        
        results_text += "\n"
        
        # 4. ENG YAXSHI NATIJALAR
        results_text += "🏆 ENG YAXSHI NATIJALAR (top 10):\n"
        best_data = best_results.all()
        
        if best_data:
            for i, (first_name, last_name, book_name, unit_name, score, correct, total, completed_at) in enumerate(best_data, 1):
                name = f"{first_name or ''} {last_name or ''}".strip()
                if not name:
                    name = "Noma'lum"
                
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                
                results_text += f"{medal} {name}\n"
                results_text += f"   📖 {book_name} - {unit_name}\n"
                results_text += f"   ✅ {correct}/{total}\n"
                results_text += f"   ⭐ {score}%\n"
                results_text += f"   📅 {completed_at.strftime('%d.%m.%Y')}\n"
        else:
            results_text += "   Hozircha ma'lumot yo'q\n"
        
        # Xabarni yuborish
        await loading_msg.delete()
        
        # Agar xabar juda uzun bo'lsa, qismlarga bo'lamiz
        if len(results_text) > 4000:
            # Birinchi qism
            part1 = results_text[:4000]
            await message.answer(part1)
            
            # Ikkinchi qism
            part2 = results_text[4000:8000] if len(results_text) > 8000 else results_text[4000:]
            await message.answer(part2)
        else:
            await message.answer(results_text)

# ========== FOYDALANUVCHILAR REYTINGI (ADMIN UCHUN) ==========

@router.message(F.text == "🏆 Foydalanuvchilar reytingi")
async def users_rating_admin(message: types.Message):
    """Admin uchun foydalanuvchilar reytingi"""
    loading_msg = await message.answer("🏆 Reyting hisoblanmoqda...")
    
    async with async_session() as session:
        # Reytingni hisoblash
        rating_result = await session.execute(
            select(
                User.user_id,
                User.first_name,
                User.last_name,
                User.username,
                func.avg(UserResult.score).label('avg_score'),
                func.count(UserResult.id).label('tests_count'),
                func.max(UserResult.score).label('best_score')
            )
            .join(UserResult, User.user_id == UserResult.user_id)
            .where(User.is_active == True)
            .group_by(User.user_id, User.first_name, User.last_name, User.username)
            .order_by(func.avg(UserResult.score).desc())
            .limit(20)
        )
        
        rating_list = rating_result.all()
        
        if not rating_list:
            await loading_msg.edit_text("🏆 Hozircha reyting mavjud emas.")
            return
        
        # Reyting matni
        rating_text = "🏆 FOYDALANUVCHILAR REYTINGI (TOP 20)\n\n"
        
        for i, (user_id, first_name, last_name, username, avg_score, tests_count, best_score) in enumerate(rating_list, 1):
            # Foydalanuvchi nomini tayyorlash
            name = f"{first_name or ''} {last_name or ''}".strip()
            if not name:
                name = f"User_{user_id}"
            
            # Username
            username_display = f" @{username}" if username else ""
            
            # Medallar
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            rating_text += (
                f"{medal} {name}{username_display}\n"
                f"   🆔 ID: {user_id}\n"
                f"   📊 O'rtacha: {avg_score:.1f}%\n"
                f"   📈 Testlar: {tests_count} ta\n"
                f"   ⭐ Eng yaxshi: {best_score}%\n\n"
            )
        
        # Qo'shimcha statistika
        total_users = len(rating_list)
        overall_avg = sum([r[4] for r in rating_list]) / total_users if total_users > 0 else 0
        
        rating_text += (
            f"📊 UMUMIY STATISTIKA:\n"
            f"• 👥 Reytingdagi foydalanuvchilar: {total_users} ta\n"
            f"• 🏆 Umumiy o'rtacha: {overall_avg:.1f}%\n"
            f"• 📈 Eng yuqori o'rtacha: {rating_list[0][4]:.1f}%\n"
            f"• 📉 Eng past o'rtacha: {rating_list[-1][4]:.1f}%\n"
        )
        
        # Filter tugmalari
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="📊 O'rtacha bo'yicha", callback_data="admin_rating_avg"),
                    types.InlineKeyboardButton(text="🥇 Eng yaxshi natija", callback_data="admin_rating_best")
                ],
                [
                    types.InlineKeyboardButton(text="📈 Testlar soni", callback_data="admin_rating_tests")
                ]
            ]
        )
        
        await loading_msg.delete()
        await message.answer(rating_text, reply_markup=keyboard)

@router.callback_query(F.data == "admin_rating_avg")
async def admin_rating_by_avg(callback: types.CallbackQuery):
    """Admin uchun o'rtacha ball bo'yicha reyting"""
    await show_admin_rating_by(callback, "avg")

@router.callback_query(F.data == "admin_rating_best")
async def admin_rating_by_best(callback: types.CallbackQuery):
    """Admin uchun eng yaxshi natija bo'yicha reyting"""
    await show_admin_rating_by(callback, "best")

@router.callback_query(F.data == "admin_rating_tests")
async def admin_rating_by_tests(callback: types.CallbackQuery):
    """Admin uchun testlar soni bo'yicha reyting"""
    await show_admin_rating_by(callback, "tests")

async def show_admin_rating_by(callback: types.CallbackQuery, sort_by="avg"):
    """Admin uchun turli mezonlar bo'yicha reyting"""
    async with async_session() as session:
        if sort_by == "avg":
            # O'rtacha ball bo'yicha
            rating_result = await session.execute(
                select(
                    User.user_id,
                    User.first_name,
                    User.last_name,
                    User.username,
                    func.avg(UserResult.score).label('value'),
                    func.count(UserResult.id).label('tests_count')
                )
                .join(UserResult, User.user_id == UserResult.user_id)
                .where(User.is_active == True)
                .group_by(User.user_id, User.first_name, User.last_name, User.username)
                .order_by(func.avg(UserResult.score).desc())
                .limit(15)
            )
            title = "📊 O'rtacha ball bo'yicha TOP 15"
            value_label = "O'rtacha"
            
        elif sort_by == "best":
            # Eng yaxshi natija bo'yicha
            rating_result = await session.execute(
                select(
                    User.user_id,
                    User.first_name,
                    User.last_name,
                    User.username,
                    func.max(UserResult.score).label('value'),
                    func.count(UserResult.id).label('tests_count')
                )
                .join(UserResult, User.user_id == UserResult.user_id)
                .where(User.is_active == True)
                .group_by(User.user_id, User.first_name, User.last_name, User.username)
                .order_by(func.max(UserResult.score).desc())
                .limit(15)
            )
            title = "🥇 Eng yaxshi natija bo'yicha TOP 15"
            value_label = "Eng yaxshi"
            
        elif sort_by == "tests":
            # Testlar soni bo'yicha
            rating_result = await session.execute(
                select(
                    User.user_id,
                    User.first_name,
                    User.last_name,
                    User.username,
                    func.count(UserResult.id).label('value'),
                    func.avg(UserResult.score).label('avg_score')
                )
                .join(UserResult, User.user_id == UserResult.user_id)
                .where(User.is_active == True)
                .group_by(User.user_id, User.first_name, User.last_name, User.username)
                .order_by(func.count(UserResult.id).desc())
                .limit(15)
            )
            title = "📈 Testlar soni bo'yicha TOP 15"
            value_label = "Testlar"
        
        rating_list = rating_result.all()
        
        if not rating_list:
            await callback.message.edit_text("🏆 Hozircha ma'lumot yo'q.")
            return
        
        rating_text = f"{title}:\n\n"
        
        for i, (user_id, first_name, last_name, username, value, extra) in enumerate(rating_list, 1):
            # Foydalanuvchi nomini tayyorlash
            name = f"{first_name or ''} {last_name or ''}".strip()
            if not name:
                name = f"User_{user_id}"
            
            # Username
            username_display = f" @{username}" if username else ""
            
            # Medallar
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            rating_text += f"{medal} {name}{username_display}\n"
            rating_text += f"   🆔 ID: {user_id}\n"
            
            if sort_by == "avg":
                rating_text += f"   📊 {value_label}: {value:.1f}%\n"
                rating_text += f"   📈 Testlar: {extra} ta\n\n"
            elif sort_by == "best":
                rating_text += f"   ⭐ {value_label}: {value}%\n"
                rating_text += f"   📊 Testlar: {extra} ta\n\n"
            elif sort_by == "tests":
                rating_text += f"   📈 {value_label}: {value} ta\n"
                rating_text += f"   📊 O'rtacha: {extra:.1f}%\n\n"
        
        # Tugmalar
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="📊 Asosiy reyting", callback_data="admin_back_to_main_rating")
                ]
            ]
        )
        
        await callback.message.edit_text(rating_text, reply_markup=keyboard)

@router.callback_query(F.data == "admin_back_to_main_rating")
async def admin_back_to_main_rating(callback: types.CallbackQuery):
    """Admin uchun asosiy reytingga qaytish"""
    await users_rating_admin(callback.message)


@router.message(F.text == "⬅️ Orqaga")
async def back_to_main(message: types.Message):
    await message.answer(
        "Asosiy menyu:",
        reply_markup=get_admin_main_menu()
    )