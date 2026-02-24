from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from contextlib import suppress
import asyncio

from pymongo.errors import DuplicateKeyError

from typing import Callable, Dict, Any, Awaitable, Union

from datetime import datetime

from src.database.models import User
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


class UserMiddleware(BaseMiddleware):
    """
    Foydalanuvchini har bir so‘rovda avtomatik bazaga qo‘shuvchi yoki yangilovchi middleware.
    """

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.cache = {} # User Cache for optimization

    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:

        # Foydalanuvchini aniqlash
        # event.from_user exists on both Message and CallbackQuery
        from_user = getattr(event, "from_user", None)
        if from_user is None:
            # If no from_user (shouldn't happen), call handler without user
            return await handler(event, data)

        user_id = int(getattr(from_user, "id"))
        is_premium = bool(getattr(from_user, "is_premium", False))
        phone_number = getattr(from_user, "phone_number", None)

        # Try to load existing user by `id` field (other parts of code use `id`)
        existing = await self.db.users.find_one({"id": user_id})

        if existing:
            # Normalize existing doc to plain dict and remove non-int Mongo _id if present
            doc = dict(existing)
            # If Mongo inserted an ObjectId under '_id', remove it so Pydantic doesn't fail
            if "id" in doc and not isinstance(doc["id"], int):
                doc.pop("_id", None)
            # Ensure `id` present and is int
            doc["id"] = int(user_id)
            try:
                user = User(**doc)
            except Exception:
                # Fall back to a minimal User instance if parsing fails
                user = User(_id=user_id, id=user_id, phone_number=phone_number, is_premium=is_premium)
        else:
            # Create a new user with sensible defaults
            user = User(
                id=user_id,
                phone_number=phone_number,
                is_premium=is_premium,
                balance=0,
                referrer_id=None,
                referrals_count=0,
            )
            with suppress(DuplicateKeyError):
                await self.db.users.insert_one(user.model_dump())
                
                # Notify Admins about new user
                try:
                    count = await self.db.users.count({})
                    admins = await self.db.admins.find({}) # Returns list of Admin models
                    bot = data.get("bot") or event.bot
                    
                    print(f"DEBUG: New User {user_id} detected. Total: {count}. Admins: {len(admins)}")

                    mention = from_user.mention_html()
                    msg_text = (
                        f"🎉 <b>Yangi foydalanuvchi!</b>\n\n"
                        f"👤 {mention}\n"
                        f"🆔 <code>{user_id}</code>\n"
                        f"📊 U botning <b>{count}</b>-foydalanuvchisi."
                    )
                    
                    for admin in admins:
                        try:
                            await bot.send_message(chat_id=admin.id, text=msg_text, parse_mode="HTML")
                        except Exception as e:
                            print(f"DEBUG: Failed to notify admin {admin.id}: {e}")
                except Exception as outer_e:
                    print(f"DEBUG: Error in New User Notification block: {outer_e}")

        # Attach the Pydantic user model to handler data
        data["user"] = user

        # --- Forced Subscription Logic ---
        # Skip for Admins
        admin = await self.db.admins.find_one({"id": user_id})
        is_admin = bool(admin)

        if not is_admin:
            # CACHE CHECK
            # Agar oxirgi 2 daqiqa ichida tekshirilgan bo'lsa, qayta tekshirmaymiz
            last_checked = self.cache.get(user_id)
            if last_checked and (datetime.now() - last_checked).total_seconds() < 120:
                pass # Cache hit: Skip check
            else:
                channels = await self.db.channels.find({})
                not_subscribed = []
                
                async def check_channel(ch):
                    try:
                        member = await event.bot.get_chat_member(ch.id, user_id)
                        if member.status in ["left", "kicked", "banned"]:
                            return ch
                    except Exception:
                        pass
                    return None

                # Run checks in parallel
                if channels:
                    results = await asyncio.gather(*(check_channel(ch) for ch in channels))
                    not_subscribed = [ch for ch in results if ch]
                
                if not_subscribed:
                    # Build Keyboard
                    buttons = []
                    for ch in not_subscribed:
                        # Fetch Title
                        try:
                            chat = await event.bot.get_chat(ch.id)
                            title = chat.title
                            url = ch.url or chat.invite_link or f"https://t.me/{chat.username}"
                        except:
                            title = "Kanalga a'zo bo'ling"
                            url = ch.url
                        
                        if url:
                             buttons.append([InlineKeyboardButton(text=f"📢 {title}", url=url)])

                    buttons.append([InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="check_subscription")])
                    
                    text = "⚠️ <b>Diqqat!</b>\n\nBotdan to'liq foydalanish uchun quyidagi kanallarga a'zo bo'ling, so'ngra \"Tasdiqlash\" tugmasini bosing:"
                    
                    if isinstance(event, Message):
                        await event.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
                        return # Stop
                    elif isinstance(event, CallbackQuery):
                        if event.data == "check_subscription":
                             await event.answer("❌ Siz hali barcha kanallarga a'zo bo'lmadingiz!", show_alert=True)
                        else:
                            await event.message.delete()
                            await event.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
                        return # Stop
                
                # Update Cache
                self.cache[user_id] = datetime.now()

        # Continue to next handler
        return await handler(event, data)
