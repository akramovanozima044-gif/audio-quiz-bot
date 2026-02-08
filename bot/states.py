# bot/states.py
from enum import Enum

class AdminStates(Enum):
    """Admin holatlari"""
    WAITING_BOOK_NAME = "waiting_book_name"
    WAITING_UNIT_NAME = "waiting_unit_name"
    WAITING_AUDIO = "waiting_audio"
    WAITING_QUESTION_TEXT = "waiting_question_text"
    WAITING_OPTIONS = "waiting_options"
    WAITING_CORRECT_ANSWER = "waiting_correct_answer"
    WAITING_EXPLANATION = "waiting_explanation"
    WAITING_BROADCAST_MESSAGE = "waiting_broadcast_message"
    WAITING_NEW_BOOK_NAME = "waiting_new_book_name"
    WAITING_NEW_UNIT_NAME = "waiting_new_unit_name"
    WAITING_NEW_QUESTION_TEXT = "waiting_new_question_text"

class UserStates(Enum):
    """User holatlari"""
    TAKING_TEST = "taking_test"
    WAITING_ANSWER = "waiting_answer"