# handlers/user.py - TO'LIQ YANGILANGAN VERSIYA
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from database import async_session, UserResult, Book, Unit, User
from sqlalchemy import select, func, desc
from keyboards import get_user_main_menu
import asyncio

router = Router()

# ========== MENYU HANDLERLARI ==========

@router.message(F.text == "⬅️ Orqaga")
async def back_to_user_main(message: types.Message):
    """User menyusiga qaytish"""
    await message.answer(
        "Asosiy menyu:",
        reply_markup=get_user_main_menu()
    )

# ========== MENING NATIJALARIM ==========

# handlers/user.py - Oddiyroq versiya

@router.message(F.text == "📊 Mening natijalarim")
async def my_results_simple(message: types.Message, state: FSMContext):
    """Foydalanuvchining o'z natijalarini ko'rsatish (oddiy versiya)"""
    user_id = message.from_user.id
    
    # Foydalanuvchi uchun loading emoji yuboramiz
    await message.answer("⏳")
    
    async with async_session() as session:
        # Foydalanuvchining oxirgi 10 ta natijasini olish
        recent_results = await session.execute(
            select(UserResult)
            .where(UserResult.user_id == user_id)
            .order_by(UserResult.completed_at.desc())
            .limit(10)
        )
        results = recent_results.scalars().all()
        
        if not results:
            await message.answer("📭 Hozircha sizda test natijalari mavjud emas.")
            return
        
        # So'nggi natijalarni ko'rsatish
        results_text = "📊 Mening so'nggi 10 ta natijam:\n\n"
        
        for i, res in enumerate(results, 1):
            # Kitob nomini olish
            book_result = await session.execute(
                select(Book).where(Book.id == res.book_id)
            )
            book = book_result.scalar_one_or_none()
            book_name = book.name if book else "Noma'lum"
            
            # Unit nomini olish
            unit_result = await session.execute(
                select(Unit).where(Unit.id == res.unit_id)
            )
            unit = unit_result.scalar_one_or_none()
            unit_name = unit.name if unit else "Noma'lum"
            
            # Natijani formatlash
            results_text += (
                f"{i}. {book_name} - {unit_name}\n"
                f"   ✅ {res.correct_answers}/{res.total_questions}\n"
                f"   📈 {res.score}%\n"
                f"   📅 {res.completed_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
        
        # Umumiy statistika
        stats_result = await session.execute(
            select(
                func.count(UserResult.id).label('total_tests'),
                func.sum(UserResult.correct_answers).label('total_correct'),
                func.sum(UserResult.total_questions).label('total_questions'),
                func.avg(UserResult.score).label('avg_score'),
                func.max(UserResult.score).label('best_score')
            ).where(UserResult.user_id == user_id)
        )
        stats = stats_result.one()
        
        total_tests, total_correct, total_questions, avg_score, best_score = stats
        
        stats_text = (
            f"\n📈 UMUMIY STATISTIKA:\n"
            f"📊 Testlar soni: {total_tests or 0} ta\n"
            f"✅ To'g'ri javoblar: {total_correct or 0}/{total_questions or 0}\n"
            f"🏆 O'rtacha ball: {(avg_score or 0):.1f}%\n"
        )
        
        if best_score:
            stats_text += f"🥇 Eng yaxshi natija: {best_score}%\n"
        
        # Barcha natijalarni ko'rish tugmasi
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="📋 Barcha natijalarim", 
                        callback_data="view_all_results"
                    )
                ]
            ]
        )
        
        # Xabarni yuborish
        await message.answer(results_text + stats_text, reply_markup=keyboard)
        
        # State ga ma'lumotlarni saqlash
        await state.update_data(user_id=user_id)

# Keyin boshqa funksiyalar o'zgarishsiz qoladi...
# ========== REYTING ==========

@router.message(F.text == "🏆 Reyting")
async def user_rating(message: types.Message):
    """Foydalanuvchilar reytingini ko'rsatish"""
    # Loading xabari
    loading_msg = await message.answer("🏆 Reyting hisoblanmoqda...")
    
    async with async_session() as session:
        # Reytingni hisoblash (faqat faol foydalanuvchilar)
        rating_result = await session.execute(
            select(
                User.user_id,
                User.first_name,
                User.last_name,
                User.username,
                func.avg(UserResult.score).label('avg_score'),
                func.count(UserResult.id).label('tests_count'),
                func.max(UserResult.score).label('best_score')
            )
            .join(UserResult, User.user_id == UserResult.user_id)
            .where(User.is_active == True)
            .group_by(User.user_id, User.first_name, User.last_name, User.username)
            .order_by(func.avg(UserResult.score).desc())
            .limit(20)  # Top 20
        )
        
        rating_list = rating_result.all()
        
        if not rating_list:
            await loading_msg.edit_text("🏆 Hozircha reyting mavjud emas.")
            return
        
        # Reyting matni
        rating_text = "🏆 TOP 20 FOYDALANUVCHILAR:\n\n"
        
        for i, (user_id, first_name, last_name, username, avg_score, tests_count, best_score) in enumerate(rating_list, 1):
            # Foydalanuvchi nomini tayyorlash
            name = f"{first_name or ''} {last_name or ''}".strip()
            if not name:
                name = f"User_{user_id}"
            
            # Username
            username_display = f" @{username}" if username else ""
            
            # Medallar
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            rating_text += (
                f"{medal} {name}{username_display}\n"
                f"   📊 O'rtacha: {avg_score:.1f}%\n"
                f"   📈 Testlar: {tests_count} ta\n"
                f"   ⭐ Eng yaxshi: {best_score}%\n\n"
            )
        
        # Joriy foydalanuvchining reytingi
        current_user_id = message.from_user.id
        
        # Joriy foydalanuvchi reytingini hisoblash
        user_rank_result = await session.execute(
            select(
                func.avg(UserResult.score).label('avg_score'),
                func.count(UserResult.id).label('tests_count'),
                func.max(UserResult.score).label('best_score'),
                func.row_number().over(
                    order_by=func.avg(UserResult.score).desc()
                ).label('rank')
            )
            .select_from(UserResult)
            .where(UserResult.user_id == current_user_id)
            .group_by(UserResult.user_id)
        )
        
        user_stats = user_rank_result.first()
        
        if user_stats:
            avg_score, tests_count, best_score, rank = user_stats
            
            # Joriy foydalanuvchi ma'lumotlari
            user_result = await session.execute(
                select(User).where(User.user_id == current_user_id)
            )
            user = user_result.scalar_one()
            
            user_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
            if not user_name:
                user_name = f"User_{current_user_id}"
            
            rating_text += (
                f"\n📊 SIZNING REYTINGINGIZ:\n"
                f"🏅 O'rin: #{rank}\n"
                f"👤 Ism: {user_name}\n"
                f"⭐ O'rtacha ball: {avg_score:.1f}%\n"
                f"📈 Testlar soni: {tests_count} ta\n"
                f"🥇 Eng yaxshi natija: {best_score}%\n"
            )
            
            # Motivatsion xabar
            if rank <= 3:
                rating_text += "\n🎉 Tabriklaymiz! Siz eng yaxshilardansiz! 🏆"
            elif rank <= 10:
                rating_text += "\n👍 Juda yaxshi! Top 10 ichidasiz! 💪"
            elif rank <= 20:
                rating_text += "\n😊 Yaxshi natija! Top 20 ichidasiz! ✨"
            else:
                rating_text += f"\n📚 Siz {rank-20} o'rinda. Yana bir oz harakat! 🔥"
        else:
            rating_text += "\n📭 Sizda hali test natijalari mavjud emas."
        
        # Filter tugmalari
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="📊 O'rtacha ball bo'yicha", callback_data="rating_by_avg"),
                    types.InlineKeyboardButton(text="🥇 Eng yaxshi natija", callback_data="rating_by_best")
                ],
                [
                    types.InlineKeyboardButton(text="📈 Testlar soni", callback_data="rating_by_tests")
                ]
            ]
        )
        
        await loading_msg.edit_text(rating_text, reply_markup=keyboard)

@router.callback_query(F.data == "rating_by_avg")
async def rating_by_avg(callback: types.CallbackQuery):
    """O'rtacha ball bo'yicha reyting"""
    await show_rating_by(callback, "avg")

@router.callback_query(F.data == "rating_by_best")
async def rating_by_best(callback: types.CallbackQuery):
    """Eng yaxshi natija bo'yicha reyting"""
    await show_rating_by(callback, "best")

@router.callback_query(F.data == "rating_by_tests")
async def rating_by_tests(callback: types.CallbackQuery):
    """Testlar soni bo'yicha reyting"""
    await show_rating_by(callback, "tests")

async def show_rating_by(callback: types.CallbackQuery, sort_by="avg"):
    """Turli mezonlar bo'yicha reyting ko'rsatish"""
    async with async_session() as session:
        if sort_by == "avg":
            # O'rtacha ball bo'yicha
            rating_result = await session.execute(
                select(
                    User.user_id,
                    User.first_name,
                    User.last_name,
                    User.username,
                    func.avg(UserResult.score).label('value'),
                    func.count(UserResult.id).label('tests_count')
                )
                .join(UserResult, User.user_id == UserResult.user_id)
                .where(User.is_active == True)
                .group_by(User.user_id, User.first_name, User.last_name, User.username)
                .order_by(func.avg(UserResult.score).desc())
                .limit(15)
            )
            title = "🏆 O'rtacha ball bo'yicha TOP 15"
            value_label = "O'rtacha"
            
        elif sort_by == "best":
            # Eng yaxshi natija bo'yicha
            rating_result = await session.execute(
                select(
                    User.user_id,
                    User.first_name,
                    User.last_name,
                    User.username,
                    func.max(UserResult.score).label('value'),
                    func.count(UserResult.id).label('tests_count')
                )
                .join(UserResult, User.user_id == UserResult.user_id)
                .where(User.is_active == True)
                .group_by(User.user_id, User.first_name, User.last_name, User.username)
                .order_by(func.max(UserResult.score).desc())
                .limit(15)
            )
            title = "🥇 Eng yaxshi natija bo'yicha TOP 15"
            value_label = "Eng yaxshi"
            
        elif sort_by == "tests":
            # Testlar soni bo'yicha
            rating_result = await session.execute(
                select(
                    User.user_id,
                    User.first_name,
                    User.last_name,
                    User.username,
                    func.count(UserResult.id).label('value'),
                    func.avg(UserResult.score).label('avg_score')
                )
                .join(UserResult, User.user_id == UserResult.user_id)
                .where(User.is_active == True)
                .group_by(User.user_id, User.first_name, User.last_name, User.username)
                .order_by(func.count(UserResult.id).desc())
                .limit(15)
            )
            title = "📈 Testlar soni bo'yicha TOP 15"
            value_label = "Testlar"
        
        rating_list = rating_result.all()
        
        if not rating_list:
            await callback.message.edit_text("🏆 Hozircha reyting mavjud emas.")
            return
        
        rating_text = f"{title}:\n\n"
        
        for i, (user_id, first_name, last_name, username, value, extra) in enumerate(rating_list, 1):
            # Foydalanuvchi nomini tayyorlash
            name = f"{first_name or ''} {last_name or ''}".strip()
            if not name:
                name = f"User_{user_id}"
            
            # Username
            username_display = f" @{username}" if username else ""
            
            # Medallar
            if i == 1:
                medal = "🥇"
            elif i == 2:
                medal = "🥈"
            elif i == 3:
                medal = "🥉"
            else:
                medal = f"{i}."
            
            rating_text += f"{medal} {name}{username_display}\n"
            
            if sort_by == "avg":
                rating_text += f"   📊 {value_label}: {value:.1f}%\n"
                rating_text += f"   📈 Testlar: {extra} ta\n\n"
            elif sort_by == "best":
                rating_text += f"   ⭐ {value_label}: {value}%\n"
                rating_text += f"   📊 Testlar: {extra} ta\n\n"
            elif sort_by == "tests":
                rating_text += f"   📈 {value_label}: {value} ta\n"
                rating_text += f"   📊 O'rtacha: {extra:.1f}%\n\n"
        
        # Tugmalar
        keyboard = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="📊 Asosiy reyting", callback_data="back_to_main_rating")
                ]
            ]
        )
        
        await callback.message.edit_text(rating_text, reply_markup=keyboard)

@router.callback_query(F.data == "back_to_main_rating")
async def back_to_main_rating(callback: types.CallbackQuery):
    """Asosiy reytingga qaytish"""
    await user_rating(callback.message)

# ========== BEKOR QILISH ==========

@router.message(F.text == "❌ Bekor qilish")
async def cancel_user_action(message: types.Message, state: FSMContext):
    """User amalini bekor qilish"""
    await state.clear()
    await message.answer(
        "❌ Amal bekor qilindi.",
        reply_markup=get_user_main_menu()
    )