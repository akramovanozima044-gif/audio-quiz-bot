# bot/keyboards/user_keyboards.py
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def user_main_menu():
    """User asosiy menyu"""
    keyboard = [
        [InlineKeyboardButton("📝 Test yechish", callback_data="user_take_test")],
        [InlineKeyboardButton("📊 Mening natijalarim", callback_data="user_my_results")],
        [InlineKeyboardButton("ℹ️ Yordam", callback_data="user_help")],
    ]
    return InlineKeyboardMarkup(keyboard)

def user_books_keyboard(books):
    """User uchun kitoblar keyboard"""
    keyboard = []
    for book in books:
        keyboard.append([InlineKeyboardButton(f"📚 {book.name}", callback_data=f"user_book_{book.id}")])
    
    keyboard.append([InlineKeyboardButton("↩️ Orqaga", callback_data="user_main_menu")])
    return InlineKeyboardMarkup(keyboard)

def user_units_keyboard(units):
    """User uchun unitlar keyboard"""
    keyboard = []
    for unit in units:
        keyboard.append([InlineKeyboardButton(f"📖 {unit.name}", callback_data=f"user_unit_{unit.id}")])
    
    keyboard.append([InlineKeyboardButton("↩️ Orqaga", callback_data="user_back_to_books")])
    return InlineKeyboardMarkup(keyboard)