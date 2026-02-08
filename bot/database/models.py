# bot/database/models.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.sql import func
import json
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

def get_database_url():
    """Database URL ni olish"""
    db_url = os.getenv('DATABASE_URL', 'sqlite:///quiz.db')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    return db_url

def get_engine():
    return create_engine(get_database_url())

def get_session():
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

# User model


# Book (Kitob) model
class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    description = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    units = relationship("Unit", back_populates="book", cascade="all, delete")

# Unit (Bo'lim) model
class Unit(Base):
    __tablename__ = "units"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    name = Column(String, nullable=False)
    order_number = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    book = relationship("Book", back_populates="units")
    questions = relationship("Question", back_populates="unit", cascade="all, delete")

# Savol model
class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    audio_file_id = Column(String, nullable=False)  # Telegram file_id
    question_text = Column(String, nullable=True)
    options = Column(JSON, nullable=False)  # Variantlar ro'yxati
    correct_answer = Column(String, nullable=False)
    explanation = Column(String, nullable=True)
    order_number = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    unit = relationship("Unit", back_populates="questions")
    results = relationship("UserAnswer", back_populates="question")

# bot/database/models.py - User modelga qo'shimcha maydonlar qo'shamiz
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=False)  # Admin tasdiqlagandan so'ng True bo'ladi
    is_admin = Column(Boolean, default=False)
    registration_status = Column(String, default="pending")  # pending, approved, rejected
    registration_date = Column(DateTime(timezone=True), server_default=func.now())
    approved_by = Column(Integer, nullable=True)  # Kim tasdiqlagan
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(String, nullable=True)  # Rad etish sababi
    last_activity = Column(DateTime(timezone=True), onupdate=func.now())
    
    results = relationship("TestResult", back_populates="user")

# Test natijalari
class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    score = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    correct_answers = Column(Integer, default=0)
    completed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User", back_populates="results")
    book = relationship("Book")
    unit = relationship("Unit")
    answers = relationship("UserAnswer", back_populates="test_result")

# User javoblari
class UserAnswer(Base):
    __tablename__ = "user_answers"
    
    id = Column(Integer, primary_key=True, index=True)
    test_result_id = Column(Integer, ForeignKey("test_results.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    user_answer = Column(String, nullable=False)
    is_correct = Column(Boolean, default=False)
    answered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    test_result = relationship("TestResult", back_populates="answers")
    question = relationship("Question", back_populates="results")

def init_db():
    """Database yaratish"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    print("✅ Database yaratildi!")
    
    # Admin qo'shish
    db = get_session()
    admin_id = int(os.getenv('ADMIN_ID', 0))
    if admin_id:
        admin = db.query(User).filter(User.telegram_id == admin_id).first()
        if not admin:
            admin = User(
                telegram_id=admin_id,
                username="admin",
                first_name="Admin",
                is_active=True,
                is_admin=True
            )
            db.add(admin)
            db.commit()
            print("✅ Admin yaratildi!")
    db.close()

if __name__ == "__main__":
    init_db()