# bot/database/crud.py
from sqlalchemy.orm import Session
from .models import User, Book, Unit, Question, TestResult, UserAnswer
from typing import List, Optional
import json

class UserCRUD:
    
    @staticmethod
    def create_pending_user(db: Session, telegram_id: int, username: str = None,
                          first_name: str = None, last_name: str = None):
        """Kutilayotgan user yaratish"""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_active=False,
            registration_status="pending"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    @staticmethod
    def approve_user(db: Session, user_id: int, approved_by: int):
        """Userni tasdiqlash"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = True
            user.registration_status = "approved"
            user.approved_by = approved_by
            user.approved_at = func.now()
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def reject_user(db: Session, user_id: int, reason: str = None):
        """Userni rad etish"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.registration_status = "rejected"
            user.rejection_reason = reason
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def get_all_users_with_status(db: Session):
        """Barcha userlarni statusi bilan olish"""
        return db.query(User).order_by(User.registration_date.desc()).all()

    @staticmethod
    def create_user(db: Session, telegram_id: int, username: str = None, 
                   first_name: str = None, last_name: str = None, 
                   is_active: bool = False, is_admin: bool = False):
        """Foydalanuvchi yaratish"""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_active=is_active,
            is_admin=is_admin
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def get_user_by_telegram_id(db: Session, telegram_id: int):
        """Telegram ID bo'yicha foydalanuvchi olish"""
        return db.query(User).filter(User.telegram_id == telegram_id).first()
    
    @staticmethod
    def get_all_users(db: Session, active_only: bool = True):
        """Barcha foydalanuvchilarni olish"""
        query = db.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        return query.all()
    
    @staticmethod
    def update_user_status(db: Session, user_id: int, is_active: bool):
        """Foydalanuvchi statusini yangilash"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_active = is_active
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def delete_user(db: Session, user_id: int):
        """Foydalanuvchini o'chirish"""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            db.delete(user)
            db.commit()
        return user

class BookCRUD:
    @staticmethod
    def create_book(db: Session, name: str, description: str = None):
        """Kitob yaratish"""
        book = Book(name=name, description=description)
        db.add(book)
        db.commit()
        db.refresh(book)
        return book
    
    @staticmethod
    def get_all_books(db: Session, active_only: bool = True):
        """Barcha kitoblarni olish"""
        query = db.query(Book)
        if active_only:
            query = query.filter(Book.is_active == True)
        return query.order_by(Book.name).all()
    
    @staticmethod
    def update_book(db: Session, book_id: int, name: str = None, description: str = None):
        """Kitobni yangilash"""
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            if name:
                book.name = name
            if description:
                book.description = description
            db.commit()
            db.refresh(book)
        return book
    
    @staticmethod
    def delete_book(db: Session, book_id: int):
        """Kitobni o'chirish"""
        book = db.query(Book).filter(Book.id == book_id).first()
        if book:
            db.delete(book)
            db.commit()
        return book

class UnitCRUD:
    @staticmethod
    def create_unit(db: Session, book_id: int, name: str):
        """Unit yaratish"""
        unit = Unit(book_id=book_id, name=name)
        db.add(unit)
        db.commit()
        db.refresh(unit)
        return unit
    
    @staticmethod
    def get_units_by_book(db: Session, book_id: int):
        """Kitob bo'yicha unitlarni olish"""
        return db.query(Unit).filter(Unit.book_id == book_id).order_by(Unit.order_number).all()
    
    @staticmethod
    def update_unit(db: Session, unit_id: int, name: str = None):
        """Unitni yangilash"""
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if unit:
            if name:
                unit.name = name
            db.commit()
            db.refresh(unit)
        return unit
    
    @staticmethod
    def delete_unit(db: Session, unit_id: int):
        """Unitni o'chirish"""
        unit = db.query(Unit).filter(Unit.id == unit_id).first()
        if unit:
            db.delete(unit)
            db.commit()
        return unit

class QuestionCRUD:
    @staticmethod
    def create_question(db: Session, unit_id: int, audio_file_id: str, options: List[str],
                       correct_answer: str, question_text: str = None, explanation: str = None):
        """Savol yaratish"""
        question = Question(
            unit_id=unit_id,
            audio_file_id=audio_file_id,
            question_text=question_text,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation
        )
        db.add(question)
        db.commit()
        db.refresh(question)
        return question
    
    @staticmethod
    def get_questions_by_unit(db: Session, unit_id: int):
        """Unit bo'yicha savollarni olish"""
        return db.query(Question).filter(Question.unit_id == unit_id).order_by(Question.order_number).all()
    
    @staticmethod
    def get_question_count(db: Session, unit_id: int):
        """Unitdagi savollar soni"""
        return db.query(Question).filter(Question.unit_id == unit_id).count()
    
    @staticmethod
    def update_question(db: Session, question_id: int, **kwargs):
        """Savolni yangilash"""
        question = db.query(Question).filter(Question.id == question_id).first()
        if question:
            for key, value in kwargs.items():
                if hasattr(question, key) and value is not None:
                    setattr(question, key, value)
            db.commit()
            db.refresh(question)
        return question
    
    @staticmethod
    def delete_question(db: Session, question_id: int):
        """Savolni o'chirish"""
        question = db.query(Question).filter(Question.id == question_id).first()
        if question:
            db.delete(question)
            db.commit()
        return question