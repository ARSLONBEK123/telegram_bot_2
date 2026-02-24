from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter, TelegramForbiddenError
import asyncio
from contextlib import suppress 

from src.config import config
from src.database.collections import db
from src.database.models import Category, Movie, Episode # Correct imports? Yes
from src.utils.callbackdata import AdminMenuCallback
from src.utils.keyboards import admin_builder
from src.filters.basic import IsAdmin
from src.filters.chattype import ChatTypeFilter
from src.utils.paginations import Pagination
import uuid

router = Router()
router.message.filter(ChatTypeFilter(private=True), IsAdmin())
router.callback_query.filter(ChatTypeFilter(private=True), IsAdmin())

class AdminState(StatesGroup):
    waiting_for_category_name = State()
    waiting_for_movie_title = State()
    waiting_for_season_number = State()
    waiting_for_episode_number = State()
    waiting_for_file = State()
    waiting_for_new_category_name = State()
    waiting_for_new_movie_title = State()
    waiting_for_new_episode_file = State()
    waiting_for_admin_id = State()
    waiting_for_channel_id = State()
    waiting_for_broadcast_message = State()

# --- Main Menu ---
@router.message(Command("admin"))
async def admin_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👨‍💻 Admin Panelga xush kelibsiz!",
        reply_markup=admin_builder({
            "📂 Kategoriyalar": {"section": "categories"},
            "👤 Adminlar": {"section": "admins"},
            "📊 Statistika": {"section": "stats"},
            "📢 Kanallar": {"section": "channels"},
            "📨 Xabar yuborish": {"section": "broadcast_start"},
        })
    )

@router.callback_query(AdminMenuCallback.filter((F.section == "main") | (F.action == "back")))
async def admin_main_menu(call: CallbackQuery, state: FSMContext):
    await state.clear() 
    await call.message.edit_text(
        "👨‍💻 Admin Panel",
        reply_markup=admin_builder({
            "📂 Kategoriyalar": {"section": "categories"},
            "👤 Adminlar": {"section": "admins"},
            "📊 Statistika": {"section": "stats"},
            "📢 Kanallar": {"section": "channels"},
            "📨 Xabar yuborish": {"section": "broadcast_start"},
        })
    )

# --- Categories ---
@router.callback_query(AdminMenuCallback.filter((F.section == "categories") & (F.action == "list")))
async def list_categories(call: CallbackQuery, state: FSMContext):
    await state.clear()
    categories = await db.categories.find(count=50)
    
    keyboard = {}
    for cat in categories:
        keyboard[cat.title] = {"section": "categories", "action": "view", "category_id": cat.id}
        
    # We want to manage them. Let's just show "Add Category" button and list existing as Text? 
    # Or buttons to delete?
    # Requirement: "admin panel orqali qo'shiladi bular"
    
    msg_text = "📂 **Kategoriyalar** (tahrirlash uchun bosing):\n\n"
    with suppress(TelegramBadRequest):
        await call.message.edit_text(
            msg_text,
            reply_markup=admin_builder(
                details=keyboard,
                footer_details={
                    "➕ Kategoriya qo‘shish": {"section": "categories", "action": "add"},
                    "🔙 Orqaga": {"section": "main"}
                }
            ),
            parse_mode="Markdown"
        )

@router.callback_query(AdminMenuCallback.filter((F.section == "categories") & (F.action == "add")))
async def ask_category_name(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Yangi kategoriya nomini yuboring:", reply_markup=None)
    await state.set_state(AdminState.waiting_for_category_name)

@router.message(AdminState.waiting_for_category_name)
async def save_category(message: Message, state: FSMContext):
    title = message.text
    # Validation?
    # Validation?
    new_id = str(uuid.uuid4())[:8]
    await db.categories.insert_one({"id": new_id, "title": title})
    await message.answer(f"✅ Kategoriya qo'shildi: {title}")
    # Return to menu
    await message.answer(
        "Admin Panel",
        reply_markup=admin_builder(
            {"📂 Kategoriyalar": {"section": "categories"}},
            footer_details={"🔙 Bosh menyu": {"section": "main"}}
        )
    )
    await state.clear()

@router.callback_query(AdminMenuCallback.filter((F.section == "categories") & (F.action == "view")))
async def category_view(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.clear()
    category_id = callback_data.category_id
    page = callback_data.page
    
    category = await db.categories.find_one({"id": category_id})
    if not category:
        await call.answer("Kategoriya topilmadi", show_alert=True)
        return

    # Count movies
    movie_count = await db.movies.count({"category_id": category_id})
    movies = await db.movies.find({"category_id": category_id})
    
    text = (
        f"📂 <b>Kategoriya:</b> {category.title}\n"
        f"🎬 <b>Kinolar soni:</b> {movie_count} ta\n\n"
        "Quyida kinolar ro'yxati va boshqaruv tugmalari:"
    )

    #  objects=season_list ## This logic is in manage_movie now

    pagination = Pagination(
        objects=movies,
        page_data=lambda p: AdminMenuCallback(
            section="categories", action="view", category_id=category_id, page=p
        ).pack(),
        item_data=lambda item, p: AdminMenuCallback(
            section="movie_manage", movie_id=item.id, page=p
        ).pack(),
        item_title=lambda item, p: f"🎬 {item.title}",
    )
    
    markup = pagination.create(page=page, lines=5, columns=1)
    builder = InlineKeyboardBuilder.from_markup(markup)
    
    # 2. Add Admin Action Buttons (Append to pagination)
    # Add Movie
    builder.row(types.InlineKeyboardButton(
        text="➕ Kino qo'shish",
        callback_data=AdminMenuCallback(section="movies_add", category_id=category_id).pack()
    ))
    
    # Manage Category Buttons
    builder.row(
        types.InlineKeyboardButton(
            text="✏️ Nomini o'zgartirish",
            callback_data=AdminMenuCallback(section="categories", action="rename", category_id=category_id).pack()
        ),
        types.InlineKeyboardButton(
            text="🗑 O'chirish",
            callback_data=AdminMenuCallback(section="categories", action="delete", category_id=category_id).pack()
        )
    )
    
    # Back Button
    builder.row(types.InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data=AdminMenuCallback(section="categories", action="list").pack()
    ))

    with suppress(TelegramBadRequest):
        await call.message.edit_text(
            text,
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )

@router.callback_query(AdminMenuCallback.filter((F.section == "categories") & (F.action == "rename")))
async def rename_category_start(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.update_data(category_id=callback_data.category_id)
    await call.message.edit_text(
        "📝 Kategoriya uchun yangi nom kiriting:",
        reply_markup=admin_builder(
            details=None,
            footer_details={"🔙 Bekor qilish": {"section": "categories", "action": "view", "category_id": callback_data.category_id}}
        )
    )
    await state.set_state(AdminState.waiting_for_new_category_name)

@router.message(AdminState.waiting_for_new_category_name)
async def save_renamed_category(message: Message, state: FSMContext):
    data = await state.get_data()
    category_id = data.get("category_id")
    new_title = message.text
    
    await db.categories.update_one({"id": category_id}, {"$set": {"title": new_title}})
    await message.answer(f"✅ Kategoriya nomi o'zgartirildi: {new_title}")
    
    # Show view again (need to reconstruct message or send new one)
    # Since message.answer sends new message, we show menu there.
    category = await db.categories.find_one({"id": category_id})
    movie_count = await db.movies.count({"category_id": category_id})
    
    # Redirect back to category view (simulated)
    # We can't query "movies" accurately without pagination code duplication here. 
    # Best is to send a simple message with "Back" button to reload the view cleanly.
    
    await message.answer(
        f"✅ Kategoriya nomi muvaffaqiyatli o'zgartirildi: <b>{new_title}</b>\n\n"
        "Boshqaruv paneliga qaytish uchun tugmani bosing:",
        reply_markup=admin_builder(
            details=None,
            footer_details={"🔙 Kategoriya boshqaruviga qaytish": {"section": "categories", "action": "view", "category_id": category_id}}
        ),
        parse_mode="HTML"
    )
    await state.clear()

@router.callback_query(AdminMenuCallback.filter((F.section == "categories") & (F.action == "delete")))
async def ask_delete_category(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    category_id = callback_data.category_id
    await call.message.edit_text(
        "⚠️ <b>Rostan ham ushbu kategoriyani o'chirmoqchimisiz?</b>\n"
        "Ichidagi barcha kinolar ham o'chib ketishi mumkin!",
        reply_markup=admin_builder(
            {
                "✅ Ha, o'chirish": {"section": "categories", "action": "delete_confirm", "category_id": category_id}
            },
            footer_details={
                "❌ Yo'q, qaytish": {"section": "categories", "action": "view", "category_id": category_id}
            }
        ),
        parse_mode="HTML"
    )

@router.callback_query(AdminMenuCallback.filter((F.section == "categories") & (F.action == "delete_confirm")))
async def delete_category_execute(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.clear()
    category_id = callback_data.category_id
    await db.categories.delete_one({"id": category_id})
    # Optional: Delete cascading movies? For now just category.
    
    await call.answer("🗑 Kategoriya o'chirildi!", show_alert=True)
    await list_categories(call, state)


# --- Movies ---
# Old 'list_categories_for_movies' and 'list_movies' were merged into 'category_view'.
# We keep 'save_movie', 'manage_movie' etc.

@router.callback_query(AdminMenuCallback.filter(F.section == "movies_add"))
async def ask_movie_title(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.clear()
    await state.update_data(category_id=callback_data.category_id)
    await call.message.edit_text("Kino nomini yuboring:")
    await state.set_state(AdminState.waiting_for_movie_title)

@router.message(AdminState.waiting_for_movie_title)
async def save_movie(message: Message, state: FSMContext):
    data = await state.get_data()
    cat_id = data.get("category_id")
    title = message.text
    
    
    new_id = str(uuid.uuid4())[:8]
    res = await db.movies.insert_one({"id": new_id, "title": title, "category_id": cat_id})
    # Warning: db.movies.insert_one returns result, need _id if we want to continue adding seasons
    
    await message.answer(f"✅ Kino qo'shildi: {title}")
    await state.clear()
    
    # Return to movies list (which is category view now)
    await message.answer("Davom eting:", reply_markup=admin_builder(
        {"Ro'yxatga qaytish": {"section": "categories", "action": "view", "category_id": cat_id}},
        footer_details={"Bosh menyu": {"section": "main"}}
    ))

@router.callback_query(AdminMenuCallback.filter(F.section == "movie_manage"))
async def manage_movie(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.clear()
    movie_id = callback_data.movie_id
    page = callback_data.page
    
    movie = await db.movies.find_one({"id": movie_id})
    if not movie:
        await call.answer("Kino topilmadi", show_alert=True)
        return

    # Stats
    season_list = await db.episodes.collection.distinct("season_number", {"movie_id": movie_id})
    season_list.sort()
    episode_count = await db.episodes.count({"movie_id": movie_id})
    
    title = movie.title
    text = (
        f"🎥 <b>Kino:</b> {title}\n"
        f"📂 <b>Fasllar soni:</b> {len(season_list)}\n"
        f"🎞 <b>Jami qismlar:</b> {episode_count}\n\n"
        "Mavjud fasllar va boshqaruv:"
    )
    
    # 1. Pagination for Seasons
    pagination = Pagination(
        objects=season_list,
        page_data=lambda p: AdminMenuCallback(
            section="movie_manage", movie_id=movie_id, page=p
        ).pack(),
        item_data=lambda item, p: AdminMenuCallback(
            section="season_view", movie_id=movie_id, season_number=item, page=1
        ).pack(),
        item_title=lambda item, p: str(item),
    )
    
    markup = pagination.create(page=page, lines=5, columns=5) # 5 columns for numbers
    builder = InlineKeyboardBuilder.from_markup(markup)
    
    # 2. Admin Actions
    builder.row(types.InlineKeyboardButton(
        text="➕ Qism/Fasl qo'shish", 
        callback_data=AdminMenuCallback(section="episode_add", movie_id=movie_id).pack()
    ))
    
    builder.row(
        types.InlineKeyboardButton(
            text="✏️ Nomini o'zgartirish",
            callback_data=AdminMenuCallback(section="movies", action="rename", movie_id=movie_id).pack()
        ),
        types.InlineKeyboardButton(
            text="🗑 Kinoni o'chirish",
            callback_data=AdminMenuCallback(section="movies", action="delete", movie_id=movie_id).pack()
        )
    )
    
    builder.row(types.InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data=AdminMenuCallback(section="categories", action="view", category_id=movie.category_id).pack()
    ))
    
    await call.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(AdminMenuCallback.filter((F.section == "movies") & (F.action == "rename")))
async def rename_movie_start(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.update_data(movie_id=callback_data.movie_id)
    await call.message.edit_text(
        "📝 Kino uchun yangi nom kiriting:",
        reply_markup=admin_builder(
            details=None,
            footer_details={"🔙 Bekor qilish": {"section": "movie_manage", "movie_id": callback_data.movie_id}}
        )
    )
    await state.set_state(AdminState.waiting_for_new_movie_title)

@router.message(AdminState.waiting_for_new_movie_title)
async def save_renamed_movie(message: Message, state: FSMContext):
    data = await state.get_data()
    movie_id = data.get("movie_id")
    new_title = message.text
    
    await db.movies.update_one({"id": movie_id}, {"$set": {"title": new_title}})
    
    # Reload view code duplicated from manage_movie (simplified)
    # Ideally should redirect or use a shared function, but sticking to inline update pattern
    
    season_list = await db.episodes.collection.distinct("season_number", {"movie_id": movie_id})
    season_list.sort()
    episode_count = await db.episodes.count({"movie_id": movie_id})
    
    text = (
        f"🎥 <b>Kino:</b> {movie.title}\n"
        f"📂 <b>Fasllar soni:</b> {len(season_list)}\n"
        f"🎞 <b>Jami qismlar:</b> {episode_count}\n\n"
        "Mavjud fasllar va boshqaruv:"
    )

    # 1. Pagination for Seasons
    pagination = Pagination(
        objects=season_list,
        page_data=lambda p: AdminMenuCallback(
            section="movie_manage", movie_id=movie_id, page=p
        ).pack(),
        item_data=lambda item, p: AdminMenuCallback(
            section="season_view", movie_id=movie_id, season_number=item, page=1
        ).pack(),
        item_title=lambda item, p: str(item),
    )
    
    markup = pagination.create(page=1, lines=5, columns=5)
    builder = InlineKeyboardBuilder.from_markup(markup)
    
    # 2. Admin Actions
    builder.row(types.InlineKeyboardButton(
        text="➕ Qism/Fasl qo'shish", 
        callback_data=AdminMenuCallback(section="episode_add", movie_id=movie_id).pack()
    ))
    
    builder.row(
        types.InlineKeyboardButton(
            text="✏️ Nomini o'zgartirish",
            callback_data=AdminMenuCallback(section="movies", action="rename", movie_id=movie_id).pack()
        ),
        types.InlineKeyboardButton(
            text="🗑 Kinoni o'chirish",
            callback_data=AdminMenuCallback(section="movies", action="delete", movie_id=movie_id).pack()
        )
    )
    
    builder.row(types.InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data=AdminMenuCallback(section="categories", action="view", category_id=movie.category_id).pack()
    ))

    await message.answer(
        f"✅ Kino nomi o'zgartirildi: {new_title}\n\n{text}",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await state.clear()

@router.callback_query(AdminMenuCallback.filter((F.section == "movies") & (F.action == "delete")))
async def ask_delete_movie(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    movie_id = callback_data.movie_id
    await call.message.edit_text(
        "⚠️ <b>Rostan ham ushbu kinoni o'chirmoqchimisiz?</b>",
        reply_markup=admin_builder(
            {
                "✅ Ha, o'chirish": {"section": "movies", "action": "delete_confirm", "movie_id": movie_id}
            },
            footer_details={
                "❌ Yo'q, qaytish": {"section": "movie_manage", "movie_id": movie_id}
            }
        ),
        parse_mode="HTML"
    )

@router.callback_query(AdminMenuCallback.filter((F.section == "movies") & (F.action == "delete_confirm")))
async def delete_movie_execute(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.clear()
    movie_id = callback_data.movie_id
    movie = await db.movies.find_one({"id": movie_id})
    cat_id = movie.category_id if movie else None
    
    await db.movies.delete_one({"id": movie_id})
    # Optional: Delete episodes too?
    # await db.episodes.delete_many({"movie_id": movie_id})
    
    await call.answer("🗑 Kino o'chirildi!", show_alert=True)
    
    if cat_id:
        # Redirect to category view
        await category_view(call, AdminMenuCallback(section="categories", action="view", category_id=cat_id), state)
    else:
         await call.message.edit_text("Kino o'chirildi. Kategoriya topilmadi.", reply_markup=admin_builder(footer_details={"Bosh sahifa": {"section": "main"}}))

# --- Episodes ---
@router.callback_query(AdminMenuCallback.filter(F.section == "episode_add"))
async def ask_season(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.clear()
    await state.update_data(movie_id=callback_data.movie_id)
    
    # Check if season_number is already provided (e.g. from season_view)
    if callback_data.season_number is not None:
        await state.update_data(season_number=callback_data.season_number)
        await call.message.edit_text("Qism raqamini kiriting (masalan: 1):")
        await state.set_state(AdminState.waiting_for_episode_number)
        return

    await call.message.edit_text("Mavsum raqamini yuboring (masalan: 1):")
    await state.set_state(AdminState.waiting_for_season_number)

@router.callback_query(AdminMenuCallback.filter(F.section == "season_view"))
async def season_view(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext): # Added db injection for safety if needed, but we use global db
    await state.clear()
    movie_id = callback_data.movie_id
    season_number = callback_data.season_number
    page = callback_data.page
    
    movie = await db.movies.find_one({"id": movie_id})
    if not movie:
         await call.answer("Kino topilmadi", show_alert=True)
         return

    # Fetch episodes
    episodes = await db.episodes.find({"movie_id": movie_id, "season_number": season_number})
    # Sort by episode number
    episodes.sort(key=lambda x: x.episode_number)
    
    text = (
        f"🎥 <b>Kino:</b> {movie.title}\n"
        f"📂 <b>Fasl:</b> {season_number}\n"
        f"🎞 <b>Qismlar soni:</b> {len(episodes)}\n\n"
        "Kerakli qismni tanlang:"
    )
    
    # Pagination for Episodes
    pagination = Pagination(
        objects=episodes,
        page_data=lambda p: AdminMenuCallback(
            section="season_view", movie_id=movie_id, season_number=season_number, page=p
        ).pack(),
        item_data=lambda item, p: AdminMenuCallback(
            section="episode_view", episode_id=item.id, page=1
        ).pack(),
        item_title=lambda item, p: str(item.episode_number),
    )
    
    markup = pagination.create(page=page, lines=5, columns=5)
    builder = InlineKeyboardBuilder.from_markup(markup)
    
    # Admin Actions
    builder.row(types.InlineKeyboardButton(
        text="➕ Qism qo'shish",
        callback_data=AdminMenuCallback(section="episode_add", movie_id=movie_id, season_number=season_number).pack()
    ))
    
    builder.row(types.InlineKeyboardButton(
        text="🗑 Faslni o'chirish",
        callback_data=AdminMenuCallback(section="season_delete", movie_id=movie_id, season_number=season_number).pack()
    ))
    
    builder.row(types.InlineKeyboardButton(
        text="🔙 Orqaga",
        callback_data=AdminMenuCallback(section="movie_manage", movie_id=movie_id).pack()
    ))
    
    await call.message.edit_text(
        text,
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

@router.callback_query(AdminMenuCallback.filter(F.section == "season_delete"))
async def ask_delete_season(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    movie_id = callback_data.movie_id
    season_number = callback_data.season_number
    
    await call.message.edit_text(
        f"⚠️ <b>Rostan ham {season_number}-faslni o'chirmoqchimisiz?</b>\n"
        "Ushbu fasldagi barcha qismlar o'chiriladi!",
        reply_markup=admin_builder(
            {
                "✅ Ha, o'chirish": {"section": "season_delete_confirm", "movie_id": movie_id, "season_number": season_number}
            },
            footer_details={
                "❌ Yo'q, qaytish": {"section": "season_view", "movie_id": movie_id, "season_number": season_number}
            }
        ),
        parse_mode="HTML"
    )

@router.callback_query(AdminMenuCallback.filter(F.section == "season_delete_confirm"))
async def delete_season_execute(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.clear()
    movie_id = callback_data.movie_id
    season_number = callback_data.season_number
    
    # Delete all episodes in this season
    await db.episodes.delete_many({"movie_id": movie_id, "season_number": season_number})
    await call.answer("🗑 Fasl o'chirildi!", show_alert=True)
    
    await call.message.edit_text(
        f"✅ {season_number}-fasl o'chirildi.",
        reply_markup=admin_builder(
            footer_details={"🔙 Kino boshqaruviga qaytish": {"section": "movie_manage", "movie_id": movie_id}}
        )
    )

@router.callback_query(AdminMenuCallback.filter(F.section == "episode_view"))
async def episode_view(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.clear()
    episode_id = callback_data.episode_id
    episode = await db.episodes.find_one({"id": episode_id})
    
    if not episode:
        await call.answer("Qism topilmadi", show_alert=True)
        return
    
    movie = await db.movies.find_one({"id": episode.movie_id})
    title = movie.title if movie else "Unknown"
    
    text = (
        f"🎥 <b>Kino:</b> {title}\n"
        f"📂 <b>Fasl:</b> {episode.season_number}\n"
        f"🎞 <b>Qism:</b> {episode.episode_number}\n\n"
        f"📝 <b>Caption:</b> {episode.caption or 'Yo‘q'}\n"
    )
    
    # Buttons
    kb = {
        "✏️ Tahrirlash": {"section": "episode_edit", "episode_id": episode_id},
        "🗑 Qismni o'chirish": {"section": "episode_delete", "episode_id": episode_id},
        "🔙 Orqaga": {"section": "season_view", "movie_id": episode.movie_id, "season_number": episode.season_number}
    }
    
    # Send file if possible? 
    # Sending file might be slow or edit_text impossible if type changes.
    # We will just show text info. User can verify file by user-mode testing. Admin mode is for management.
    
    await call.message.edit_text(
        text,
        reply_markup=admin_builder(kb, row=1),
        parse_mode="HTML"
    )

@router.callback_query(AdminMenuCallback.filter(F.section == "episode_edit"))
async def edit_episode_start(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.update_data(episode_id=callback_data.episode_id)
    await call.message.edit_text(
        "Yangi video yoki faylni yuboring:",
        reply_markup=admin_builder(
            details=None,
            footer_details={"🔙 Bekor qilish": {"section": "episode_view", "episode_id": callback_data.episode_id}}
        )
    )
    await state.set_state(AdminState.waiting_for_new_episode_file)

@router.message(AdminState.waiting_for_new_episode_file, F.video | F.document)
async def save_edited_episode(message: Message, state: FSMContext):
    data = await state.get_data()
    episode_id = data.get("episode_id")
    
    if message.video:
        file_id = message.video.file_id
        caption = message.caption
    else:
        file_id = message.document.file_id
        caption = message.caption
        
    await db.episodes.update_one(
        {"id": episode_id},
        {"$set": {"file_id": file_id, "caption": caption}}
    )
    
    await message.answer(f"✅ Qism yangilandi!")
    
    # Reload view
    # We need to call episode_view manually or via message.
    # We'll use message.answer with simple text and markup.
    
    episode = await db.episodes.find_one({"id": episode_id})
    movie = await db.movies.find_one({"id": episode.movie_id})
    title = movie.title if movie else "Unknown"
    
    text = (
        f"🎥 <b>Kino:</b> {title}\n"
        f"📂 <b>Fasl:</b> {episode.season_number}\n"
        f"🎞 <b>Qism:</b> {episode.episode_number}\n\n"
        f"📝 <b>Caption:</b> {episode.caption or 'Yo‘q'}\n"
    )
    
    kb = {
        "✏️ Tahrirlash": {"section": "episode_edit", "episode_id": episode_id},
        "🗑 Qismni o'chirish": {"section": "episode_delete", "episode_id": episode_id},
        "🔙 Orqaga": {"section": "season_view", "movie_id": episode.movie_id, "season_number": episode.season_number}
    }
    
    await message.answer(
        text,
        reply_markup=admin_builder(kb, row=1),
        parse_mode="HTML"
    )
    await state.clear()

@router.callback_query(AdminMenuCallback.filter(F.section == "episode_delete"))
async def ask_delete_episode(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    episode_id = callback_data.episode_id
    await call.message.edit_text(
        "⚠️ <b>Rostan ham ushbu qismni o'chirmoqchimisiz?</b>",
        reply_markup=admin_builder(
            {
                "✅ Ha, o'chirish": {"section": "episode_delete_confirm", "episode_id": episode_id}
            },
            footer_details={
                "❌ Yo'q, qaytish": {"section": "episode_view", "episode_id": episode_id}
            }
        ),
        parse_mode="HTML"
    )

@router.callback_query(AdminMenuCallback.filter(F.section == "episode_delete_confirm"))
async def delete_episode_execute(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.clear()
    episode_id = callback_data.episode_id
    episode = await db.episodes.find_one({"id": episode_id})
    
    if episode:
        movie_id = episode.movie_id
        season_number = episode.season_number
        await db.episodes.delete_one({"id": episode_id})
        await call.answer("🗑 Qism o'chirildi!", show_alert=True)
        
        await call.message.edit_text(
            f"✅ {episode.episode_number}-qism o'chirildi.",
            reply_markup=admin_builder(
                footer_details={"🔙 Faslga qaytish": {"section": "season_view", "movie_id": movie_id, "season_number": season_number}}
            )
        )
    else:
        await call.answer("Qism topilmadi", show_alert=True)

@router.message(AdminState.waiting_for_season_number)
async def ask_episode(message: Message, state: FSMContext):
    try:
        season = int(message.text)
    except ValueError:
        await message.answer("Raqam kiriting!")
        return
    
    await state.update_data(season_number=season)
    await message.answer("Qism raqamini kiriting (masalan: 1):")
    await state.set_state(AdminState.waiting_for_episode_number)

@router.message(AdminState.waiting_for_episode_number)
async def ask_file(message: Message, state: FSMContext):
    try:
        episode = int(message.text)
    except ValueError:
        await message.answer("Raqam kiriting!")
        return
        
    await state.update_data(episode_number=episode)
    await message.answer("Endi videoni (yoki faylni) yuboring:")
    await state.set_state(AdminState.waiting_for_file)

@router.message(AdminState.waiting_for_file)
async def save_episode(message: Message, state: FSMContext):
    data = await state.get_data()
    movie_id = data['movie_id']
    season = data['season_number']
    episode_num = data['episode_number']
    
    real_file_id = None
    if message.video:
        real_file_id = message.video.file_id
        caption = message.caption
    elif message.document:
        real_file_id = message.document.file_id
        caption = message.caption
    else:
        await message.answer("Video yoki fayl kuting!")
        return

    # Upload to DB Channel
    if config.DB_CHANNEL:
        try:
            # Clean Channel ID for link
            channel_id_str = str(config.DB_CHANNEL)
            if channel_id_str.startswith("-100"):
                clean_chat_id = channel_id_str[4:]
            else:
                clean_chat_id = channel_id_str.replace("-", "")

            # Send to channel
            sent_msg = await message.bot.send_video( # Changed bot to message.bot
                chat_id=config.DB_CHANNEL,
                video=real_file_id,
                caption=caption
            )
            
            # Save Link
            file_id = f"https://t.me/c/{clean_chat_id}/{sent_msg.message_id}"
        except Exception as e:
            await message.answer(f"⚠️ Kanalga yuklashda xatolik: {e}\nOddiy fayl sifatida saqlanmoqda.")
            file_id = real_file_id
    else:
        file_id = real_file_id
    
    new_id = str(uuid.uuid4())[:8]
    ep_data = {
        "id": new_id, 
        "movie_id": movie_id, 
        "season_number": season, 
        "episode_number": episode_num,
        "file_id": file_id,
        "caption": caption
    }
    
    await db.episodes.insert_one(ep_data)
    
    await message.answer(
        f"✅ {season}-mavsum {episode_num}-qism saqlandi!",
        reply_markup=admin_builder(
            {"Faslga qaytish": {"section": "season_view", "movie_id": movie_id, "season_number": season}},
            footer_details={"Bosh menyu": {"section": "main"}}
        )
    )
    await state.clear()


# --- Admins Management ---
@router.callback_query(AdminMenuCallback.filter(F.section == "admins"))
async def manage_admins_menu(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.clear()
    
    admins = await db.admins.find({})
    admin_list_text = ""
    for idx, admin in enumerate(admins, 1):
        name = admin.full_name if hasattr(admin, 'full_name') and admin.full_name else "Admin"
        
        # If name is default, try to fetch real name
        if name == "Admin":
            try:
                chat = await call.bot.get_chat(admin.id)
                name = chat.full_name
                # Update DB
                await db.admins.update_one({"id": admin.id}, {"full_name": name})
            except Exception:
                pass

        admin_list_text += f"{idx}. <b>{name}</b> (<code>{admin.id}</code>)\n"
        
    text = (
        "👤 <b>Adminlar ro'yxati:</b>\n\n"
        f"{admin_list_text}\n"
        "Quyidagi amallardan birini tanlang:"
    )
    
    with suppress(TelegramBadRequest):
        await call.message.edit_text(
            text,
            reply_markup=admin_builder(
                {
                    "➕ Admin qo'shish": {"section": "admin_add"},
                    "➖ Admin o'chirish": {"section": "admin_delete"},
                },
                footer_details={"🔙 Bosh menyu": {"section": "main"}}
            ),
            parse_mode="HTML"
        )

@router.callback_query(AdminMenuCallback.filter(F.section == "admin_add"))
async def add_admin_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "Yangi adminning <b>Telegram ID</b> raqamini yuboring yoki uning xabarini shu yerga <b>Forward</b> qiling:",
        reply_markup=admin_builder(details=None, footer_details={"🔙 Bekor qilish": {"section": "admins"}})
    )
    await state.set_state(AdminState.waiting_for_admin_id)



@router.message(AdminState.waiting_for_admin_id)
async def save_new_admin(message: Message, state: FSMContext):
    user_id = None
    full_name = "Admin"
    
    if message.forward_from:
        user_id = message.forward_from.id
        full_name = message.forward_from.full_name
    elif message.text and message.text.isdigit():
        user_id = int(message.text)
        try:
             chat = await message.bot.get_chat(user_id)
             full_name = chat.full_name
        except:
             pass
    
    if not user_id:
        await message.answer("⚠️ ID aniqlanmadi. Iltimos, ID raqam yuboring yoki xabar forward qiling.")
        return

    # Check if existing
    existing = await db.admins.find_one({"id": user_id})
    if existing:
        await message.answer("ℹ️ Bu foydalanuvchi allaqachon admin!")
    else:
        await db.admins.insert_one({"id": user_id, "full_name": full_name})
        await message.answer(f"✅ Yangi admin qo'shildi: <b>{full_name}</b> (<code>{user_id}</code>)", parse_mode="HTML")
    
    await state.clear()
    # Go back to admin menu logic (via message)
    # Re-fetch admins for display
    admins = await db.admins.find({})
    admin_list_text = ""
    for idx, admin in enumerate(admins, 1):
        name = admin.full_name if hasattr(admin, 'full_name') and admin.full_name else "Admin"
        admin_list_text += f"{idx}. <b>{name}</b> (<code>{admin.id}</code>)\n"

    await message.answer(
        "👤 <b>Adminlar ro'yxati:</b>\n\n"
        f"{admin_list_text}\n"
        "Quyidagi amallardan birini tanlang:",
        reply_markup=admin_builder(
            {
                "➕ Admin qo'shish": {"section": "admin_add"},
                "➖ Admin o'chirish": {"section": "admin_delete"},
            },
            footer_details={"🔙 Bosh menyu": {"section": "main"}}
        ),
        parse_mode="HTML"
    )


@router.callback_query(AdminMenuCallback.filter(F.section == "admin_delete"))
async def list_admins_for_delete(call: CallbackQuery, state: FSMContext):
    await state.clear()
    admins = await db.admins.find({}) # Returns cursor/list
    
    kb = {}
    for admin in admins:
        name = admin.full_name if hasattr(admin, 'full_name') and admin.full_name else "Admin"
        
        # If name is default, try to fetch real name
        if name == "Admin":
            try:
                chat = await call.bot.get_chat(admin.id)
                name = chat.full_name
                # Update DB
                await db.admins.update_one({"id": admin.id}, {"full_name": name})
            except Exception:
                pass
                
        kb[f"🗑 {name}"] = {"section": "admin_delete_confirm", "user_id": admin.id}
    
    if not kb:
        await call.answer("Adminlar ro'yxati bo'sh!", show_alert=True)
        return

    await call.message.edit_text(
        "O'chirmoqchi bo'lgan adminni tanlang:",
        reply_markup=admin_builder(
            kb,
            row=2,
            footer_details={"🔙 Orqaga": {"section": "admins"}}
        )
    )

@router.callback_query(AdminMenuCallback.filter(F.section == "admin_delete_confirm"))
async def delete_admin_confirm(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    target_id = callback_data.user_id
    
    if target_id == call.from_user.id:
        await call.answer("❌ O'zingizni o'chira olmaysiz!", show_alert=True)
        return

    delete_result = await db.admins.delete_one({"id": target_id})
    
    if delete_result.deleted_count > 0:
        await call.answer(f"✅ Admin {target_id} o'chirildi", show_alert=True)
        # Manually refresh list
        # We can just call list_admins_for_delete logic again
        # We'll just invoke it by messaging.
        # Re-send list
        await list_admins_for_delete(call, state)
    else:
        await call.answer("❌ Xatolik: Admin topilmadi", show_alert=True)


# --- Statistics ---
@router.callback_query(AdminMenuCallback.filter(F.section == "stats"))
async def admin_stats(call: CallbackQuery, state: FSMContext):
    await state.clear()
    
    users = await db.users.count({})
    admins = await db.admins.count({})
    categories = await db.categories.count({})
    movies = await db.movies.count({})
    episodes = await db.episodes.count({})
    
    text = (
        "📊 <b>Bot Statistikasi</b>\n\n"
        f"👥 <b>Foydalanuvchilar:</b> {users}\n"
        f"👤 <b>Adminlar:</b> {admins}\n"
        f"📂 <b>Kategoriyalar:</b> {categories}\n"
        f"🎥 <b>Kinolar:</b> {movies}\n"
        f"🎞 <b>Qismlar:</b> {episodes}\n"
    )
    
    await call.message.edit_text(
        text,
        reply_markup=admin_builder(
            details=None,
            footer_details={"🔙 Orqaga": {"section": "main"}}
        ),
        parse_mode="HTML"
    )


# --- Channels Management ---
@router.callback_query(AdminMenuCallback.filter(F.section == "channels"))
async def manage_channels_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    channels = await db.channels.find({})
    
    kb = {}
    for ch in channels:
        # Dynamically fetch title if possible, else use ID
        try:
           chat = await call.bot.get_chat(ch.id)
           title = chat.title
        except:
           title = f"ID: {ch.id}"
           
        kb[f"🗑 {title}"] = {"section": "channel_delete", "channel_id": ch.id}

    await call.message.edit_text(
        "📢 <b>Majburiy Obuna Kanallari</b>\n\n"
        "Yangi kanal qo'shish uchun + tugmasini bosing.\n"
        "O'chirish uchun kanal nomini tanlang.",
        reply_markup=admin_builder(
            kb,
            row=1,
            footer_details={
                "➕ Kanal qo'shish": {"section": "channel_add"},
                "🔙 Bosh menyu": {"section": "main"}
            }
        ),
        parse_mode="HTML"
    )

@router.callback_query(AdminMenuCallback.filter(F.section == "channel_add"))
async def add_channel_start(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "Yangi kanalni qo'shish uchun:\n\n"
        "1. Botni kanalga <b>Admin</b> qiling.\n"
        "2. Kanaldan birorta xabarni shu yerga <b>Forward</b> qiling (yoki ID sini yuboring).",
        reply_markup=admin_builder(details=None, footer_details={"🔙 Bekor qilish": {"section": "channels"}})
    )
    await state.set_state(AdminState.waiting_for_channel_id)

@router.message(AdminState.waiting_for_channel_id)
async def save_channel(message: Message, state: FSMContext):
    channel_id = None
    url = None
    
    if message.forward_from_chat:
        channel_id = message.forward_from_chat.id
        if message.forward_from_chat.username:
             url = f"https://t.me/{message.forward_from_chat.username}"
    elif message.text:
        # Try parse ID or Link? Simple ID for now
        # Or if link: t.me/joinchat/...
        if message.text.startswith("-100") or message.text.lstrip("-").isdigit():
            channel_id = int(message.text)
    
    if not channel_id:
        await message.answer("⚠️ Kanal ID si aniqlanmadi. Iltimos, xabar forward qiling yoki ID yuboring.")
        return

    # 1. Check if bot is admin
    try:
        member = await message.bot.get_chat_member(channel_id, message.bot.id)
        if member.status != "administrator":
            await message.answer("🚫 Bot ushbu kanalda admin emas! Iltimos, avval botga admin huquqini bering.")
            return
    except Exception as e:
        await message.answer(f"❌ Xatolik: Kanal topilmadi yoki bot admin emas.\n{e}")
        return

    # 2. If private, need Invite Link.
    # We can try export_chat_invite_link if we don't have one
    if not url:
        try:
             chat = await message.bot.get_chat(channel_id)
             if chat.username:
                 url = f"https://t.me/{chat.username}"
             else:
                 # Private
                 # Try to get existing link or create one
                 url = await message.bot.export_chat_invite_link(channel_id)
        except:
             pass 
    
    # 3. Save
    existing = await db.channels.find_one({"id": channel_id})
    if existing:
        await message.answer("ℹ️ Bu kanal allaqachon qo'shilgan!")
    else:
        await db.channels.insert_one({"id": channel_id, "url": url})
        await message.answer("✅ Kanal muvaffaqiyatli qo'shildi!")
    
    await state.clear()
    # Go back to list (need to call handler logic, but via message is safer)
    # We'll just show menu
    await message.answer(
        "Kanallar boshqaruvi:",
        reply_markup=admin_builder(
            {"Menyuga qaytish": {"section": "channels"}},
            footer_details={"Bosh menyu": {"section": "main"}}
        )
    )

@router.callback_query(AdminMenuCallback.filter(F.section == "channel_delete"))
async def delete_channel(call: CallbackQuery, callback_data: AdminMenuCallback, state: FSMContext):
    await state.clear()
    channel_id = callback_data.channel_id
    await db.channels.delete_one({"id": channel_id})
    await call.answer("🗑 Kanal o'chirildi", show_alert=True)
    
    await manage_channels_menu(call, state)


# --- Broadcast ---
@router.callback_query(AdminMenuCallback.filter(F.section == "broadcast_start"))
async def start_broadcast_handler(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text(
        "📨 <b>Xabar yuborish</b>\n\n"
        "Barcha foydalanuvchilarga yubormoqchi bo'lgan xabaringizni shu yerga yozing yoki forward qiling.\n"
        "Matn, Rasm, Video, Audio — hammasi mumkin.",
        reply_markup=admin_builder(details=None, footer_details={"🔙 Bekor qilish": {"section": "main"}}),
        parse_mode="HTML"
    )
    await state.set_state(AdminState.waiting_for_broadcast_message)


@router.message(AdminState.waiting_for_broadcast_message)
async def perform_broadcast(message: Message, state: FSMContext):
    # Determine message data
    # We will simply copy this message ID to everyone.
    
    # Notify admin that process started
    status_msg = await message.answer("⏳ Tarqatish boshlandi... 0 ta yuborildi.")
    
    # Start background task
    asyncio.create_task(broadcast_worker(message, status_msg))
    
    await state.clear()
    await message.answer(
        "✅ Tarqatish jarayoni fonda ketmoqda. Siz botdan foydalanishda davom etishingiz mumkin.",
        reply_markup=admin_builder({"Menyu": {"section": "main"}})
    )

async def broadcast_worker(source_message: Message, status_message: Message):
    sent_count = 0
    failed_count = 0
    total_users = await db.users.count({})
    
    # Iterate users
    # Note: For strict 100k+ efficiency, we should paginate. 
    # But pymongo Cursor is already iterable.
    cursor = db.users.collection.find({}, {"id": 1}).sort("id", 1) 
    
    start_time = asyncio.get_running_loop().time()
    
    async for user in cursor:
        user_id = user["id"]
        try:
            await source_message.copy_to(chat_id=user_id)
            sent_count += 1
        except TelegramForbiddenError:
            # Bot blocked
            failed_count += 1
        except TelegramRetryAfter as e:
            # Rate limit hit, wait and retry
            await asyncio.sleep(e.retry_after)
            try:
                await source_message.copy_to(chat_id=user_id)
                sent_count += 1
            except:
                failed_count += 1
        except Exception:
            failed_count += 1
        
        # Periodic update (every 200 users or enough time passed)
        if (sent_count + failed_count) % 200 == 0:
            try:
                await status_message.edit_text(
                    f"⏳ Tarqatilmoqda...\n\n"
                    f"✅ Yuborildi: {sent_count}\n"
                    f"❌ Xatolik/Blok: {failed_count}\n"
                    f"📊 Jami: {sent_count + failed_count} / {total_users}"
                )
            except:
                pass
        
        # Rate limit safety (approx 25 msgs/sec)
        await asyncio.sleep(0.04)

    # Final Report
    try:
        await status_message.edit_text(
             f"🏁 <b>Tarqatish yakunlandi!</b>\n\n"
             f"✅ Muvaffaqiyatli: {sent_count}\n"
             f"❌ Xatolik/Blok: {failed_count}\n"
             f"👥 Jami urishlar: {sent_count + failed_count}",
             parse_mode="HTML"
        )
    except:
        pass

