# bot/main.py - soddalashtirilgan versiya
import os
import logging
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from telegram import Update

# Handlers import
from bot.handlers.common import start_command
from bot.handlers.admin import AdminHandlers
from bot.handlers.user import UserHandlers
from bot.handlers.registration import RegistrationHandler
from bot.database.models import init_db

# Load environment variables
load_dotenv()

# Logging sozlamalari
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def main():
    """Asosiy funksiya - botni ishga tushirish"""
    
    # Bot tokenini olish
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN environment variable topilmadi!")
    
    # Database yaratish
    init_db()
    
    # Application yaratish
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    
    # Registration handlers (birinchi bo'lsin, chunki /start dan keyin ishlaydi)
    registration_handler = RegistrationHandler()
    for handler in registration_handler.get_handlers():
        application.add_handler(handler)
    
    # Admin handlers
    admin_handlers = AdminHandlers()
    for handler in admin_handlers.get_handlers():
        application.add_handler(handler)
    
    # User handlers
    user_handlers = UserHandlers()
    for handler in user_handlers.get_handlers():
        application.add_handler(handler)
    
    # Xatolik handler
    async def error_handler(update, context):
        logger.error(f"Xato yuz berdi: {context.error}")
    
    application.add_error_handler(error_handler)
    
    # Botni ishga tushirish
    PORT = int(os.getenv('PORT', 8000))
    ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
    
    if ENVIRONMENT == 'production':
        # Production - Webhook
        WEBHOOK_URL = os.getenv('WEBHOOK_URL')
        if not WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL environment variable topilmadi!")
        
        webhook_url = f"{WEBHOOK_URL}/{BOT_TOKEN}"
        
        async def startup():
            await application.bot.setWebhook(webhook_url)
            logger.info(f"Webhook o'rnatildi: {webhook_url}")
        
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=webhook_url,
            on_startup=startup
        )
    else:
        # Development - Polling
        logger.info("Bot polling rejimida ishga tushdi...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()