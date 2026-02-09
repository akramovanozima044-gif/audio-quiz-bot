# config.py
# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    DATABASE_URL = os.getenv("DATABASE_URL")
    PORT = int(os.getenv("PORT", 8000))
    RAILWAY_ENVIRONMENT = os.getenv("RAILWAY_ENVIRONMENT", "development")
    
config = Config()