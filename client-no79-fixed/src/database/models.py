from typing import Optional, Union

from pydantic import BaseModel


import uuid

class User(BaseModel):
    id: int

class Admin(BaseModel):
    id: int
    full_name: Optional[str] = "Admin"


class Channel(BaseModel):
    id: int
    url: Optional[str] = None


class Category(BaseModel):
    """
    Admin tomonidan yaratiladigan kino/serial va boshqa bo'limlar uchun kategoriya.
    """
    id: str = None  # Custom ID
    title: str 


class Movie(BaseModel):
    """
    Oddiy kino/serial modeli.
    """
    id: str = None # Custom ID
    title: str

    # Qaysi kategoriyaga tegishli (Category.id)
    category_id: Optional[str] = None


class Episode(BaseModel):
    """
    Bitta qism (episode) modeli.
    """
    id: str = None # Custom ID

    movie_id: str  # Qaysi kinoga tegishli (Movie.id)

    season_number: int  # Mavsum raqami (1, 2, 3 ...)
    episode_number: int  # Qism raqami (1, 2, 3 ...)

    file_id: str  # Telegram video/file_id yoki media id
    caption: Optional[str] = None


