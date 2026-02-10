# config.py - Railway uchun optimallashtirilgan
import os
import logging

logger = logging.getLogger(__name__)

class Config:
    # Environment variables - Railway to'g'ridan-to'g'ri beradi
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # PORT - Railway avtomatik beradi
    PORT = int(os.getenv("PORT", "8000"))
    
    # Webhook URL (agar ishlatilsa)
    RAILWAY_STATIC_URL = os.getenv("RAILWAY_STATIC_URL", "")
    
    @classmethod
    def validate_all(cls):
        """Barcha sozlamalarni tekshirish"""
        errors = []
        
        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN is not set")
        
        if not cls.ADMIN_ID or cls.ADMIN_ID <= 0:
            errors.append("ADMIN_ID is not valid")
        
        if not cls.DATABASE_URL:
            logger.warning("DATABASE_URL is not set - Railway will provide it automatically")
        
        if errors:
            for error in errors:
                logger.error(f"Config error: {error}")
            return False
        
        logger.info("✅ All configurations are valid")
        logger.info(f"📊 Config: BOT_TOKEN={'Set' if cls.BOT_TOKEN else 'Not set'}")
        logger.info(f"📊 Config: ADMIN_ID={cls.ADMIN_ID}")
        logger.info(f"📊 Config: PORT={cls.PORT}")
        logger.info(f"📊 Config: DATABASE_URL={'Set' if cls.DATABASE_URL else 'Not set'}")
        
        return True

config = Config()