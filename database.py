from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import config
import os

# PostgreSQL uchun URL ni tuzatish (Railway uchun)
if config.DATABASE_URL and config.DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = config.DATABASE_URL.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = config.DATABASE_URL or "sqlite:///./quiz.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String)
    last_name = Column(String, nullable=True)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    requested_access = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Aloqalar
    results = relationship("QuizResult", back_populates="user")
    
    def __repr__(self):
        return f"<User {self.user_id} - {self.username}>"

class AdminRequest(Base):
    __tablename__ = "admin_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    username = Column(String)
    requested_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="pending")  # pending, approved, rejected
    
    def __repr__(self):
        return f"<AdminRequest {self.user_id} - {self.status}>"

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Aloqalar
    units = relationship("Unit", back_populates="book", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Book {self.name}>"

class Unit(Base):
    __tablename__ = "units"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    book_id = Column(Integer, ForeignKey("books.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Aloqalar
    book = relationship("Book", back_populates="units")
    questions = relationship("Question", back_populates="unit", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Unit {self.name}>"

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    unit_id = Column(Integer, ForeignKey("units.id"))
    audio_file = Column(String)  # Audio fayl nomi
    options = Column(Text)  # JSON formatda variantlar
    correct_answer = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Aloqalar
    unit = relationship("Unit", back_populates="questions")
    
    def __repr__(self):
        return f"<Question {self.id}>"

class QuizResult(Base):
    __tablename__ = "quiz_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    unit_id = Column(Integer, ForeignKey("units.id"))
    score = Column(Integer)
    total_questions = Column(Integer)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    # Aloqalar
    user = relationship("User", back_populates="results")
    
    def __repr__(self):
        return f"<QuizResult {self.user_id} - {self.score}/{self.total_questions}>"

# Database yaratish
def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ Database yaratildi/tayyor")

def get_db():
    """Database session yaratish generatori"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Avtomatik init
init_db()