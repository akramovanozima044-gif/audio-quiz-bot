# config.py - YANGILANGAN VERSIYA
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Environment variables
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = os.getenv("ADMIN_ID")
    DATABASE_URL = os.getenv("DATABASE_URL")
    PORT = os.getenv("PORT", "8000")
    
    # Token validation
    @classmethod
    def validate_token(cls):
        if not cls.BOT_TOKEN:
            print("❌ ERROR: BOT_TOKEN is not set!")
            print("Please set BOT_TOKEN in Railway Variables")
            return False
        
        # Token format tekshirish
        if ':' not in cls.BOT_TOKEN:
            print(f"❌ ERROR: Invalid token format! Token: {cls.BOT_TOKEN}")
            print("Token should be like: 1234567890:AAHhDkjsdfjkKJHSDFJKHSDFjk")
            return False
        
        parts = cls.BOT_TOKEN.split(':')
        if len(parts) != 2:
            print(f"❌ ERROR: Invalid token format! Token: {cls.BOT_TOKEN}")
            return False
        
        if not parts[0].isdigit() or len(parts[0]) != 10:
            print(f"❌ ERROR: Invalid token ID part! Token: {cls.BOT_TOKEN}")
            return False
        
        print(f"✅ Token format is valid (ID: {parts[0]})")
        return True
    
    @classmethod
    def validate_admin_id(cls):
        if not cls.ADMIN_ID:
            print("⚠️ WARNING: ADMIN_ID is not set!")
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
        print("🔍 Validating configuration...")
        
        # Token tekshirish
        if not cls.validate_token():
            return False
        
        # Admin ID tekshirish
        if not cls.validate_admin_id():
            return False
        
        # Database URL tekshirish
        if not cls.DATABASE_URL:
            print("⚠️ WARNING: DATABASE_URL is not set!")
            print("Railway will provide it automatically")
        else:
            print("✅ DATABASE_URL is set")
        
        print(f"✅ All validations passed!")
        print(f"📊 Config summary:")
        print(f"   - BOT_TOKEN: {'Set' if cls.BOT_TOKEN else 'Not set'}")
        print(f"   - ADMIN_ID: {cls.ADMIN_ID}")
        print(f"   - PORT: {cls.PORT}")
        print(f"   - DATABASE_URL: {'Set' if cls.DATABASE_URL else 'Not set'}")
        
        return True

config = Config()

# Bot ishga tushganda tekshirish
if __name__ == "__main__":
    config.validate_all()