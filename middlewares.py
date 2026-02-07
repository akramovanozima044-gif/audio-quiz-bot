from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from database import async_session
from sqlalchemy import select
from database import User

class AdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Admin ID ni .env dan olish
        import os
        from dotenv import load_dotenv
        load_dotenv()
        ADMIN_ID = int(os.getenv("ADMIN_ID"))
        
        # Agar user ADMIN_ID ga teng bo'lsa, admin
        if event.from_user.id == ADMIN_ID:
            data['is_admin'] = True
        else:
            data['is_admin'] = False
        
        return await handler(event, data)

class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.user_id == event.from_user.id)
            )
            user = result.scalar_one_or_none()
            
            if user:
                data['user'] = user
                data['is_active'] = user.is_active
            else:
                data['user'] = None
                data['is_active'] = False
        
        return await handler(event, data)