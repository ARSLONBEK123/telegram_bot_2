from aiogram.filters import Filter

from aiogram.types import Message, CallbackQuery
from src.database.collections import db

class IsAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id
        
        # Hardcoded admin ID lar (fallback)
        hardcoded_admin_ids = [2038175209]
        if user_id in hardcoded_admin_ids:
            return True
        
        # Database dan adminlarni tekshirish
        try:
            admin = await db.admins.find_one({"id": user_id})
            if admin:
                return True
            
            # Agar _id bo'yicha topilmasa, id maydoni bo'yicha tekshirish
            admin = await db.admins.find_one({"_id": user_id})
            return admin is not None
        except Exception as e:
            print(f"Error checking admin status: {e}")
            # Xatolik bo'lsa, False qaytarish
            return False

