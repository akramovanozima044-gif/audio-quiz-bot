# states.py
from aiogram.fsm.state import State, StatesGroup

class AdminStates(StatesGroup):
    # Test tuzish
    waiting_for_book_name = State()
    waiting_for_unit_name = State()
    waiting_for_audio = State()
    waiting_for_options = State()
    waiting_for_correct_answer = State()
    
    # Test formatlash
    editing_book_name = State()
    editing_unit_name = State()
    editing_question = State()
    
    # Xabar yuborish
    waiting_for_broadcast_message = State()

class UserStates(StatesGroup):
    choosing_book = State()
    choosing_unit = State()
    taking_test = State()
    waiting_for_answer = State()