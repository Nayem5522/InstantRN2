import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from flask import Flask
import threading
import os
from config import API_TOKEN
from plugins import start_router, video_router, settings_router, admin_router

# Flask health check for Render/Heroku
app = Flask(__name__)
@app.route("/")
def home(): return "Bot is Alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

async def main():
    bot = Bot(token=API_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register Routers
    dp.include_router(start_router)
    dp.include_router(video_router)
    dp.include_router(settings_router)
    dp.include_router(admin_router)
    
    print("🚀 PrimeSnapThumb Bot Started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(main())
