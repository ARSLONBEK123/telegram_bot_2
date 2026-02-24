import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.database.collections import db

async def clean_users():
    print("🧹 Cleaning duplicate users...")
    
    # 1. Pipeline to find duplicates
    pipeline = [
        {"$group": {
            "_id": "$id",  # Group by user ID
            "count": {"$sum": 1},
            "docs": {"$push": "$_id"} # Store ObjectId of all duplicates
        }},
        {"$match": {
            "count": {"$gt": 1} # Only those with > 1 entry
        }}
    ]

    duplicates = await db.users.collection.aggregate(pipeline).to_list(length=None)
    
    total_removed = 0
    users_fixed = 0

    if not duplicates:
        print("✅ No duplicates found.")
    else:
        print(f"⚠️ Found {len(duplicates)} users with duplicates.")
        
        for item in duplicates:
            user_id = item["_id"]
            doc_ids = item["docs"]
            
            # Keep the first one (or last One, doesn't matter much if data is same)
            # We'll keep the first one encountered (usually oldest)
            # doc_ids is a list of ObjectIds
            
            to_remove = doc_ids[1:] # Skip the first one, remove the rest
            
            if to_remove:
                await db.users.collection.delete_many({"_id": {"$in": to_remove}})
                total_removed += len(to_remove)
                users_fixed += 1
                print(f"   👤 User {user_id}: Removed {len(to_remove)} duplicates.")

    print(f"\n──────────────────────────")
    print(f"🎉 Process Complete!")
    print(f"👥 Users Fixed: {users_fixed}")
    print(f"🗑 Total Deleted Entries: {total_removed}")
    print(f"──────────────────────────")

    # Optional: Create Unique Index to prevent future duplicates
    print("🔒 Ensuring Unique Index on 'id'...")
    await db.users.collection.create_index("id", unique=True)
    print("✅ Index created.")

if __name__ == "__main__":
    asyncio.run(clean_users())
