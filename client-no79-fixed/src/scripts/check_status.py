import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

# Import AFTER creating the path
from src.loader import bot
from src.database.collections import db

async def check_status():
    print("Checking database status...")
    
    # Count all episodes
    total = await db.episodes.collection.count_documents({})
    
    # Count migrated (starts with https://t.me/)
    migrated = await db.episodes.collection.count_documents({"file_id": {"$regex": "^https://t.me/"}})
    
    # Count remaining (legacy file_id)
    # We assume anything NOT starting with http is legacy
    remaining = await db.episodes.collection.count_documents({"file_id": {"$not": {"$regex": "^http"}}})
    
    print(f"\n--- STATISTIKA ---")
    print(f"Jami qismlar: {total}")
    print(f"Migratsiya bo'lgan: {migrated}")
    print(f"Qolgan: {remaining}")
    print(f"---------------------")
    
    if remaining == 0:
        print("XAMMASI TUGADI! Barcha fayllar havolaga aylantirildi.")
    else:
        print(f"Hali {remaining} ta qism qoldi. Migratsiya skriptini qayta ishga tushiring.")

    await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(check_status())
    except KeyboardInterrupt:
        pass
