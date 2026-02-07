import os
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from database import create_db, AsyncSessionLocal
from middlewares import DatabaseMiddleware, UserMiddleware
from handlers import router
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot token from environment
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    logger.error("BOT_TOKEN not set in environment variables")
    exit(1)

# Database URL from Railway
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    # Convert to asyncpg format for Railway PostgreSQL
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
    logger.info(f"Using PostgreSQL database from Railway")
else:
    DATABASE_URL = "sqlite+aiosqlite:///./database.db"
    logger.info("Using SQLite database")

# Audio path
AUDIO_PATH = os.getenv('AUDIO_PATH', 'data/audio')
os.makedirs(AUDIO_PATH, exist_ok=True)
logger.info(f"✅ Audio folder: {AUDIO_PATH}")

async def main():
    # Initialize bot
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    # Initialize dispatcher
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Add middlewares
    dp.update.middleware(DatabaseMiddleware())
    dp.update.middleware(UserMiddleware())
    
    # Include router
    dp.include_router(router)
    
    # Create database tables
    await create_db()
    logger.info("✅ Database initialized successfully")
    
    # Start bot
    logger.info("🚀 Bot starting...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
