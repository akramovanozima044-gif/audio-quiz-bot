# config.py - Tuzatilgan Railway uchun
import os

class Config:
    # Environment variables - Railway to'g'ridan-to'g'ri beradi
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = os.getenv("ADMIN_ID")
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # PORT - Railway avtomatik beradi, int ga o'tkazamiz
    PORT = int(os.getenv("PORT", "8000"))
    
    # Webhook URL (agar ishlatilsa)
    RAILWAY_PUBLIC_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN")
    
    # Token validation
    @classmethod
    def validate_token(cls):
        if not cls.BOT_TOKEN:
            print("❌ ERROR: BOT_TOKEN is not set in Railway Variables!")
            print("Please add BOT_TOKEN in Railway dashboard")
            return False
        
        # Token format tekshirish (soddalashtirilgan)
        if not cls.BOT_TOKEN or ':' not in cls.BOT_TOKEN:
            print(f"❌ ERROR: Invalid token format!")
            print("Token should be like: 1234567890:AAHhDkjsdfjkKJHSDFJKHSDFjk")
            return False
        
        print(f"✅ Bot token is set")
        return True
    
    @classmethod
    def validate_admin_id(cls):
        if not cls.ADMIN_ID:
            print("⚠️ WARNING: ADMIN_ID is not set in Railway Variables!")
            print("You can get your ID from @userinfobot")
            return False
        
        try:
            admin_id = int(cls.ADMIN_ID)
            if admin_id <= 0:
                print(f"❌ ERROR: Invalid ADMIN_ID: {cls.ADMIN_ID}")
                return False
            print(f"✅ Admin ID is valid: {admin_id}")
            return True
        except ValueError:
            print(f"❌ ERROR: ADMIN_ID must be a number: {cls.ADMIN_ID}")
            return False
    
    @classmethod
    def validate_all(cls):
        print("🔍 Validating Railway configuration...")
        
        # Token tekshirish
        if not cls.validate_token():
            return False
        
        # Admin ID tekshirish (warning beradi, lekin to'xtamaydi)
        cls.validate_admin_id()
        
        # Database URL tekshirish
        if not cls.DATABASE_URL:
            print("⚠️ WARNING: DATABASE_URL is not set!")
            print("Railway PostgreSQL will provide it automatically")
        else:
            print("✅ DATABASE_URL is set")
        
        print(f"✅ Config validations completed")
        print(f"📊 Config summary:")
        print(f"   - BOT_TOKEN: {'Set' if cls.BOT_TOKEN else 'Not set'}")
        print(f"   - ADMIN_ID: {cls.ADMIN_ID}")
        print(f"   - PORT: {cls.PORT}")
        print(f"   - DATABASE_URL: {'Set' if cls.DATABASE_URL else 'Not set'}")
        
        return True

config = Config()