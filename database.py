from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional, List, Dict, Any
from config import MONGO_URL, DB_NAME, OWNER_ID

client: AsyncIOMotorClient = None
db = None


# ================= DB INIT =================
async def init_db():
    global client, db
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]

    await db.users.create_index("user_id", unique=True)
    await db.admins.create_index("user_id", unique=True)

    await add_admin(OWNER_ID)
    print("MongoDB Connected ✅")


async def close_db():
    global client
    if client:
        client.close()


# ================= USER =================
async def add_user(user_id: int, username: str = None, first_name: str = None):
    await db.users.update_one(
        {"user_id": user_id},
        {
            "$set": {"username": username, "first_name": first_name},
            "$setOnInsert": {
                "user_id": user_id,
                "thumbnail": None,
                "caption": "{filename}",
                "watermark": None,
                "caption_on": True,   # নতুন: ক্যাপশন ডিফল্টভাবে ON
                "watermark_on": False, # নতুন: ওয়াটারমার্ক ডিফল্টভাবে OFF
                "usage_count": 0,
                "banned": False
            }
        },
        upsert=True
    )

async def get_user(user_id: int):
    return await db.users.find_one({"user_id": user_id})

# ================= SETTINGS =================
async def set_thumbnail(user_id: int, file_id: str):
    await db.users.update_one(
        {"user_id": user_id}, 
        {"$set": {"thumbnail": file_id}}
         )

async def set_caption(user_id: int, caption: str):
    await db.users.update_one({"user_id": user_id}, {"$set": {"caption": caption}})


# ইউজার ডাটা কল করার জন্য (এটি video.py তে ব্যবহার হয়েছে)
async def get_user_data(user_id: int):
    return await db.users.find_one({"user_id": user_id})

# ওয়াটারমার্ক টেক্সট সেভ করার জন্য
async def set_watermark(user_id: int, text: str):
    await db.users.update_one(
        {"user_id": user_id}, 
        {"$set": {"watermark": text}}
    )

# ভিডিও প্রসেসিং কাউন্ট করার জন্য
async def increment_usage(user_id: int):
    await db.users.update_one(
        {"user_id": user_id}, 
        {"$inc": {"usage_count": 1}}
    )

async def get_user_count():
    return await db.users.count_documents({})


async def get_all_users():
    return await db.users.find().to_list(length=None)


async def get_leaderboard(limit: int = 10):
    return await db.users.find(
        {"usage_count": {"$gt": 0}}
    ).sort("usage_count", -1).limit(limit).to_list(length=limit)


# ================= BAN =================
async def ban_user(user_id: int):
    await db.users.update_one({"user_id": user_id}, {"$set": {"banned": True}})
    return True


async def unban_user(user_id: int):
    await db.users.update_one({"user_id": user_id}, {"$set": {"banned": False}})
    return True


async def is_banned(user_id: int) -> bool:
    user = await db.users.find_one({"user_id": user_id})
    return user.get("banned", False) if user else False


# ================= ADMIN =================
async def add_admin(user_id: int):
    await db.admins.update_one(
        {"user_id": user_id},
        {"$set": {"user_id": user_id}},
        upsert=True
    )


async def remove_admin(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return False
    result = await db.admins.delete_one({"user_id": user_id})
    return result.deleted_count > 0


async def is_admin(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    admin = await db.admins.find_one({"user_id": user_id})
    return admin is not None


async def get_all_admins() -> List[int]:
    admins = await db.admins.find().to_list(length=None)
    return [a["user_id"] for a in admins]
    

async def toggle_setting(user_id: int, field: str):
    """ক্যাপশন বা ওয়াটারমার্ক অন/অফ করার ফাংশন"""
    user = await db.users.find_one({"user_id": user_id})
    current_status = user.get(field, False)
    # স্ট্যাটাস উল্টে দেওয়া (True থাকলে False, False থাকলে True)
    await db.users.update_one(
        {"user_id": user_id}, 
        {"$set": {field: not current_status}}
    )
    return not current_status
    
async def remove_thumbnail(user_id: int):
    """ইউজারের সেট করা থাম্বনেইল ডিলিট করার ফাংশন"""
    await db.users.update_one(
        {"user_id": user_id}, 
        {"$set": {"thumbnail": None}}
    )
    return True
