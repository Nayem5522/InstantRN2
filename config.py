import os
import random

# Telegram API & Bot Token
API_TOKEN = os.environ.get("API_TOKEN", "")
MONGO_URL = os.environ.get("MONGO_URL", "")
DB_NAME = os.environ.get("DB_NAME", "PrimeSnapThumb_DB")
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

# Force Subscribe Channel ID (e.g., -100xxxx)
AUTH_CHANNEL = os.environ.get("AUTH_CHANNEL", "") 

# URLs for Buttons
CHANNEL_URL = "https://t.me/PrimeXBots"
MOVIE_CHANNEL = "https://t.me/PrimeCineZone"
SUPPORT_GROUP = "https://t.me/Prime_Support_group"
CREATOR_URL = "https://t.me/Prime_Nayem"
ADMIN_URL = "https://t.me/Prime_Admin_Support_ProBot"

# UI Images
START_PIC = "https://i.postimg.cc/DzfVh49m/file-000000009e2471fab7304fc4d4b26799.png"
SOURCE_PIC = "https://i.postimg.cc/hvFZ93Ct/file-000000004188623081269b2440872960.png"

def get_random_pic() -> str:
    """Get a random image from START_PICS."""
    if START_PICS:
        return random.choice(START_PICS)
    return None
