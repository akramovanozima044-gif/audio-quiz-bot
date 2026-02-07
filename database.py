from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///database.db")

# Agar Railway DATABASE_URL bergan bo'lsa
if DATABASE_URL and DATABASE_URL.startswith('postgresql://'):
    # async uchun postgresql+asyncpg ga o'zgartirish
    DATABASE_URL = DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://')
else:
    # Local development uchun SQLite
    DATABASE_URL = "sqlite+aiosqlite:///./database.db"

# Database engine yaratish
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    results = relationship("UserResult", back_populates="user")

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    units = relationship("Unit", back_populates="book", cascade="all, delete-orphan")

class Unit(Base):
    __tablename__ = "units"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"))
    created_at = Column(DateTime, default=datetime.now)
    
    book = relationship("Book", back_populates="units")
    questions = relationship("Question", back_populates="unit", cascade="all, delete-orphan")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True)
    unit_id = Column(Integer, ForeignKey("units.id"))
    audio_path = Column(String(500), nullable=False)
    question_text = Column(String(500))
    options = Column(Text, nullable=False)  # JSON formatida saqlanadi: ["var1", "var2", "var3", "var4"]
    correct_answer = Column(Integer, nullable=False)  # To'g'ri javob indeksi (0-3)
    created_at = Column(DateTime, default=datetime.now)
    
    unit = relationship("Unit", back_populates="questions")

class UserResult(Base):
    __tablename__ = "user_results"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    unit_id = Column(Integer, ForeignKey("units.id"))
    correct_answers = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    score = Column(Integer, default=0)  # Foizda
    completed_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="results")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)