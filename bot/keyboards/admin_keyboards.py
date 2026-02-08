# bot/keyboards/admin_keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def admin_main_menu():
    """Admin asosiy menyu"""
    keyboard = [
        [InlineKeyboardButton("📝 Test tuzish", callback_data="admin_create_test")],
        [InlineKeyboardButton("📊 Test yechish", callback_data="admin_take_test")],
        [InlineKeyboardButton("🗑️ Test formatlash/o'chirish", callback_data="admin_manage_tests")],
        [InlineKeyboardButton("👥 Foydalanuvchilar ro'yxati", callback_data="admin_users_list")],
        [InlineKeyboardButton("📢 Xabar yuborish", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📈 Umumiy natijalar", callback_data="admin_overall_results")],
    ]
    return InlineKeyboardMarkup(keyboard)

def books_keyboard(books, with_new=True):
    """Kitoblar keyboard"""
    keyboard = []
    for book in books:
        keyboard.append([InlineKeyboardButton(f"📚 {book.name}", callback_data=f"book_{book.id}")])
    
    if with_new:
        keyboard.append([InlineKeyboardButton("➕ Yangi kitob qo'shish", callback_data="add_new_book")])
    
    keyboard.append([InlineKeyboardButton("↩️ Orqaga", callback_data="admin_main_menu")])
    return InlineKeyboardMarkup(keyboard)

def units_keyboard(units, book_id, with_new=True):
    """Unitlar keyboard"""
    keyboard = []
    for unit in units:
        keyboard.append([InlineKeyboardButton(f"📖 {unit.name}", callback_data=f"unit_{unit.id}")])
    
    if with_new:
        keyboard.append([InlineKeyboardButton("➕ Yangi unit", callback_data=f"new_unit_{book_id}")])
    
    keyboard.append([InlineKeyboardButton("↩️ Orqaga", callback_data=f"back_to_books")])
    return InlineKeyboardMarkup(keyboard)

def question_management_keyboard(question_id, unit_id):
    """Savol boshqarish keyboard"""
    keyboard = [
        [InlineKeyboardButton("✏️ Nomini o'zgartirish", callback_data=f"edit_question_{question_id}")],
        [InlineKeyboardButton("🗑️ O'chirish", callback_data=f"delete_question_{question_id}")],
        [InlineKeyboardButton("↩️ Orqaga", callback_data=f"back_to_unit_{unit_id}")],
    ]
    return InlineKeyboardMarkup(keyboard)

def unit_management_keyboard(unit_id, book_id):
    """Unit boshqarish keyboard"""
    keyboard = [
        [InlineKeyboardButton("✏️ Nomini o'zgartirish", callback_data=f"edit_unit_{unit_id}")],
        [InlineKeyboardButton("🗑️ O'chirish", callback_data=f"delete_unit_{unit_id}")],
        [InlineKeyboardButton("➕ Savol qo'shish", callback_data=f"add_question_{unit_id}")],
        [InlineKeyboardButton("📋 Savollar ro'yxati", callback_data=f"list_questions_{unit_id}")],
        [InlineKeyboardButton("↩️ Orqaga", callback_data=f"back_to_book_{book_id}")],
    ]
    return InlineKeyboardMarkup(keyboard)

def book_management_keyboard(book_id):
    """Kitob boshqarish keyboard"""
    keyboard = [
        [InlineKeyboardButton("✏️ Nomini o'zgartirish", callback_data=f"edit_book_{book_id}")],
        [InlineKeyboardButton("🗑️ O'chirish", callback_data=f"delete_book_{book_id}")],
        [InlineKeyboardButton("📖 Unitlar", callback_data=f"book_units_{book_id}")],
        [InlineKeyboardButton("↩️ Orqaga", callback_data="admin_manage_tests")],
    ]
    return InlineKeyboardMarkup(keyboard)

def confirm_keyboard(action, data_id):
    """Tasdiqlash keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Ha", callback_data=f"confirm_{action}_{data_id}"),
            InlineKeyboardButton("❌ Yo'q", callback_data=f"cancel_{action}_{data_id}")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def user_management_keyboard(user_id):
    """Foydalanuvchi boshqarish keyboard"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Aktivlashtirish", callback_data=f"activate_user_{user_id}"),
            InlineKeyboardButton("❌ Bloklash", callback_data=f"deactivate_user_{user_id}")
        ],
        [InlineKeyboardButton("🗑️ O'chirish", callback_data=f"delete_user_{user_id}")],
        [InlineKeyboardButton("↩️ Orqaga", callback_data="admin_users_list")],
    ]
    return InlineKeyboardMarkup(keyboard)

def test_start_keyboard(unit_id):
    """Test boshlash keyboard"""
    keyboard = [
        [InlineKeyboardButton("✅ Testni boshlash", callback_data=f"start_test_{unit_id}")],
        [InlineKeyboardButton("↩️ Orqaga", callback_data="back_to_units")],
    ]
    return InlineKeyboardMarkup(keyboard)

def after_test_keyboard(is_admin=True):
    """Test tugagach keyboard"""
    menu = "admin_main_menu" if is_admin else "user_main_menu"
    keyboard = [
        [InlineKeyboardButton("🔄 Testni qayta boshlash", callback_data="restart_test")],
        [InlineKeyboardButton("🏠 Menyuga qaytish", callback_data=menu)],
    ]
    return InlineKeyboardMarkup(keyboard)