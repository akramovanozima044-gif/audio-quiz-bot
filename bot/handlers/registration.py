# bot/handlers/registration.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.constants import ParseMode
from bot.database.models import get_session
from bot.database.crud import UserCRUD
import html

class RegistrationHandler:
    def __init__(self):
        pass
    
    async def start_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User ro'yxatdan o'tishni boshlash"""
        user = update.effective_user
        
        # Database tekshirish
        db = get_session()
        existing_user = UserCRUD.get_user_by_telegram_id(db, user.id)
        
        if existing_user:
            db.close()
            if existing_user.is_active:
                await update.message.reply_text(
                    "✅ Siz allaqachon ro'yxatdan o'tgansiz va botdan foydalana olasiz!\n"
                    "Botni qayta ishga tushirish uchun /start bosing."
                )
            elif existing_user.registration_status == "pending":
                await update.message.reply_text(
                    "⏳ Sizning arizangiz admin tomonidan ko'rib chiqilmoqda.\n"
                    "Tasdiqlangandan so'ng sizga xabar beramiz."
                )
            elif existing_user.registration_status == "rejected":
                reason = existing_user.rejection_reason or "Ko'rsatilmagan"
                await update.message.reply_text(
                    f"❌ Sizning arizangiz rad etilgan.\n"
                    f"Sabab: {reason}\n\n"
                    f"Agar bu xato deb o'ylasangiz, admin bilan bog'laning."
                )
            return
        
        # Yangi user yaratish
        user_data = UserCRUD.create_pending_user(
            db=db,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        db.close()
        
        # Adminlarga bildirishnoma yuborish
        await self.notify_admins(update, context, user_data)
        
        # Userga tasdiqlash haqida xabar
        await update.message.reply_text(
            "✅ *Arizangiz qabul qilindi!*\n\n"
            "Admin tomonidan tekshirilgach, sizga xabar beramiz.\n"
            "Tasdiqlangandan so'ng /start buyrug'i orqali botdan foydalana olasiz.\n\n"
            "⏳ *Iltimos, kuting...*",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def notify_admins(self, update: Update, context: ContextTypes.DEFAULT_TYPE, user):
        """Adminlarga yangi ariza haqida xabar yuborish"""
        from bot.database.models import User
        
        db = get_session()
        admins = db.query(User).filter(User.is_admin == True, User.is_active == True).all()
        db.close()
        
        # Escape qilish
        first_name = html.escape(user.first_name or '')
        last_name = html.escape(user.last_name or '')
        username = user.username or 'Yoq'
        
        user_info = (
            f"👤 *Yangi foydalanuvchi ariza yubordi:*\n\n"
            f"🆔 ID: `{user.telegram_id}`\n"
            f"👤 Ism: {first_name}\n"
            f"📛 Familiya: {last_name}\n"
            f"📱 Username: @{username}\n"
            f"📅 Sana: {user.registration_date.strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Arizani tasdiqlaysizmi?"
        )
        
        keyboard = [
            [
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_user_{user.id}"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_user_{user.id}")
            ],
            [InlineKeyboardButton("👁️ Profilni ko'rish", callback_data=f"view_user_{user.id}")]
        ]
        
        for admin in admins:
            try:
                await context.bot.send_message(
                    chat_id=admin.telegram_id,
                    text=user_info,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            except Exception as e:
                print(f"Adminga xabar yuborishda xato: {e}")
    
    # Admin handlerlari
    async def approve_user_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin user ni tasdiqlash"""
        query = update.callback_query
        await query.answer()
        
        admin_id = query.from_user.id
        user_id = int(query.data.replace("approve_user_", ""))
        
        db = get_session()
        
        # Admin ekanligini tekshirish
        admin = UserCRUD.get_user_by_telegram_id(db, admin_id)
        if not admin or not admin.is_admin:
            await query.edit_message_text(
                "❌ Sizda bu amalni bajarish uchun ruxsat yo'q!",
                parse_mode=ParseMode.MARKDOWN
            )
            db.close()
            return
        
        # Userni tasdiqlash
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await query.edit_message_text(
                "❌ Foydalanuvchi topilmadi!",
                parse_mode=ParseMode.MARKDOWN
            )
            db.close()
            return
        
        # Tasdiqlash
        from bot.database.crud import UserCRUD
        UserCRUD.approve_user(db, user_id, admin_id)
        
        # Userga xabar yuborish
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text="🎉 *Tabriklaymiz!*\n\n"
                     "Sizning arizangiz tasdiqlandi. Endi botdan to'liq foydalana olasiz!\n\n"
                     "Botni ishga tushirish uchun /start bosing.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            print(f"Userga xabar yuborishda xato: {e}")
        
        # Admin ga javob
        await query.edit_message_text(
            f"✅ *{user.first_name} @{user.username}* foydalanuvchisi tasdiqlandi!\n\n"
            f"📅 Tasdiqlangan sana: {user.approved_at.strftime('%Y-%m-%d %H:%M')}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        db.close()
    
    async def reject_user_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Admin user ni rad etish"""
        query = update.callback_query
        await query.answer()
        
        admin_id = query.from_user.id
        user_id = int(query.data.replace("reject_user_", ""))
        
        # Rad etish sababini so'rash
        context.user_data[f"reject_reason_{user_id}"] = {"admin_id": admin_id, "query": query}
        
        await query.edit_message_text(
            "❌ *Foydalanuvchini rad etish*\n\n"
            "Rad etish sababini kiriting:",
            parse_mode=ParseMode.MARKDOWN
        )
    
    async def handle_reject_reason(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Rad etish sababini qabul qilish"""
        user_id = None
        for key in context.user_data:
            if key.startswith("reject_reason_"):
                user_id = int(key.replace("reject_reason_", ""))
                break
        
        if not user_id:
            return
        
        reason = update.message.text
        data = context.user_data.get(f"reject_reason_{user_id}")
        
        if not data:
            return
        
        admin_id = data["admin_id"]
        query = data["query"]
        
        db = get_session()
        
        # Admin ekanligini tekshirish
        admin = UserCRUD.get_user_by_telegram_id(db, admin_id)
        if not admin or not admin.is_admin:
            await update.message.reply_text(
                "❌ Sizda bu amalni bajarish uchun ruxsat yo'q!",
                parse_mode=ParseMode.MARKDOWN
            )
            db.close()
            return
        
        # Userni rad etish
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await update.message.reply_text(
                "❌ Foydalanuvchi topilmadi!",
                parse_mode=ParseMode.MARKDOWN
            )
            db.close()
            return
        
        # Rad etish
        from bot.database.crud import UserCRUD
        UserCRUD.reject_user(db, user_id, reason)
        
        # Userga xabar yuborish
        try:
            await context.bot.send_message(
                chat_id=user.telegram_id,
                text="❌ *Arizangiz rad etildi*\n\n"
                     f"Sabab: {reason}\n\n"
                     "Agar bu xato deb o'ylasangiz, admin bilan bog'laning.",
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            print(f"Userga xabar yuborishda xato: {e}")
        
        # Admin ga javob
        await query.edit_message_text(
            f"❌ *{user.first_name} @{user.username}* foydalanuvchisi rad etildi.\n\n"
            f"📝 Sabab: {reason}",
            parse_mode=ParseMode.MARKDOWN
        )
        
        # Holatni tozalash
        del context.user_data[f"reject_reason_{user_id}"]
        db.close()
    
    async def view_user_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """User profilini ko'rish"""
        query = update.callback_query
        await query.answer()
        
        user_id = int(query.data.replace("view_user_", ""))
        
        db = get_session()
        user = db.query(User).filter(User.id == user_id).first()
        db.close()
        
        if not user:
            await query.edit_message_text(
                "❌ Foydalanuvchi topilmadi!",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        status_emoji = {
            "pending": "⏳",
            "approved": "✅",
            "rejected": "❌"
        }
        
        user_info = (
            f"👤 *Foydalanuvchi profili:*\n\n"
            f"{status_emoji.get(user.registration_status, '❓')} *Holat:* {user.registration_status}\n"
            f"🆔 Telegram ID: `{user.telegram_id}`\n"
            f"👤 Ism: {html.escape(user.first_name or '')}\n"
            f"📛 Familiya: {html.escape(user.last_name or '')}\n"
            f"📱 Username: @{user.username or 'Yoq'}\n"
            f"📅 Ro'yxatdan o'tgan: {user.registration_date.strftime('%Y-%m-%d %H:%M')}\n"
        )
        
        if user.approved_at:
            user_info += f"✅ Tasdiqlangan: {user.approved_at.strftime('%Y-%m-%d %H:%M')}\n"
        
        if user.rejection_reason:
            user_info += f"❌ Rad etish sababi: {user.rejection_reason}\n"
        
        keyboard = []
        if user.registration_status == "pending":
            keyboard.append([
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_user_{user.id}"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_user_{user.id}")
            ])
        
        keyboard.append([InlineKeyboardButton("↩️ Orqaga", callback_data="admin_users_list")])
        
        await query.edit_message_text(
            user_info,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    def get_handlers(self):
        """Barcha registration handlerlarini qaytarish"""
        return [
            CallbackQueryHandler(self.approve_user_callback, pattern="^approve_user_"),
            CallbackQueryHandler(self.reject_user_callback, pattern="^reject_user_"),
            CallbackQueryHandler(self.view_user_profile, pattern="^view_user_"),
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_reject_reason),
        ]