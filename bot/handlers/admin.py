# bot/handlers/admin.py - TO'LIQ TO'G'RILANGAN VERSIYA
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from bot.database.models import get_session, Book, Unit, Question, User
from bot.database.crud import BookCRUD, UnitCRUD, QuestionCRUD, UserCRUD
from bot.keyboards.admin_keyboards import *
from bot.states import AdminStates
import json
import html
import time

class AdminHandlers:
    def __init__(self):
        self.user_data = {}
    
    # ========== TEST TUZISH ==========
    async def admin_create_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test tuzish menyusi"""
        query = update.callback_query
        await query.answer()
        
        db = get_session()
        books = db.query(Book).filter(Book.is_active == True).all()
        db.close()
        
        await query.edit_message_text(
            "📚 <b>Kitob tanlang yoki yangi kitob qo'shing:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=books_keyboard(books)
        )
    
    async def select_book(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Kitob tanlash"""
        query = update.callback_query
        await query.answer()
        
        book_id = int(query.data.replace("book_", ""))
        
        db = get_session()
        book = db.query(Book).filter(Book.id == book_id).first()
        units = db.query(Unit).filter(Unit.book_id == book_id).all()
        db.close()
        
        await query.edit_message_text(
            f"📖 <b>{book.name}</b>\n\nUnitlar ro'yxati:",
            parse_mode=ParseMode.HTML,
            reply_markup=units_keyboard(units, book_id)
        )
    
    async def add_new_book(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Yangi kitob qo'shish"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        self.user_data[user_id] = {"state": AdminStates.WAITING_BOOK_NAME}
        
        await query.edit_message_text(
            "📝 <b>Yangi kitob nomini kiriting:</b>",
            parse_mode=ParseMode.HTML
        )
    
    async def handle_new_book_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Yangi kitob nomini qabul qilish"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_data:
            return
        
        book_name = update.message.text
        
        db = get_session()
        book = BookCRUD.create_book(db, book_name)
        db.close()
        
        del self.user_data[user_id]
        
        await update.message.reply_text(
            f"✅ <b>{book_name}</b> kitobi yaratildi!",
            parse_mode=ParseMode.HTML,
            reply_markup=admin_main_menu()
        )
    
    async def select_unit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Unit tanlash"""
        query = update.callback_query
        await query.answer()
        
        unit_id = int(query.data.replace("unit_", ""))
        
        db = get_session()
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        db.close()
        
        await query.edit_message_text(
            f"📝 <b>{unit.name}</b> uniti\n\nKerakli amalni tanlang:",
            parse_mode=ParseMode.HTML,
            reply_markup=unit_management_keyboard(unit_id, unit.book_id)
        )
    
    async def add_new_unit(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Yangi unit qo'shish"""
        query = update.callback_query
        await query.answer()
        
        book_id = int(query.data.replace("new_unit_", ""))
        user_id = query.from_user.id
        
        self.user_data[user_id] = {
            "state": AdminStates.WAITING_UNIT_NAME,
            "book_id": book_id
        }
        
        await query.edit_message_text(
            "📝 <b>Yangi unit nomini kiriting:</b>",
            parse_mode=ParseMode.HTML
        )
    
    async def handle_new_unit_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Yangi unit nomini qabul qilish"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_data:
            return
        
        data = self.user_data[user_id]
        if data["state"] != AdminStates.WAITING_UNIT_NAME:
            return
        
        unit_name = update.message.text
        book_id = data["book_id"]
        
        db = get_session()
        unit = UnitCRUD.create_unit(db, book_id, unit_name)
        db.close()
        
        del self.user_data[user_id]
        
        await update.message.reply_text(
            f"✅ <b>{unit_name}</b> uniti yaratildi!\n\nEndi savol qo'shishingiz mumkin.",
            parse_mode=ParseMode.HTML,
            reply_markup=unit_management_keyboard(unit.id, book_id)
        )
    
    async def add_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Savol qo'shish"""
        query = update.callback_query
        await query.answer()
        
        unit_id = int(query.data.replace("add_question_", ""))
        user_id = query.from_user.id
        
        self.user_data[user_id] = {
            "state": AdminStates.WAITING_AUDIO,
            "unit_id": unit_id,
            "step": 1
        }
        
        await query.edit_message_text(
            "🎵 <b>Audio faylni yuboring:</b>\n\n"
            "Eslatma: Audio MP3 formatida bo'lishi kerak",
            parse_mode=ParseMode.HTML
        )
    
    async def handle_audio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Audio qabul qilish"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_data:
            return
        
        data = self.user_data[user_id]
        if data["state"] != AdminStates.WAITING_AUDIO:
            return
        
        if not update.message.audio:
            await update.message.reply_text("Iltimos, audio fayl yuboring!")
            return
        
        audio = update.message.audio
        file_id = audio.file_id
        
        data["audio_file_id"] = file_id
        data["state"] = AdminStates.WAITING_QUESTION_TEXT
        data["step"] = 2
        
        await update.message.reply_text(
            "📝 <b>Savol matnini kiriting (ixtiyoriy):</b>\n\n"
            "Agar savol matni kerak bo'lmasa, 'o'tkazib yuborish' deb yozing",
            parse_mode=ParseMode.HTML
        )
    
    async def handle_question_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Savol matnini qabul qilish"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_data:
            return
        
        data = self.user_data[user_id]
        if data["state"] != AdminStates.WAITING_QUESTION_TEXT:
            return
        
        question_text = update.message.text
        
        if question_text.lower() != "o'tkazib yuborish":
            data["question_text"] = question_text
        else:
            data["question_text"] = None
        
        data["state"] = AdminStates.WAITING_OPTIONS
        data["step"] = 3
        
        await update.message.reply_text(
            "📋 <b>Variantlarni kiriting:</b>\n\n"
            "Har bir variant yangi qatorda bo'lsin\n"
            "Masalan:\n"
            "Variant A\n"
            "Variant B\n"
            "Variant C\n"
            "Variant D",
            parse_mode=ParseMode.HTML
        )
    
    async def handle_options(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Variantlarni qabul qilish"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_data:
            return
        
        data = self.user_data[user_id]
        if data["state"] != AdminStates.WAITING_OPTIONS:
            return
        
        options_text = update.message.text
        options = [opt.strip() for opt in options_text.split('\n') if opt.strip()]
        
        if len(options) < 2:
            await update.message.reply_text("Kamida 2 ta variant kiriting!")
            return
        
        data["options"] = options
        data["state"] = AdminStates.WAITING_CORRECT_ANSWER
        data["step"] = 4
        
        options_list = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(options)])
        
        await update.message.reply_text(
            f"✅ <b>Variantlar qabul qilindi:</b>\n\n{options_list}\n\n"
            f"📝 <b>To'g'ri javobni kiriting (variant nomi bilan):</b>",
            parse_mode=ParseMode.HTML
        )
    
    async def handle_correct_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """To'g'ri javobni qabul qilish"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_data:
            return
        
        data = self.user_data[user_id]
        if data["state"] != AdminStates.WAITING_CORRECT_ANSWER:
            return
        
        correct_answer = update.message.text
        
        if correct_answer not in data["options"]:
            await update.message.reply_text(
                "❌ To'g'ri javob variantlar ro'yxatida bo'lishi kerak! "
                "Qaytadan kiriting:"
            )
            return
        
        data["correct_answer"] = correct_answer
        data["state"] = AdminStates.WAITING_EXPLANATION
        data["step"] = 5
        
        await update.message.reply_text(
            "📝 <b>Izoh kiriting (ixtiyoriy):</b>\n\n"
            "Agar izoh kerak bo'lmasa, 'o'tkazib yuborish' deb yozing",
            parse_mode=ParseMode.HTML
        )
    
    async def handle_explanation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Izohni qabul qilish"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_data:
            return
        
        data = self.user_data[user_id]
        if data["state"] != AdminStates.WAITING_EXPLANATION:
            return
        
        explanation = update.message.text
        
        if explanation.lower() != "o'tkazib yuborish":
            data["explanation"] = explanation
        else:
            data["explanation"] = None
        
        db = get_session()
        
        question = QuestionCRUD.create_question(
            db=db,
            unit_id=data["unit_id"],
            audio_file_id=data["audio_file_id"],
            question_text=data.get("question_text"),
            options=data["options"],
            correct_answer=data["correct_answer"],
            explanation=data.get("explanation")
        )
        
        db.close()
        
        await context.bot.send_audio(
            chat_id=update.effective_chat.id,
            audio=data["audio_file_id"],
            caption=f"✅ <b>Savol yaratildi!</b>\n\n"
                   f"📝 Savol: {data.get('question_text', 'Mavjud emas')}\n"
                   f"📋 Variantlar: {', '.join(data['options'])}\n"
                   f"✅ To'g'ri javob: {data['correct_answer']}\n"
                   f"📖 Izoh: {data.get('explanation', 'Mavjud emas')}",
            parse_mode=ParseMode.HTML
        )
        
        del self.user_data[user_id]
        
        await update.message.reply_text(
            "✅ Savol muvaffaqiyatli yaratildi!",
            reply_markup=admin_main_menu()
        )
    
    # ========== TEST YECHISH ==========
    async def admin_take_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin test yechish"""
        query = update.callback_query
        await query.answer()
        
        db = get_session()
        books = db.query(Book).filter(Book.is_active == True).all()
        db.close()
        
        await query.edit_message_text(
            "📚 <b>Test yechish uchun kitob tanlang:</b>",
            parse_mode=ParseMode.HTML,
            reply_markup=books_keyboard(books, with_new=False)
        )
    
    async def start_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Testni boshlash"""
        query = update.callback_query
        await query.answer()
        
        unit_id = int(query.data.replace("start_test_", ""))
        
        db = get_session()
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        questions = db.query(Question).filter(Question.unit_id == unit_id).order_by(Question.order_number).all()
        db.close()
        
        if not questions:
            await query.edit_message_text(
                f"❌ <b>{unit.name}</b> unitida savollar mavjud emas!",
                parse_mode=ParseMode.HTML,
                reply_markup=test_start_keyboard(unit_id)
            )
            return
        
        user_id = query.from_user.id
        context.user_data[f"test_{user_id}"] = {
            "unit_id": unit_id,
            "questions": [q.id for q in questions],
            "current_question": 0,
            "answers": [],
            "score": 0
        }
        
        await self.send_next_question(update, context, user_id)
    
    async def send_next_question(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Keyingi savolni yuborish"""
        test_data = context.user_data.get(f"test_{user_id}")
        
        if not test_data:
            return
        
        current_idx = test_data["current_question"]
        question_ids = test_data["questions"]
        
        if current_idx >= len(question_ids):
            await self.finish_test(update, context, user_id)
            return
        
        db = get_session()
        question = db.query(Question).filter(Question.id == question_ids[current_idx]).first()
        db.close()
        
        if not question:
            return
        
        try:
            await context.bot.send_audio(
                chat_id=update.effective_chat.id if update.message else update.callback_query.message.chat_id,
                audio=question.audio_file_id,
                caption=f"❓ <b>Savol {current_idx + 1}/{len(question_ids)}</b>\n\n"
                       f"{question.question_text or 'Audio tinglang va javobni tanlang:'}",
                parse_mode=ParseMode.HTML
            )
            
            options = question.options
            keyboard = []
            
            for i in range(0, len(options), 2):
                row = []
                for j in range(2):
                    if i + j < len(options):
                        row.append(
                            InlineKeyboardButton(
                                options[i + j],
                                callback_data=f"test_answer_{options[i + j]}"
                            )
                        )
                keyboard.append(row)
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id if update.message else update.callback_query.message.chat_id,
                text="Javobni tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        except Exception as e:
            print(f"Error sending question: {e}")
    
    async def handle_test_answer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Test javobini qabul qilish"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        test_data = context.user_data.get(f"test_{user_id}")
        
        if not test_data:
            return
        
        user_answer = query.data.replace("test_answer_", "")
        current_idx = test_data["current_question"]
        question_ids = test_data["questions"]
        
        db = get_session()
        question = db.query(Question).filter(Question.id == question_ids[current_idx]).first()
        db.close()
        
        if not question:
            return
        
        is_correct = (user_answer == question.correct_answer)
        
        test_data["answers"].append({
            "question_id": question.id,
            "user_answer": user_answer,
            "is_correct": is_correct,
            "correct_answer": question.correct_answer
        })
        
        if is_correct:
            test_data["score"] += 10
        
        result_text = f"✅ <b>To'g'ri!</b>" if is_correct else f"❌ <b>Noto'g'ri!</b>"
        result_text += f"\n\nJavobingiz: {user_answer}"
        
        if not is_correct:
            result_text += f"\nTo'g'ri javob: {question.correct_answer}"
        
        if question.explanation:
            result_text += f"\n\n📖 Izoh: {question.explanation}"
        
        await query.edit_message_text(
            result_text,
            parse_mode=ParseMode.HTML
        )
        
        test_data["current_question"] += 1
        
        import asyncio
        await asyncio.sleep(2)
        
        await self.send_next_question(update, context, user_id)
    
    async def finish_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int):
        """Testni tugatish"""
        test_data = context.user_data.get(f"test_{user_id}")
        
        if not test_data:
            return
        
        total = len(test_data["questions"])
        correct = sum(1 for ans in test_data["answers"] if ans["is_correct"])
        score = test_data["score"]
        
        result_text = f"""
🎉 <b>TEST TUGADI!</b>

📊 <b>Natijangiz:</b>
✅ To'g'ri javoblar: {correct}/{total}
🏆 Ball: {score}
📈 Foiz: {correct/total*100:.1f}%
        """
        
        await context.bot.send_message(
            chat_id=update.effective_chat.id if update.message else update.callback_query.message.chat_id,
            text=result_text,
            parse_mode=ParseMode.HTML,
            reply_markup=after_test_keyboard(is_admin=True)
        )
        
        del context.user_data[f"test_{user_id}"]
    
    # ========== XABAR YUBORISH ==========
    async def admin_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Barcha foydalanuvchilarga xabar yuborish"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        self.user_data[user_id] = {"state": AdminStates.WAITING_BROADCAST_MESSAGE}
        
        await query.edit_message_text(
            "📢 <b>Barcha foydalanuvchilarga yuboriladigan xabarni kiriting:</b>\n\n"
            "Xabar HTML formatda bo'lishi mumkin.",
            parse_mode=ParseMode.HTML
        )
    
    async def handle_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Xabarni yuborish"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_data:
            return
        
        data = self.user_data[user_id]
        if data["state"] != AdminStates.WAITING_BROADCAST_MESSAGE:
            return
        
        message = update.message.text
        
        db = get_session()
        users = db.query(User).filter(User.is_active == True).all()
        db.close()
        
        sent_count = 0
        failed_count = 0
        
        await update.message.reply_text(f"📤 Xabar yuborilmoqda... {len(users)} ta foydalanuvchiga")
        
        for user in users:
            try:
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
                sent_count += 1
            except Exception as e:
                print(f"Xabar yuborishda xato: {e}")
                failed_count += 1
        
        del self.user_data[user_id]
        
        await update.message.reply_text(
            f"✅ <b>Xabar yuborish tugatildi!</b>\n\n"
            f"📤 Yuborildi: {sent_count} ta\n"
            f"❌ Xatolik: {failed_count} ta",
            parse_mode=ParseMode.HTML,
            reply_markup=admin_main_menu()
        )
    
    # ========== FOYDALANUVCHILAR RO'YXATI ==========
    async def admin_users_list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Foydalanuvchilar ro'yxati"""
        query = update.callback_query
        await query.answer()
        
        db = get_session()
        users = db.query(User).order_by(User.registration_date.desc()).all()
        db.close()
        
        if not users:
            await query.edit_message_text(
                "📭 <b>Foydalanuvchilar mavjud emas</b>",
                parse_mode=ParseMode.HTML,
                reply_markup=admin_main_menu()
            )
            return
        
        users_text = "<b>👥 Foydalanuvchilar ro'yxati:</b>\n\n"
        
        for i, user in enumerate(users, 1):
            status = "✅" if user.is_active else "❌"
            admin = "👑" if user.is_admin else ""
            reg_status = "⏳" if user.registration_status == "pending" else "✅" if user.registration_status == "approved" else "❌"
            
            users_text += f"{i}. {status}{admin}{reg_status} "
            users_text += f"{user.first_name or ''} {user.last_name or ''}"
            
            if user.username:
                users_text += f" (@{user.username})"
            
            users_text += f" - ID: {user.telegram_id}\n"
            users_text += f"   📅 {user.registration_date.strftime('%d.%m.%Y')}\n\n"
        
        await query.edit_message_text(
            users_text,
            parse_mode=ParseMode.HTML,
            reply_markup=admin_main_menu()
        )
    
    # ========== UMUMIY NATIJALAR ==========
    async def admin_overall_results(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Umumiy natijalar"""
        query = update.callback_query
        await query.answer()
        
        db = get_session()
        
        # Faol foydalanuvchilar soni
        active_users = db.query(User).filter(User.is_active == True).count()
        
        # Kutilayotgan foydalanuvchilar
        pending_users = db.query(User).filter(User.registration_status == "pending").count()
        
        # Tasdiqlangan foydalanuvchilar
        approved_users = db.query(User).filter(User.registration_status == "approved").count()
        
        # Rad etilgan foydalanuvchilar
        rejected_users = db.query(User).filter(User.registration_status == "rejected").count()
        
        # Kitoblar soni
        books_count = db.query(Book).count()
        
        # Savollar soni
        questions_count = db.query(Question).count()
        
        db.close()
        
        stats_text = f"""
📊 <b>Umumiy statistika:</b>

👥 <b>Foydalanuvchilar:</b>
✅ Faol foydalanuvchilar: {active_users} ta
⏳ Kutilayotgan: {pending_users} ta
✅ Tasdiqlangan: {approved_users} ta
❌ Rad etilgan: {rejected_users} ta

📚 <b>Testlar:</b>
📖 Kitoblar: {books_count} ta
❓ Savollar: {questions_count} ta
        """
        
        await query.edit_message_text(
            stats_text,
            parse_mode=ParseMode.HTML,
            reply_markup=admin_main_menu()
        )
    
    # ========== ASOSIY MENYU ==========
    async def admin_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin asosiy menyuga qaytish"""
        query = update.callback_query
        await query.answer()
        
        await query.edit_message_text(
            "🏠 <b>Admin panel</b>\n\nKerakli bo'limni tanlang:",
            parse_mode=ParseMode.HTML,
            reply_markup=admin_main_menu()
        )
    
    # ========== HANDLE MESSAGES ==========
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Matnli xabarlarni qayta ishlash"""
        user_id = update.effective_user.id
        
        if user_id not in self.user_data:
            return
        
        data = self.user_data[user_id]
        state = data.get("state")
        
        if state == AdminStates.WAITING_BOOK_NAME:
            await self.handle_new_book_name(update, context)
        elif state == AdminStates.WAITING_UNIT_NAME:
            await self.handle_new_unit_name(update, context)
        elif state == AdminStates.WAITING_QUESTION_TEXT:
            await self.handle_question_text(update, context)
        elif state == AdminStates.WAITING_OPTIONS:
            await self.handle_options(update, context)
        elif state == AdminStates.WAITING_CORRECT_ANSWER:
            await self.handle_correct_answer(update, context)
        elif state == AdminStates.WAITING_EXPLANATION:
            await self.handle_explanation(update, context)
        elif state == AdminStates.WAITING_BROADCAST_MESSAGE:
            await self.handle_broadcast(update, context)
    
    # ========== GET HANDLERS ==========
    def get_handlers(self):
        """Barcha admin handlerlarini qaytarish"""
        return [
            # Callback query handlers
            CallbackQueryHandler(self.admin_create_test, pattern="^admin_create_test$"),
            CallbackQueryHandler(self.select_book, pattern="^book_"),
            CallbackQueryHandler(self.add_new_book, pattern="^add_new_book$"),
            CallbackQueryHandler(self.select_unit, pattern="^unit_"),
            CallbackQueryHandler(self.add_new_unit, pattern="^new_unit_"),
            CallbackQueryHandler(self.add_question, pattern="^add_question_"),
            CallbackQueryHandler(self.admin_take_test, pattern="^admin_take_test$"),
            CallbackQueryHandler(self.start_test, pattern="^start_test_"),
            CallbackQueryHandler(self.handle_test_answer, pattern="^test_answer_"),
            CallbackQueryHandler(self.admin_broadcast, pattern="^admin_broadcast$"),
            CallbackQueryHandler(self.admin_users_list, pattern="^admin_users_list$"),
            CallbackQueryHandler(self.admin_overall_results, pattern="^admin_overall_results$"),
            CallbackQueryHandler(self.admin_main_menu, pattern="^admin_main_menu$"),
            
            # Message handlers
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message),
            MessageHandler(filters.AUDIO, self.handle_audio),
        ]