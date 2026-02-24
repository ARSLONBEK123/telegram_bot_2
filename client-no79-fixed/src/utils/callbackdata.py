from aiogram.filters.callback_data import CallbackData
from typing import Optional


class UserMenuCallback(CallbackData, prefix="menu"):
    """
    Movie-bot uchun callback data formati (user taraf).

    section – qaysi bo‘lim:
        - "menu"         – startdan keyingi asosiy menyu (menu:open)
        - "movies"       – eski nom, hozir "menu" o‘rnida ishlatilmaydi
        - "category"     – kategoriyalar (admin kiritgan)
        - "movie"        – bitta kino/serial sahifasi
        - "season"       – fasllar va qismlar
    """

    section: Optional[str] = None
    action: Optional[str] = None

    # Admin tomonidan yaratilgan kategoriya ID si
    category_id: Optional[str] = None

    # Kino ID (Mongo _id si string ko‘rinishida saqlanadi)
    movie_id: Optional[str] = None

    # Fasl / qism raqamlari
    season_number: Optional[int] = None
    episode_number: Optional[int] = None

    # Sahifalash
    page: Optional[int] = 1



class AdminMenuCallback(CallbackData, prefix="adminmenu"):
    """
    Admin panel uchun callback data.

    section:
        - "main"     – asosiy admin menyu
        - "categories" – kategoriyalar
        - "movies"     – kinolar
        - "episodes"   – qismlar
        - "users"      – foydalanuvchilar (optional)

    action:
        - "list"     – ro‘yxat
        - "add"      – qo‘shish (start adding)
        - "delete"   – o‘chirish
        - "edit"     – tahrirlash (optional)
        - "select"   – tanlash (sub-menu ga o‘tish)
        - "back"     – orqaga qaytish
    """

    section: Optional[str] = "main"
    action: Optional[str] = "list"
    
    # Context (qaysi obyekt ustida amal bajarilayotgani)
    category_id: Optional[str] = None
    movie_id: Optional[str] = None
    season_number: Optional[int] = None
    episode_id: Optional[str] = None
    user_id: Optional[int] = None
    channel_id: Optional[int] = None

    page: int = 1

