# bot/handlers/user.py
from telegram import Update
from telegram.ext import ContextTypes, CallbackQueryHandler
from telegram.constants import ParseMode
from bot.database.models import get_session, Book, Unit, Question, User
from bot.database.crud import UserCRUD
from bot.keyboards.user_keyboards import *
from bot.keyboards.admin_keyboards import test_start_keyboard, after_test_keyboard

class UserHandlers:
    def __init__(self):
        pass
    
    async def user_take_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User test yechish"""
        query = update.callback_query
        await query.answer()
        
        db = get_session()
        books = db.query(Book).filter(Book.is_active == True).all()
        db.close()
        
        await query.edit_message_text(
            "📚 <b>Test yechish uchun kitob tanlang:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=user_books_keyboard(books)
        )
    
    async def user_select_book(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User kitob tanlash"""
        query = update.callback_query
        await query.answer()
        
        book_id = int(query.data.replace("user_book_", ""))
        
        db = get_session()
        book = db.query(Book).filter(Book.id == book_id).first()
        units = db.query(Unit).filter(Unit.book_id == book_id).all()
        db.close()
        
        await query.edit_message_text(
            f"📖 <b>{book.name}</b>\n\nUnitlar ro'yxati:",
            parse_mode=ParseMode.HTML,
            reply_markup=user_units_keyboard(units)
        )
    
    async def user_select_unit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User unit tanlash"""
        query = update.callback_query
        await query.answer()
        
        unit_id = int(query.data.replace("user_unit_", ""))
        
        db = get_session()
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        questions_count = db.query(Question).filter(Question.unit_id == unit_id).count()
        db.close()
        
        await query.edit_message_text(
            f"📝 <b>{unit.name}</b>\n\n"
            f"Savollar soni: {questions_count}\n\n"
            f"Testni boshlashga tayyormisiz?",
            parse_mode=ParseMode.HTML,
            reply_markup=test_start_keyboard(unit_id)
        )
    
    async def user_my_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User natijalari"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        db = get_session()
        user = db.query(User).filter(User.telegram_id == user_id).first()
        
        # Bu yerda user natijalarini olish logikasi
        # Hozircha oddiy xabar
        
        db.close()
        
        await query.edit_message_text(
            "📊 <b>Mening natijalarim</b>\n\n"
            "Bu bo'lim hozircha ishlab chiqilmoqda...",
            parse_mode=ParseMode.HTML,
            reply_markup=user_main_menu()
        )
    
    async def user_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User yordam"""
        query = update.callback_query
        await query.answer()
        
        help_text = """
<b>📚 Botdan foydalanish:</b>

1. <b>Test yechish</b> - Audio savollarga javob bering
2. <b>Mening natijalarim</b> - O'z natijalaringizni ko'ring
3. <b>Yordam</b> - Qo'llanma

<b>📞 Aloqa:</b>
Savollar bo'lsa admin bilan bog'laning.
        """
        
        await query.edit_message_text(
            help_text,
            parse_mode=ParseMode.HTML,
            reply_markup=user_main_menu()
        )
    
    async def user_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User asosiy menyuga qaytish"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "🏠 <b>Asosiy menyu</b>\n\nKerakli bo'limni tanlang:",
            parse_mode=ParseMode.HTML,
            reply_markup=user_main_menu()
        )
    
    def get_handlers(self):
        """Barcha user handlerlarini qaytarish"""
        return [
            CallbackQueryHandler(self.user_take_test, pattern="^user_take_test$"),
            CallbackQueryHandler(self.user_select_book, pattern="^user_book_"),
            CallbackQueryHandler(self.user_select_unit, pattern="^user_unit_"),
            CallbackQueryHandler(self.user_my_results, pattern="^user_my_results$"),
            CallbackQueryHandler(self.user_help, pattern="^user_help$"),
            CallbackQueryHandler(self.user_main_menu, pattern="^user_main_menu$"),
            CallbackQueryHandler(self.user_main_menu, pattern="^user_back_to_books$"),
        ]

    def get_handlers(self):
        """Barcha user handlerlarini qaytarish"""
        return [
            CallbackQueryHandler(self.user_take_test, pattern="^user_take_test$"),
            CallbackQueryHandler(self.user_select_book, pattern="^user_book_"),
            CallbackQueryHandler(self.user_select_unit, pattern="^user_unit_"),
            CallbackQueryHandler(self.user_my_results, pattern="^user_my_results$"),
            CallbackQueryHandler(self.user_help, pattern="^user_help$"),
            CallbackQueryHandler(self.user_main_menu, pattern="^user_main_menu$"),
            CallbackQueryHandler(self.user_main_menu, pattern="^user_back_to_books$"),
        ]     