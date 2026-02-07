# keyboards.py
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from database import Book, Unit

def get_admin_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📝 Test tuzish"))
    builder.add(KeyboardButton(text="🧪 Test yechish"))
    builder.add(KeyboardButton(text="🔄 Test formatlash"))
    builder.add(KeyboardButton(text="🗑️ Testni o'chirish"))
    builder.add(KeyboardButton(text="👥 Foydalanuvchilar ro'yxati"))
    builder.add(KeyboardButton(text="❌ Foydalanuvchilarni o'chirish"))
    builder.add(KeyboardButton(text="📢 Xabar yuborish"))
    builder.add(KeyboardButton(text="📊 Umumiy natijalar"))
    builder.add(KeyboardButton(text="🏆 Foydalanuvchilar reytingi"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_user_main_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🚀 Test boshlash"))
    builder.add(KeyboardButton(text="📊 Mening natijalarim"))
    builder.add(KeyboardButton(text="🏆 Reyting"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_test_creation_menu():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="📚 Mavjud kitoblar"))
    builder.add(KeyboardButton(text="➕ Yangi kitob qo'shish"))
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def get_back_keyboard():
    """Orqaga qaytish uchun keyboard"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="⬅️ Orqaga"))
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)    

def get_books_keyboard(books, action="select"):
    builder = InlineKeyboardBuilder()
    for book in books:
        builder.add(InlineKeyboardButton(
            text=book.name,
            callback_data=f"{action}_book_{book.id}"
        ))
    builder.add(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"))
    builder.adjust(1)
    return builder.as_markup()

def get_books_management_keyboard(books):
    """Kitoblarni boshqarish uchun keyboard"""
    builder = InlineKeyboardBuilder()
    
    for book in books:
        builder.add(InlineKeyboardButton(
            text=f"📖 {book.name}",
            callback_data=f"manage_book_{book.id}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="➕ Yangi kitob yaratish",
        callback_data="create_new_book"
    ))
    
    builder.add(InlineKeyboardButton(
        text="❌ Bekor qilish",
        callback_data="cancel"
    ))
    
    builder.adjust(1)
    return builder.as_markup()    

def get_units_keyboard(units, action="select"):
    builder = InlineKeyboardBuilder()
    for unit in units:
        builder.add(InlineKeyboardButton(
            text=unit.name,
            callback_data=f"{action}_unit_{unit.id}"
        ))
    builder.add(InlineKeyboardButton(text="➕ Yangi unit", callback_data="add_new_unit"))
    builder.add(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"))
    builder.adjust(1)
    return builder.as_markup()

def get_units_management_keyboard(units, book_id):
    """Unitlarni boshqarish uchun keyboard"""
    builder = InlineKeyboardBuilder()
    
    for unit in units:
        builder.add(InlineKeyboardButton(
            text=f"📄 {unit.name}",
            callback_data=f"manage_unit_{unit.id}"
        ))
    
    builder.add(InlineKeyboardButton(
        text="➕ Yangi unit qo'shish",
        callback_data=f"add_unit_to_{book_id}"
    ))
    
    builder.add(InlineKeyboardButton(
        text="⬅️ Kitoblarga qaytish",
        callback_data="back_to_books"
    ))
    
    builder.adjust(1)
    return builder.as_markup()

def get_unit_actions_keyboard(unit_id):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="➕ Savol qo'shish",
        callback_data=f"add_question_{unit_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="📋 Savollar ro'yxati",
        callback_data=f"view_questions_{unit_id}"
    ))
    builder.add(InlineKeyboardButton(text="⬅️ Orqaga", callback_data="back_to_units"))
    builder.adjust(1)
    return builder.as_markup()

def get_cancel_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Bekor qilish"))
    return builder.as_markup(resize_keyboard=True)

def get_test_options(options):
    builder = InlineKeyboardBuilder()
    for i, option in enumerate(options, 1):  # 1 dan boshlash
        builder.add(InlineKeyboardButton(
            text=f"{i}. {option}",
            callback_data=f"answer_{i-1}"  # 0-based index
        ))
    builder.adjust(2)
    return builder.as_markup()

def get_approve_keyboard(user_id):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="✅ Ruxsat berish",
        callback_data=f"approve_user_{user_id}"
    ))
    builder.add(InlineKeyboardButton(
        text="❌ Rad etish",
        callback_data=f"reject_user_{user_id}"
    ))
    return builder.as_markup()

def get_yes_no_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="✅ Ha"))
    builder.add(KeyboardButton(text="❌ Yo'q"))
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

 

# keyboards.py - yangi funksiyalar qo'shamiz
def get_books_keyboard_for_users(books):
    """Foydalanuvchilar uchun kitoblar keyboard"""
    builder = InlineKeyboardBuilder()
    for book in books:
        builder.add(InlineKeyboardButton(
            text=book.name,
            callback_data=f"select_user_book_{book.id}"
        ))
    builder.add(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"))
    builder.adjust(1)
    return builder.as_markup()

def get_units_keyboard_for_users(units):
    """Foydalanuvchilar uchun unitlar keyboard (Yangi unit qo'shish tugmasi O'CHIRILADI)"""
    builder = InlineKeyboardBuilder()
    for unit in units:
        builder.add(InlineKeyboardButton(
            text=unit.name,
            callback_data=f"select_user_unit_{unit.id}"
        ))
    builder.add(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"))
    builder.adjust(1)
    return builder.as_markup()

def get_units_keyboard_for_admin(units):
    """Admin uchun unitlar keyboard (Yangi unit qo'shish tugmasi bor)"""
    builder = InlineKeyboardBuilder()
    for unit in units:
        builder.add(InlineKeyboardButton(
            text=unit.name,
            callback_data=f"manage_unit_{unit.id}"
        ))
    builder.add(InlineKeyboardButton(text="➕ Yangi unit", callback_data="add_new_unit"))
    builder.add(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel"))
    builder.adjust(1)
    return builder.as_markup()  

# keyboards.py ga qo'shing:
def get_broadcast_keyboard():
    """Xabar yuborish uchun keyboard"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="confirm_broadcast"))
    builder.add(InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast"))
    builder.adjust(2)
    return builder.as_markup()        