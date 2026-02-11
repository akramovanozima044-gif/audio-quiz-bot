from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# ---------- ASOSIY MENYULAR ----------

def admin_main_menu():
    """Admin asosiy menyusi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Test tuzish")],
            [KeyboardButton(text="🧪 Test yechish")],
            [KeyboardButton(text="🗑️ Test formatlash/o'chirish")],
            [KeyboardButton(text="👥 Foydalanuvchilar ro'yxati")],
            [KeyboardButton(text="📢 Habar yuborish")],
            [KeyboardButton(text="📊 Umumiy natijalar")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

def user_main_menu():
    """Foydalanuvchi asosiy menyusi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🧪 Test yechish")],
            [KeyboardButton(text="📊 Mening natijalarim")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )

# ---------- INLINE TUGMALAR ----------

def request_access_keyboard(user_id: int):
    """Ruxsat so'rash tugmasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Ruxsat so'rash",
                    callback_data=f"request_access_{user_id}"
                )
            ]
        ]
    )

def user_approval_keyboard(user_id: int):
    """Foydalanuvchini tasdiqlash tugmalari"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Ruxsat berish", callback_data=f"approve_{user_id}"),
                InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{user_id}")
            ]
        ]
    )

def test_creation_menu():
    """Test yaratish menyusi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📚 Mavjud kitoblar", callback_data="existing_books")],
            [InlineKeyboardButton(text="➕ Yangi kitob qo'shish", callback_data="add_new_book")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin_menu")]
        ]
    )

def back_to_admin_menu_keyboard():
    """Admin menyusiga qaytish"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Admin menyusi", callback_data="back_to_admin_menu")]
        ]
    )

# ---------- TEST ISHLASH TUGMALARI ----------

def start_test_keyboard():
    """Testni boshlash tugmasi"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Testni boshlash", callback_data="start_test")],
            [InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_menu")]
        ]
    )

def next_question_keyboard():
    """Keyingi savol uchun tugma"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➡️ Keyingi savol", callback_data="next_question")]
        ]
    )

def test_completed_keyboard():
    """Test tugagandan so'ng menyu"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Testni qayta boshlash", callback_data="restart_test")],
            [InlineKeyboardButton(text="🏠 Asosiy menyu", callback_data="main_menu")]
        ]
    )

# ---------- KITOB VA UNIT TANLASH ----------

def books_list_keyboard(books):
    """Kitoblar ro'yxati"""
    buttons = []
    for book in books:
        buttons.append([InlineKeyboardButton(text=book.name, callback_data=f"book_{book.id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_test_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def units_list_keyboard(units):
    """Unitlar ro'yxati"""
    buttons = []
    for unit in units:
        buttons.append([InlineKeyboardButton(text=unit.name, callback_data=f"unit_{unit.id}")])
    buttons.append([InlineKeyboardButton(text="➕ Yangi unit", callback_data="add_new_unit")])
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_books")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)