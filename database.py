# database.py - TO'LIQ TO'G'RILANGAN VERSIYA


import os
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    is_active = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    
    test_results = relationship("TestResult", back_populates="user")

class Book(Base):
    __tablename__ = 'books'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    units = relationship("Unit", back_populates="book")

class Unit(Base):
    __tablename__ = 'units'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    name = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    book = relationship("Book", back_populates="units")
    questions = relationship("Question", back_populates="unit")

class Question(Base):
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    unit_id = Column(Integer, ForeignKey('units.id'), nullable=False)
    audio_file = Column(String(500), nullable=False)
    options = Column(Text, nullable=False)
    correct_answer = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    
    unit = relationship("Unit", back_populates="questions")

class TestResult(Base):
    __tablename__ = 'test_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'), nullable=False)
    unit_id = Column(Integer, ForeignKey('units.id'), nullable=False)
    score = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    completed_at = Column(DateTime, default=datetime.now)
    
    user = relationship("User", back_populates="test_results")

# Database engine
async def init_db():
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if DATABASE_URL:
        if DATABASE_URL.startswith("postgresql://"):
            DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        DATABASE_URL = "sqlite+aiosqlite:///database.db"
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    return engine

# Global session factory
async def get_session():
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if DATABASE_URL:
        if DATABASE_URL.startswith("postgresql://"):
            DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        DATABASE_URL = "sqlite+aiosqlite:///database.db"
    
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    return async_session