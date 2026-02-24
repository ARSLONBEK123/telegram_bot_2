import asyncio
from contextlib import suppress
from aiogram.exceptions import TelegramBadRequest

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton

from aiogram.filters import CommandStart

from src.utils.callbackdata import UserMenuCallback
from src.utils.keyboards import user_builder

from src.filters.chattype import ChatTypeFilter
from src.database.collections import db

router = Router()
router.message.filter(ChatTypeFilter(private=True))
router.callback_query.filter(ChatTypeFilter(private=True))


@router.message(CommandStart())
@router.callback_query(UserMenuCallback.filter(F.section == "start"))
async def start(message: Message | CallbackQuery) -> None:
    """
    Start komandasi – foydalanuvchi uchun asosiy menyu.
    Hammasi inline tugmalar orqali ishlaydi.
    """
    text = (
        f"🎬 Xush kelibsiz {message.from_user.mention_html()}!\n\n"
        "Bu bot orqali siz:\n"
        "— 🎥 Eng so‘nggi kinolar\n"
        "— 📺 Eng mashhur seriallar\n"
        "— 🔥 Trend kontentlar\n"
        "— ⚡ Tez va qulay tomosha\n\n"
        "👇 Davom etish uchun menyuni oching"
    )
    # Check if admin and send Reply Keyboard
    admin = await db.admins.find_one({"id": message.from_user.id})
    if admin:
        admin_markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="/admin")]], 
            resize_keyboard=True, 
            one_time_keyboard=False
        )
        await message.answer("admin panel...", reply_markup=admin_markup)

    if isinstance(message, CallbackQuery):
        await message.answer()
        await message.message.edit_text(
        text,
        reply_markup=user_builder(
            {
                "🎬 menyu": {
                    "section": "menu",
                    "action": "open",
                    "page": 1,
                },
                "🪪 Admin bilan bog'lanish": {
                    "section": "contact_admin",
                    "action": "view",
                },
            }
        ),
    )
        return

    await message.answer(
        text,
        reply_markup=user_builder(
            {
                "🎬 menyu": {
                    "section": "menu",
                    "action": "open",
                    "page": 1,
                },
                "🪪 Admin bilan bog'lanish": {
                    "section": "contact_admin",
                    "action": "view",
                },
            }
        ),
    )

@router.callback_query(UserMenuCallback.filter(F.section == "contact_admin"))
async def contact_admin(callback: CallbackQuery, callback_data: UserMenuCallback) -> None:
    """
    Foydalanuvchi uchun oddiy "admin bilan bog'lanish" oynasi.
    """
    text = f"Assalomu aleykum hurmatli {callback.from_user.mention_html()}!\n\nReklama boʻyicha admin lichkasi: @Elbek_05_25"
    with suppress(TelegramBadRequest):
        await callback.answer()
        await callback.message.edit_text(text, reply_markup=user_builder(
            {
                "🔙 ortga": {"section": "start"}
            }
        ))