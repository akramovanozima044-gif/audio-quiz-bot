# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# User menu
# keyboards.py - Yangilangan user menu funksiyasi

def get_user_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📚 Test yechish")
    
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# Admin menu
def get_admin_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📝 Test tuzish")
    builder.button(text="🧪 Test yechish")
    builder.button(text="🗑️ Test formatlash/o'chirish")
    builder.button(text="👥 Foydalanuvchilar ro'yxati")
    builder.button(text="📢 Habar yuborish")
    builder.button(text="📊 Umumiy natijalar")
    builder.adjust(2, 2, 2)
    return builder.as_markup(resize_keyboard=True)

# Tasdiqlash tugmalari
def get_confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ruxsat berish", callback_data="allow_user")
    builder.button(text="❌ Rad etish", callback_data="deny_user")
    builder.adjust(2)
    return builder.as_markup()

# Kitoblar tugmalari (inline)
def get_books_keyboard(books, action="select"):
    builder = InlineKeyboardBuilder()
    for book in books:
        builder.button(text=book.name, callback_data=f"{action}_book_{book.id}")
    if action == "select":
        builder.button(text="➕ Yangi kitob qo'shish", callback_data="add_new_book")
    builder.button(text="🔙 Orqaga", callback_data="back_to_admin_menu")
    builder.adjust(1)
    return builder.as_markup()

# Test tuzish uchun kitoblar tugmalari
def get_books_for_create_keyboard(books):
    builder = InlineKeyboardBuilder()
    for book in books:
        builder.button(text=book.name, callback_data=f"create_book_{book.id}")
    builder.button(text="➕ Yangi kitob qo'shish", callback_data="add_new_book_for_create")
    builder.button(text="🔙 Orqaga", callback_data="back_to_test_create_menu")
    builder.adjust(1)
    return builder.as_markup()

# Unit tugmalari
def get_units_keyboard(units, book_id, action="create"):
    builder = InlineKeyboardBuilder()
    for unit in units:
        builder.button(text=unit.name, callback_data=f"{action}_unit_{unit.id}")
    builder.button(text="➕ Yangi unit qo'shish", callback_data=f"add_unit_{book_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"back_to_books_{book_id}")
    builder.adjust(1)
    return builder.as_markup()

# Savol qo'shish tugmalari
def get_add_question_keyboard(unit_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Savol qo'shish", callback_data=f"add_question_{unit_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"back_to_units_{unit_id}")
    builder.adjust(1)
    return builder.as_markup()

# Test yaratishni yakunlash
def get_finish_creating_keyboard(unit_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yakunlash", callback_data=f"finish_creating_{unit_id}")
    builder.button(text="➕ Yana savol qo'shish", callback_data=f"add_more_question_{unit_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"back_to_units_{unit_id}")
    builder.adjust(1)
    return builder.as_markup()

# Admin test tuzish menu
def get_test_create_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📚 Mavjud kitoblar")
    builder.button(text="➕ Yangi kitob qo'shish")
    builder.button(text="🔙 Orqaga")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# Test yakunlash menu
def get_test_finish_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔄 Testni boshidan boshlash")
    builder.button(text="🏠 Menuga qaytish")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# Foydalanuvchilarni boshqarish
def get_users_management_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="👁️ Foydalanuvchilarni ko'rish")
    builder.button(text="❌ Foydalanuvchini o'chirish")
    builder.button(text="🔙 Orqaga")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# Bekor qilish tugmasi
def get_cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="❌ Bekor qilish")
    builder.adjust(1)
    return builder.as_markup(resize_keyboard=True)

# keyboards.py ga qo'shimcha funksiyalar

# Test yechish uchun kitoblar tugmalari
def get_books_for_test_keyboard(books, user_type="admin"):
    builder = InlineKeyboardBuilder()
    for book in books:
        builder.button(text=book.name, callback_data=f"test_book_{book.id}_{user_type}")
    builder.button(text="🔙 Orqaga", callback_data=f"back_to_{user_type}_menu")
    builder.adjust(1)
    return builder.as_markup()

# Test yechish uchun unit tugmalari
def get_units_for_test_keyboard(units, book_id, user_type="admin"):
    builder = InlineKeyboardBuilder()
    for unit in units:
        builder.button(text=unit.name, callback_data=f"test_unit_{unit.id}_{user_type}")
    builder.button(text="🔙 Orqaga", callback_data=f"back_to_test_books_{user_type}")
    builder.adjust(1)
    return builder.as_markup()

# Testni boshlash tugmasi
def get_start_test_keyboard(unit_id, user_type="admin"):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Testni boshlash", callback_data=f"start_test_{unit_id}_{user_type}")
    builder.button(text="🔙 Orqaga", callback_data=f"back_to_test_units_{unit_id}_{user_type}")
    builder.adjust(1)
    return builder.as_markup()

# Test davomida javob variantlari
def get_answer_options_keyboard(options, question_index):
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(options):
        builder.button(text=option, callback_data=f"answer_{i}_{question_index}")
    builder.adjust(1)
    return builder.as_markup()

# Test yakunlash menyusi
def get_test_complete_menu(user_type="user"):
    builder = ReplyKeyboardBuilder()
    builder.button(text="🔄 Testni qayta boshlash")
    if user_type == "admin":
        builder.button(text="🏠 Admin menyusi")
    else:
        builder.button(text="🏠 User menyusi")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)    
# keyboards.py ga qo'shimcha funksiyalar

# Formatlash/o'chirish menyusi
def get_format_menu_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="📚 Kitoblarni boshqarish")
    builder.button(text="📝 Unitlarni boshqarish")
    builder.button(text="❓ Savollarni boshqarish")
    builder.button(text="🔙 Orqaga")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# Kitoblarni boshqarish
def get_books_manage_keyboard(books):
    builder = InlineKeyboardBuilder()
    for book in books:
        builder.button(text=f"✏️ {book.name}", callback_data=f"manage_book_{book.id}")
    builder.button(text="🔙 Orqaga", callback_data="back_to_format_menu")
    builder.adjust(1)
    return builder.as_markup()

# Kitobni boshqarish
def get_book_manage_options(book_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Nomni o'zgartirish", callback_data=f"edit_book_name_{book_id}")
    builder.button(text="🗑️ Kitobni o'chirish", callback_data=f"delete_book_{book_id}")
    builder.button(text="📝 Unitlarini ko'rish", callback_data=f"view_units_{book_id}")
    builder.button(text="🔙 Orqaga", callback_data="back_to_books_manage")
    builder.adjust(1)
    return builder.as_markup()

# Unitlarni boshqarish
def get_units_manage_keyboard(units, book_id):
    builder = InlineKeyboardBuilder()
    for unit in units:
        builder.button(text=f"✏️ {unit.name}", callback_data=f"manage_unit_{unit.id}")
    builder.button(text="🔙 Orqaga", callback_data=f"back_to_book_manage_{book_id}")
    builder.adjust(1)
    return builder.as_markup()

# Unitni boshqarish
def get_unit_manage_options(unit_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Nomni o'zgartirish", callback_data=f"edit_unit_name_{unit_id}")
    builder.button(text="🗑️ Unitni o'chirish", callback_data=f"delete_unit_{unit_id}")
    builder.button(text="❓ Savollarini ko'rish", callback_data=f"view_questions_{unit_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"back_to_units_manage_{unit_id}")
    builder.adjust(1)
    return builder.as_markup()

# Savollarni boshqarish
def get_questions_manage_keyboard(questions, unit_id):
    builder = InlineKeyboardBuilder()
    for question in questions:
        # Qisqa nom (audio fayl nomi yoki ID)
        display_name = f"Savol {question.id}"
        if question.audio_file:
            if isinstance(question.audio_file, str) and len(question.audio_file) > 10:
                display_name = f"🎵 Savol {question.id}"
        
        builder.button(text=f"✏️ {display_name}", callback_data=f"manage_question_{question.id}")
    builder.button(text="🔙 Orqaga", callback_data=f"back_to_unit_manage_{unit_id}")
    builder.adjust(1)
    return builder.as_markup()

# Savolni boshqarish
def get_question_manage_options(question_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✏️ Audio ni o'zgartirish", callback_data=f"edit_question_audio_{question_id}")
    builder.button(text="✏️ Variantlarni o'zgartirish", callback_data=f"edit_question_options_{question_id}")
    builder.button(text="✏️ To'g'ri javobni o'zgartirish", callback_data=f"edit_question_answer_{question_id}")
    builder.button(text="🗑️ Savolni o'chirish", callback_data=f"delete_question_{question_id}")
    builder.button(text="🔙 Orqaga", callback_data=f"back_to_questions_manage_{question_id}")
    builder.adjust(1)
    return builder.as_markup()

# Tasdiqlash tugmalari
def get_confirmation_keyboard(action, item_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, o'chirish", callback_data=f"confirm_{action}_{item_id}")
    builder.button(text="❌ Yo'q, bekor qilish", callback_data=f"cancel_{action}_{item_id}")
    builder.adjust(2)
    return builder.as_markup()

# keyboards.py - F-qadam uchun yangi funksiyalar

# Foydalanuvchilarni o'chirish uchun tugmalar
def get_users_delete_keyboard(users):
    builder = InlineKeyboardBuilder()
    for user in users:
        username = f"@{user.username}" if user.username else user.first_name
        builder.button(text=f"❌ {username}", callback_data=f"delete_user_{user.user_id}")
    builder.button(text="🔙 Orqaga", callback_data="back_to_users_manage")
    builder.adjust(1)
    return builder.as_markup()

# Foydalanuvchini o'chirishni tasdiqlash
def get_user_delete_confirmation_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha, o'chirish", callback_data=f"confirm_delete_user_{user_id}")
    builder.button(text="❌ Yo'q, bekor qilish", callback_data="cancel_delete_user")
    builder.adjust(2)
    return builder.as_markup()