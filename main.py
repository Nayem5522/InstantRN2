# CantarellaBots
# Don't Remove Credit
# Telegram Channel @CantarellaBots
#Supoort group @rexbotschat
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio
from flask import Flask
import threading
import os
# CantarellaBots
# Don't Remove Credit
# Telegram Channel @CantarellaBots
#Supoort group @rexbotschat
from config import API_TOKEN
from database import init_db, close_db
from plugins import start_router, settings_router, video_router, admin_router
# CantarellaBots
# Don't Remove Credit
# Telegram Channel @CantarellaBots
#Supoort group @rexbotschat
# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
# CantarellaBots
# Don't Remove Credit
# Telegram Channel @CantarellaBots
#Supoort group @rexbotschats
# Register routers
dp.include_router(start_router)
dp.include_router(settings_router)
dp.include_router(video_router)
dp.include_router(admin_router)
# CantarellaBots
# Don't Remove Credit
# Telegram Channel @CantarellaBots
#Supoort group @rexbotschat
# Flask health check server
app = Flask(__name__)

# CantarellaBots
# Don't Remove Credit
# Telegram Channel @CantarellaBots
#Supoort group @rexbotschat
@app.route("/")
def home():
    return "Bot Made By @CantarellaBots"

# CantarellaBots
# Don't Remove Credit
# Telegram Channel @CantarellaBots
#Supoort group @rexbotschat
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

# CantarellaBots
# Don't Remove Credit
# Telegram Channel @CantarellaBots
#Supoort group @rexbotschats
async def main():
    # Initialize database
    await init_db()
    print("🚀 Bot is starting...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await close_db()

# CantarellaBots
# Don't Remove Credit
# Telegram Channel @CantarellaBots
#Supoort group @rexbotschat
if __name__ == "__main__":
    print(r"""
   ______            __                  __  __        ____        __       
  / ____/___ _____  / /_____ _________  / / / /___ _  / __ )____  / /______ 
 / /   / __ `/ __ \/ __/ __ `/ ___/ _ \/ / / / __ `/ / __  / __ \/ __/ ___/ 
/ /___/ /_/ / / / / /_/ /_/ / /  /  __/ / / / /_/ / / /_/ / /_/ / /_(__  )  
\____/\__,_/_/ /_/\__/\__,_/_/   \___/_/_/_/\__,_/ /_____/\____/\__/____/   
                                                                            
      BOT WORKING PROPERLY....
    """)
    print("Starting Bot...")
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
# CantarellaBots
# Don't Remove Credit
# Telegram Channel @CantarellaBots
#Supoort group @rexbotschat# CantarellaBots
# Don't Remove Credit
# Telegram Channel @CantarellaBots
#Supoort group @rexbotschat# CantarellaBots
# Don't Remove Credit
# Telegram Channel @CantarellaBots
#Supoort group @rexbotschat
