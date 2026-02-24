from aiogram import Router, F, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest
from contextlib import suppress
import re

from src.database.collections import db
from src.loader import bot
from src.utils.callbackdata import UserMenuCallback
from src.utils.keyboards import user_builder
from src.utils.paginations import Pagination
from src.filters.chattype import ChatTypeFilter

router = Router()
router.callback_query.filter(ChatTypeFilter(private=True))

@router.callback_query(F.data == "check_subscription")
async def check_subscription_success(call: types.CallbackQuery):
    await call.message.delete()
    
    text = (
        f"🎬 Xush kelibsiz {call.from_user.mention_html()}!\n\n"
        "Bu bot orqali siz:\n"
        "— 🎥 Eng so‘nggi kinolar\n"
        "— 📺 Eng mashhur seriallar\n"
        "— 🔥 Trend kontentlar\n"
        "— ⚡ Tez va qulay tomosha\n\n"
        "👇 Davom etish uchun menyuni oching"
    )

    await call.message.answer(
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

@router.callback_query(UserMenuCallback.filter(F.section == "menu"))
async def show_categories(call: types.CallbackQuery, callback_data: UserMenuCallback):
    """
    Show list of categories.
    """
    categories = await db.categories.find(count=50) # Limit 50 for now
    
    keyboard_dict = {}
    for cat in categories:
        keyboard_dict[cat.title] = {
            "section": "category",
            "category_id": cat.id,
        }
    
    markup = user_builder(keyboard_dict, row=2, footer_details={"🔙 Orqaga": {"section": "start"}})
    
    if call.message.content_type != "text":
        await call.message.delete()
        await call.message.answer("📂 Kategoriya tanlang:", reply_markup=markup)
    else:
        with suppress(TelegramBadRequest):
            await call.message.edit_text("📂 Kategoriya tanlang:", reply_markup=markup)

@router.callback_query(UserMenuCallback.filter(F.section == "category"))
async def show_movies(call: types.CallbackQuery, callback_data: UserMenuCallback):
    """
    Show list of movies in a category.
    """
    category_id = callback_data.category_id
    category = await db.categories.find_one({"id": category_id})
    cat_title = category.title if category else "Kategoriya"
    
    # Simple pagination could be added here using callback_data.page
    movies = await db.movies.find({"category_id": category_id}, count=50)
    
    keyboard_dict = {}
    for movie in movies:
        keyboard_dict[movie.title] = {
            "section": "movie",
            "movie_id": movie.id,
        }
        
    markup = user_builder(keyboard_dict, row=2, footer_details={"🔙 Orqaga": {"section": "menu"}})
    
    if call.message.content_type != "text":
        await call.message.delete()
        await call.message.answer(f"📂 {cat_title} — kinolar:", reply_markup=markup)
    else:
        with suppress(TelegramBadRequest):
            await call.message.edit_text(f"📂 {cat_title} — kinolar:", reply_markup=markup)

@router.callback_query(UserMenuCallback.filter(F.section == "movie"))
async def show_seasons(call: types.CallbackQuery, callback_data: UserMenuCallback):
    """
    Show seasons for a movie/series.
    """
    movie_id = callback_data.movie_id
    movie = await db.movies.find_one({"id": movie_id})
    title = movie.title if movie else "Kino"
    
    # Get distinct seasons. Note: Collection wrapper might not have distinct, accessing raw collection
    # OR retrieving all episodes (expensive) and set-ing. 
    # Let's try raw collection access if possible, or just find all episodes projection.
    # The wrapper is db.episodes.collection
    try:
        seasons = await db.episodes.collection.distinct("season_number", {"movie_id": movie_id})
        seasons.sort()
    except Exception:
        # Fallback if distinct not working or driver issues
        episodes = await db.episodes.find({"movie_id": movie_id})
        seasons = sorted(list(set(e.season_number for e in episodes)))

    if not seasons:
        await call.answer("Bu kinoga hali qismlar yuklanmagan 😔", show_alert=True)
        return

    # Auto-skip if only 1 season
    if len(seasons) == 1:
        # Construct callback for Season View (Ep 1)
        cb = UserMenuCallback(
            section="season_view", 
            movie_id=movie_id, 
            season_number=seasons[0], 
            episode_number=1, 
            page=1
        )
        await show_episode_content(call, cb)
        return

    keyboard_dict = {}
    for s in seasons:
        keyboard_dict[f"{s}-mavsum"] = {
            "section": "season_view", # view handled separately
            "movie_id": movie_id,
            "season_number": s,
            "episode_number": 1, # Start from ep 1
            "page": 1 
        }
        
    markup = user_builder(
        keyboard_dict, 
        row=2, 
        footer_details={"🔙 Orqaga": {"section": "category", "category_id": movie.category_id}}
    )
    
    if call.message.content_type != "text":
        await call.message.delete()
        await call.message.answer(f"📺 {title} — mavsumni tanlang:", reply_markup=markup)
    else:
        with suppress(TelegramBadRequest):
            await call.message.edit_text(f"📺 {title} — mavsumni tanlang:", reply_markup=markup)


@router.callback_query(UserMenuCallback.filter(F.section == "season_view"))
async def show_episode_content(call: types.CallbackQuery, callback_data: UserMenuCallback):
    """
    Shows the actual episode video + pagination.
    """
    movie_id = callback_data.movie_id
    season = callback_data.season_number
    episode_num = callback_data.episode_number
    page = callback_data.page # For chunking episode buttons if too many

    # Find the specific episode
    episode = await db.episodes.find_one({
        "movie_id": movie_id, 
        "season_number": season,
        "episode_number": episode_num
    })

    if not episode:
        await call.answer(f"{season}-mavsum, {episode_num}-qism topilmadi.", show_alert=True)
        return

    # Prepare Pagination for Episodes
    all_season_eps = await db.episodes.find({"movie_id": movie_id, "season_number": season})
    all_season_eps.sort(key=lambda x: x.episode_number)
    
    # Use Pagination class
    layout = Pagination(
        objects=all_season_eps,
        page_data=lambda page: UserMenuCallback(
            section="season_view", movie_id=movie_id, season_number=season, episode_number=episode_num, page=page
        ).pack(),
        item_data=lambda item, page: UserMenuCallback(
            section="season_view", movie_id=movie_id, season_number=season, episode_number=item.episode_number, page=page
        ).pack(),
        item_title=lambda item, page: f"· {item.episode_number} ·" if item.episode_number == episode_num else str(item.episode_number),
    )
    
    markup = layout.create(page=page, lines=2, columns=5)
    
    # Check seasons count for Back button optimization
    seasons_cnt = 0
    try:
        dist_seasons = await db.episodes.collection.distinct("season_number", {"movie_id": movie_id})
        seasons_cnt = len(dist_seasons)
    except:
        # Fallback
        seasons_cnt = 2 # Assume multiple to be safe if fails, so it goes to movie view

    # Add Back button
    builder = InlineKeyboardBuilder.from_markup(markup)
    
    back_target = {}

    caption = (
        f"🎬 <b>{episode_num}-qism</b> | {season}-mavsum\n"
        f"{(episode.caption if episode.caption else '')}"
    )

    if seasons_cnt == 1:
        # Go back to Category (skip movie/season view loop)
        # We need category_id. Fetch movie to get it.
        caption = (
            f"{(episode.caption if episode.caption else '')}"
        )
        mov = await db.movies.find_one({"id": movie_id})
        cat_id = mov.category_id if mov else None
        if cat_id:
             back_target = UserMenuCallback(section="category", category_id=cat_id).pack()
        else:
             back_target = UserMenuCallback(section="menu").pack()
    else:
        # Go back to Season Selection (standard)
        back_target = UserMenuCallback(section="movie", movie_id=movie_id).pack()

    # Determine if file_id is a link or a telegram file_id
    file_id = episode.file_id
    is_link = file_id.startswith("http") or "t.me/" in file_id

    # Add Watch Button if it's a link - REMOVED AS PER REQUEST
    # if is_link:
    #     builder.row(InlineKeyboardButton(text="🎥 Videoni ko'rish", url=file_id))
    
    # Check if we are editing or sending new - Back button is always needed
    builder.row(InlineKeyboardButton(text="🔙 Orqaga", callback_data=back_target))

    try:
        # If it is a link, we cannot "edit_media" from a video to a text+link easily if previous was video.
        # But we can try to send a new message or specific behavior.
        
        if is_link:
            # Try to copy the message from the channel using the link
            # Link format: https://t.me/c/123456789/123
            match = re.search(r"t\.me\/c\/(\d+)\/(\d+)", file_id)
            
            sent_copy = False
            message_deleted = False

            if match:
                try:
                    chat_id_suffix = match.group(1)
                    message_id_ref = int(match.group(2))
                    # Construct full private channel ID: -100 + suffix
                    # Construct full private channel ID: -100 + suffix
                    from_chat_id = int(f"-100{chat_id_suffix}")
                    
                    # Try to delete previous message (safe to ignore if already deleted)
                    with suppress(TelegramBadRequest):
                        await call.message.delete()
                        message_deleted = True 
                    
                    print(f"DEBUG: Copying Msg={message_id_ref} from Chat={from_chat_id}") # Debug print
                    
                    await bot.copy_message(
                        chat_id=call.from_user.id,
                        from_chat_id=from_chat_id,
                        message_id=message_id_ref,
                        caption=caption,
                        parse_mode="HTML",
                        reply_markup=builder.as_markup()
                    )
                    sent_copy = True
                except Exception as e:
                    print(f"❌ Error copying video: {e}")
                    # e.g. Message deleted, Bot not admin, or ID format wrong
                    pass

            if not sent_copy:
                 # Fallback: Send Text indicating failure.
                 # User requested NO BUTTON.
                msg_text = (
                    f"{caption}\n\n"
                    "⚠️ Videoni yuklab bo'lmadi. Administratorga murojaat qiling."
                )
                
                # If we already deleted the message (attempting copy), we MUST answer new.
                if message_deleted:
                     await call.message.answer(msg_text, reply_markup=builder.as_markup(), parse_mode="HTML")
                
                # If message exists (video or doc), delete & answer (legacy logic)
                elif call.message.video or call.message.document:
                     await call.message.delete()
                     await call.message.answer(msg_text, reply_markup=builder.as_markup(), parse_mode="HTML")
                
                # Else try to edit text
                else:
                     with suppress(TelegramBadRequest):
                        await call.message.edit_text(msg_text, reply_markup=builder.as_markup(), parse_mode="HTML")


        else:
            # Legacy File ID behavior (Send Video)
            if call.message.video or call.message.document:
                 media = types.InputMediaVideo(media=file_id, caption=caption, parse_mode="HTML")
                 with suppress(TelegramBadRequest):
                    await call.message.edit_media(media=media, reply_markup=builder.as_markup())
            else:
                 # Previous was text, delete it and send video
                 await call.message.delete()
                 await call.message.answer_video(
                     video=file_id,
                     caption=caption,
                     reply_markup=builder.as_markup(),
                     parse_mode="HTML"
                 )
                 
    except TelegramBadRequest as e:
        # Fallback
        if "not modified" in str(e):
             await call.answer()
        elif "no text in the message to edit" in str(e):
             await call.message.delete()
             if is_link:
                  await call.message.answer(msg_text, reply_markup=builder.as_markup(), parse_mode="HTML")
             else:
                  await call.message.answer_video(video=file_id, caption=caption, reply_markup=builder.as_markup(), parse_mode="HTML")
        else:
             await call.answer("Xatolik yuz berdi.", show_alert=True)
             
