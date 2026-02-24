import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.loader import bot
from src.config import config
from src.database.collections import db
from aiogram.exceptions import TelegramRetryAfter

async def migrate_files():
    print("Migration started...")
    
    if not config.DB_CHANNEL:
        print("DB_CHANNEL is not set in .env! Please set it first.")
        return

    # Extract channel ID without -100 prefix for private link
    # Example: -100123456789 -> 123456789
    channel_id_str = str(config.DB_CHANNEL)
    if channel_id_str.startswith("-100"):
        clean_chat_id = channel_id_str[4:]
    else:
        clean_chat_id = channel_id_str.replace("-", "")

    # Get all episodes using raw collection for efficiency
    cursor = db.episodes.collection.find({})
    
    count = 0
    updated = 0
    skipped = 0
    
    print(f"Target Channel ID: {config.DB_CHANNEL}")
    print(f"Link Prefix: https://t.me/c/{clean_chat_id}/")

    async for episode in cursor:
        count += 1
        file_id = episode.get("file_id")
        episode_id = episode.get("id")
        caption = episode.get("caption", "")

        if not file_id:
            print(f"[WARN] Episode {episode_id} has no file_id. Skipping.")
            continue

        # Check if already a link
        if file_id.startswith("http") or "t.me/" in file_id:
            print(f"[SKIP] Episode {episode_id} is already a link. Skipping.")
            skipped += 1
            continue

        print(f"[PROC] Processing Episode {episode_id}...")

        try:
            # Send video to channel
            # We use send_video with existing file_id (Telegram allows resending by ID)
            msg = await bot.send_video(
                chat_id=config.DB_CHANNEL, 
                video=file_id, 
                caption=caption
            )
            
            # Construct Link
            # https://t.me/c/1234567890/123
            new_link = f"https://t.me/c/{clean_chat_id}/{msg.message_id}"
            
            # Update DB
            await db.episodes.collection.update_one(
                {"_id": episode["_id"]},
                {"$set": {"file_id": new_link}}
            )
            
            print(f"[OK] Migrated: {new_link}")
            updated += 1
            
            # Sleep to avoid FloodWait
            await asyncio.sleep(2)

        except TelegramRetryAfter as e:
            print(f"[WAIT] FloodWait: Sleeping {e.retry_after} seconds...")
            await asyncio.sleep(e.retry_after)
            # Retry logic could be added here, but for now simple skip/fail
            print(f"[FAIL] Failed Episode {episode_id} due to FloodWait (skipped for now)")
        
        except Exception as e:
            print(f"[ERR] Error processing {episode_id}: {e}")
            await asyncio.sleep(1)

    print(f"\nMigration Complete!")
    print(f"Total: {count}")
    print(f"Updated: {updated}")
    print(f"Skipped: {skipped}")

    await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(migrate_files())
    except KeyboardInterrupt:
        print("Migration stopped.")
