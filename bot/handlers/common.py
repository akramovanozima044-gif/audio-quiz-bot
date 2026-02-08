# bot/handlers/common.py
import os
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from bot.database.models import get_session, User
from bot.database.crud import UserCRUD
from bot.keyboards.admin_keyboards import admin_main_menu
from bot.keyboards.user_keyboards import user_main_menu
from bot.handlers.registration import RegistrationHandler

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi"""
    user_id = update.effective_user.id
    
    db = get_session()
    user = UserCRUD.get_user_by_telegram_id(db, user_id)
    
    if not user:
        # Ro'yxatdan o'tmagan - avtomatik ro'yxatdan o'tkazamiz
        db.close()
        registration_handler = RegistrationHandler()
        await registration_handler.start_registration(update, context)
        return
    
    # User borligini tekshirish
    if user.is_admin and user.is_active:
        # Admin
        await update.message.reply_text(
            "👑 *Admin panel* ga xush kelibsiz!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=admin_main_menu()
        )
    elif user.is_active and user.registration_status == "approved":
        # Faol user
        await update.message.reply_text(
            "👋 *Audio Quiz Bot* ga xush kelibsiz!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=user_main_menu()
        )
    elif user.registration_status == "pending":
        # Kutilayotgan user
        await update.message.reply_text(
            "⏳ *Sizning arizangiz admin tomonidan ko'rib chiqilmoqda.*\n\n"
            "Tasdiqlangandan so'ng sizga xabar beramiz.\n"
            "Iltimos, biroz kuting...",
            parse_mode=ParseMode.MARKDOWN
        )
    elif user.registration_status == "rejected":
        # Rad etilgan user
        reason = user.rejection_reason or "Ko'rsatilmagan"
        await update.message.reply_text(
            f"❌ *Sizning arizangiz rad etilgan.*\n\n"
            f"Sabab: {reason}\n\n"
            f"Agar bu xato deb o'ylasangiz, admin bilan bog'laning.",
            parse_mode=ParseMode.MARKDOWN
        )
    
    db.close()