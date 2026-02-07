# handlers/test.py - TEST YECHISH UCHUN UMUMIY HANDLERLAR
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
import asyncio
import os
import json
from database import async_session, Book, Unit, Question, UserResult
from sqlalchemy import select
from keyboards import (
    get_user_main_menu,
    get_admin_main_menu,
    get_books_keyboard_for_users,
    get_units_keyboard_for_users,
    get_test_options,
    get_yes_no_keyboard,
    get_cancel_keyboard
)
from states import UserStates
from aiogram.types import FSInputFile

router = Router()

# ========== UMUMIY TEST YECHISH FUNKSIYALARI ==========

async def start_test_for_user(message: types.Message, state: FSMContext, is_admin=False):
    """Test boshlash - kitob tanlash (ham admin, ham user uchun)"""
    async with async_session() as session:
        result = await session.execute(select(Book))
        books = result.scalars().all()
        
        if not books:
            await message.answer(
                "❌ Hozircha testlar mavjud emas. "
                "Iltimos, admin test yaratishini kuting."
            )
            return
        
        await message.answer(
            "📚 Test ishlash uchun kitob tanlang:",
            reply_markup=get_books_keyboard_for_users(books)
        )
        # Admin yoki user ekanligini state ga saqlash
        await state.update_data(is_admin=is_admin)
        await state.set_state(UserStates.choosing_book)

@router.message(F.text == "🚀 Test boshlash")
async def user_start_test(message: types.Message, state: FSMContext):
    """User uchun test boshlash"""
    await start_test_for_user(message, state, is_admin=False)

@router.message(F.text == "🧪 Test yechish")
async def admin_start_test(message: types.Message, state: FSMContext):
    """Admin uchun test boshlash"""
    await start_test_for_user(message, state, is_admin=True)

@router.callback_query(F.data.startswith("select_user_book_"))
async def select_book_for_test(callback: types.CallbackQuery, state: FSMContext):
    """Kitob tanlagandan keyin unitlarni ko'rsatish"""
    book_id = int(callback.data.split("_")[3])
    
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
            await callback.message.answer(
                f"❌ '{book.name}' kitobida hali unitlar mavjud emas."
            )
            await state.clear()
            return
        
        # Kitob ID sini state ga saqlash
        await state.update_data(book_id=book_id, book_name=book.name)
        
        await callback.message.edit_text(
            f"📖 Kitob: {book.name}\n\n"
            f"Unit tanlang:",
            reply_markup=get_units_keyboard_for_users(units)
        )
        await state.set_state(UserStates.choosing_unit)

@router.callback_query(F.data.startswith("select_user_unit_"))
async def select_unit_for_test(callback: types.CallbackQuery, state: FSMContext):
    """Unit tanlagandan keyin testni boshlash"""
    unit_id = int(callback.data.split("_")[3])
    
    async with async_session() as session:
        # Unitni olish
        unit_result = await session.execute(
            select(Unit).where(Unit.id == unit_id)
        )
        unit = unit_result.scalar_one()
        
        # Unitdagi savollarni hisoblash
        questions_result = await session.execute(
            select(Question).where(Question.unit_id == unit_id)
        )
        questions = questions_result.scalars().all()
        
        if not questions:
            await callback.message.answer(
                f"❌ '{unit.name}' unitida hali savollar mavjud emas."
            )
            await state.clear()
            return
        
        # Unit ma'lumotlarini state ga saqlash
        await state.update_data(
            unit_id=unit_id,
            unit_name=unit.name,
            questions_count=len(questions),
            question_ids=[q.id for q in questions],  # Savol ID larini saqlaymiz
            current_question_index=0,
            correct_answers=0
        )
        
        await callback.message.answer(
            f"📄 Unit: {unit.name}\n"
            f"📊 Savollar soni: {len(questions)}\n\n"
            f"Testni boshlashga tayyormisiz?",
            reply_markup=get_yes_no_keyboard()
        )

@router.message(F.text == "✅ Ha")
async def confirm_start_test(message: types.Message, state: FSMContext):
    """Testni boshlashni tasdiqlash"""
    data = await state.get_data()
    
    if not data.get('unit_id'):
        await message.answer("Iltimos, avval unit tanlang.")
        return
    
    # Admin yoki user ekanligini olish
    is_admin = data.get('is_admin', False)
    
    await message.answer(
        "🎯 Test boshlandi! E'tibor bering!\n\n"
        "Har bir savol uchun audio tinglab, to'g'ri javobni tanlang.",
        reply_markup=types.ReplyKeyboardRemove()
    )
    
    # Testni boshlash
    await send_next_question(message, state, is_admin)

async def send_next_question(message: types.Message, state: FSMContext, is_admin=False):
    """Keyingi savolni yuborish"""
    data = await state.get_data()
    
    unit_id = data.get('unit_id')
    current_question_index = data.get('current_question_index', 0)
    question_ids = data.get('question_ids', [])
    
    if current_question_index >= len(question_ids):
        # Test tugadi
        await finish_test(message, state, is_admin)
        return
    
    # Joriy savol ID sini olish
    current_question_id = question_ids[current_question_index]
    
    async with async_session() as session:
        # Savolni olish
        question_result = await session.execute(
            select(Question).where(Question.id == current_question_id)
        )
        question = question_result.scalar_one()
        
        # Audio faylni yuborish
        try:
            if os.path.exists(question.audio_path):
                audio = FSInputFile(question.audio_path)
                await message.answer_audio(audio=audio)
            else:
                # Agar fayl yo'q bo'lsa
                await message.answer("🎵 (Audio fayli mavjud emas)")
        except Exception as e:
            print(f"Audio xatosi: {e}")
            await message.answer("🎵 (Audio yuborishda xatolik)")
        
        # Variantlarni tayyorlash
        try:
            options = json.loads(question.options)
        except:
            options = ["Variant 1", "Variant 2", "Variant 3", "Variant 4"]
        
        # Javoblar tugmalarini yuborish
        await message.answer(
            f"❓ Savol {current_question_index + 1}/{len(question_ids)}\n"
            f"Javobni tanlang:",
            reply_markup=get_test_options(options)
        )
        
        # Savol ma'lumotlarini state ga saqlash
        await state.update_data(
            current_question_id=current_question_id,
            current_question=question,
            current_question_index=current_question_index
        )
        
        await state.set_state(UserStates.waiting_for_answer)

@router.callback_query(UserStates.waiting_for_answer, F.data.startswith("answer_"))
async def process_answer(callback: types.CallbackQuery, state: FSMContext):
    """Foydalanuvchi javobini qabul qilish"""
    user_answer_index = int(callback.data.split("_")[1])
    data = await state.get_data()
    
    current_question = data.get('current_question')
    correct_answers = data.get('correct_answers', 0)
    current_question_index = data.get('current_question_index', 0)
    is_admin = data.get('is_admin', False)
    
    # Variantlarni olish
    try:
        options = json.loads(current_question.options)
    except:
        options = ["Variant 1", "Variant 2", "Variant 3", "Variant 4"]
    
    user_answer = options[user_answer_index]
    correct_answer = options[current_question.correct_answer]
    
    # Javobni tekshirish
    is_correct = (user_answer_index == current_question.correct_answer)
    
    if is_correct:
        correct_answers += 1
        response_text = f"✅ To'g'ri! Javob: {correct_answer}"
    else:
        response_text = f"❌ Noto'g'ri. To'g'ri javob: {correct_answer}"
    
    await callback.message.answer(response_text)
    
    # Natijani yangilash
    await state.update_data(correct_answers=correct_answers)
    
    # Keyingi savolga o'tish
    await state.update_data(
        current_question_index=current_question_index + 1
    )
    
    # Kichik kutish
    await asyncio.sleep(1)
    
    # Keyingi savolni yuborish
    await send_next_question(callback.message, state, is_admin)

async def finish_test(message: types.Message, state: FSMContext, is_admin=False):
    """Testni yakunlash va natijalarni ko'rsatish"""
    data = await state.get_data()
    
    correct_answers = data.get('correct_answers', 0)
    total_questions = data.get('questions_count', 0)
    book_id = data.get('book_id')
    unit_id = data.get('unit_id')
    unit_name = data.get('unit_name')
    user_id = message.from_user.id
    
    # Agar book_id yo'q bo'lsa, unit orqali topamiz
    if not book_id and unit_id:
        async with async_session() as session:
            unit_result = await session.execute(
                select(Unit).where(Unit.id == unit_id)
            )
            unit = unit_result.scalar_one()
            book_id = unit.book_id
    
    # Foizni hisoblash
    score_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
    
    # Natijani database ga saqlash (faqat userlar uchun)
    if not is_admin:
        async with async_session() as session:
            new_result = UserResult(
                user_id=user_id,
                book_id=book_id,
                unit_id=unit_id,
                correct_answers=correct_answers,
                total_questions=total_questions,
                score=int(score_percentage)
            )
            session.add(new_result)
            await session.commit()
    
    # Natijani ko'rsatish
    result_text = (
        f"🎉 Test yakunlandi!\n\n"
        f"📄 Unit: {unit_name}\n"
        f"📊 Natijangiz: {correct_answers}/{total_questions}\n"
        f"📈 Foiz: {score_percentage:.1f}%\n\n"
    )
    
    # Baholash
    if score_percentage >= 90:
        result_text += "🏅 A'lo! Juda yaxshi!"
    elif score_percentage >= 70:
        result_text += "👍 Yaxshi!"
    elif score_percentage >= 50:
        result_text += "😊 Qoniqarli"
    else:
        result_text += "📚 Yana mashq qilishingiz kerak"
    
    # Admin yoki user ekanligiga qarab menyu ko'rsatish
    if is_admin:
        from keyboards import get_admin_main_menu
        await message.answer(
            result_text,
            reply_markup=get_admin_main_menu()
        )
    else:
        await message.answer(
            result_text,
            reply_markup=get_user_main_menu()
        )
    
    # State ni tozalash
    await state.clear()

# ========== BEKOR QILISH ==========

@router.message(F.text == "❌ Yo'q")
async def cancel_test(message: types.Message, state: FSMContext):
    """Testni bekor qilish"""
    await state.clear()
    
    # Admin yoki user ekanligini tekshirish
    from main import ADMIN_ID
    if message.from_user.id == ADMIN_ID:
        from keyboards import get_admin_main_menu
        await message.answer("Test bekor qilindi.", reply_markup=get_admin_main_menu())
    else:
        await message.answer("Test bekor qilindi.", reply_markup=get_user_main_menu())

@router.callback_query(F.data == "cancel")
async def cancel_test_callback(callback: types.CallbackQuery, state: FSMContext):
    """Callback orqali testni bekor qilish"""
    await state.clear()
    await callback.message.edit_text("❌ Test bekor qilindi.")
    
    # Admin yoki user ekanligini tekshirish
    from main import ADMIN_ID
    if callback.from_user.id == ADMIN_ID:
        from keyboards import get_admin_main_menu
        await callback.message.answer("Asosiy menyu:", reply_markup=get_admin_main_menu())
    else:
        await callback.message.answer("Asosiy menyu:", reply_markup=get_user_main_menu())