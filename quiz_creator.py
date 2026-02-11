# ============= TEST TUZISH TIZIMI =============
import os
import json
import uuid
from datetime import datetime
from aiogram import F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import FSInputFile, InputFile
import tempfile

# ============= FSM HOLATLARI =============
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
    
    # Testni tahrirlash
    editing_question = State()

# ============= MA'LUMOTLAR BAZASI =============
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
            # Test ma'lumotlari
            books_db = {
                "book_1": {
                    "id": "book_1",
                    "name": "Ingliz tili",
                    "description": "Ingliz tili darsligi",
                    "created_by": 123456789,
                    "created_at": datetime.now().isoformat(),
                    "units": {
                        "unit_1": {
                            "id": "unit_1",
                            "name": "Greetings",
                            "description": "Salomlashish",
                            "created_at": datetime.now().isoformat(),
                            "tests": {
                                "test_1": {
                                    "id": "test_1",
                                    "question": "Salom qanday aytiladi?",
                                    "audio_file": None,
                                    "options": ["Hello", "Goodbye", "Thanks", "Sorry"],
                                    "correct_answer": 0,
                                    "explanation": "Hello - salom",
                                    "created_at": datetime.now().isoformat()
                                }
                            }
                        }
                    }
                }
            }
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

# ============= ADMIN TEKSHIRISH DECORATOR =============
def admin_required(handler):
    """Admin huquqini tekshirish"""
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

# ============= TEST TUZISH MENYUSI =============
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
        for book_id, book in books_db.items():
            units_count = len(book.get('units', {}))
            tests_count = sum(len(unit.get('tests', {})) for unit in book.get('units', {}).values())
            
            text += f"📖 **{book['name']}**\n"
            text += f"🆔 `{book_id}`\n"
            text += f"📝 {book.get('description', 'Tavsifsiz')}\n"
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
    for book_id, book in list(books_db.items())[:10]:  # Oxirgi 10 ta kitob
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
        f"📝 {book.get('description', 'Tavsifsiz')}\n"
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
        for unit_id, unit in units.items():
            tests_count = len(unit.get('tests', {}))
            text += f"📖 **{unit['name']}**\n"
            text += f"🆔 `{unit_id}`\n"
            text += f"📝 {unit.get('description', 'Tavsifsiz')}\n"
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
    book_id = callback.data.replace('select_unit_', '')
    
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

@dp.callback_query(F.data.startswith('select_unit_'))
@admin_callback_required
async def select_unit_final_callback(callback: CallbackQuery, state: FSMContext):
    """Unit tanlanganda"""
    parts = callback.data.split('_')
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
        f"📝 {unit.get('description', 'Tavsifsiz')}\n"
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
        # Audio faylni yuklab olish
        if message.audio:
            file_id = message.audio.file_id
            file_name = message.audio.file_name or f"audio_{uuid.uuid4().hex[:8]}.mp3"
        else:  # voice
            file_id = message.voice.file_id
            file_name = f"voice_{uuid.uuid4().hex[:8]}.ogg"
        
        # Faylni yuklab olish
        file = await bot.get_file(file_id)
        file_path = file.file_path
        
        # Audioni saqlash (real projectda cloud storage ga saqlang)
        # Hozircha file_id ni saqlaymiz
        await state.update_data(audio_file=file_id, audio_file_name=file_name)
        await state.set_state(TestCreationStates.waiting_options)
        
        await message.reply(
            "✅ Audio qabul qilindi!\n\n"
            "📝 **Variantlarni kiriting**\n\n"
            "4 ta variantni har bir qatorga bittadan yozing:\n"
            "Masalan:\n"
            "Variant 1\n"
            "Variant 2\n"
            "Variant 3\n"
            "Variant 4",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"❌ Audio yuklashda xatolik: {e}")
        await message.reply("❌ Audio yuklashda xatolik yuz berdi. Qayta urinib ko'ring yoki audiosiz davom eting.")

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
    
    # Variantlarni tugmalar bilan ko'rsatish
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
        f"✅ To'g'ri javob: **{callback.message.reply_markup.inline_keyboard[correct_index][0].text}**\n\n"
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
    
    # Test ma'lumotlarini olish
    data = await state.get_data()
    
    test_id = f"test_{uuid.uuid4().hex[:8]}"
    
    book_id = data.get('test_book_id')
    unit_id = data.get('test_unit_id')
    
    if book_id in books_db and unit_id in books_db[book_id]['units']:
        # Testni saqlash
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
            f"🎵 Audio: {'Bor' if data.get('audio_file') else 'Yoq'}\n"
            f"✅ To'g'ri javob: {data.get('options')[data.get('correct_answer')]}\n\n"
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

# ============= BOT ISHGA TUSHGANDA =============
def init_test_system():
    """Test tizimini ishga tushirish"""
    load_books_db()
    logger.info("📚 Test tuzish tizimi yuklandi")