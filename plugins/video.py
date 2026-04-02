import os
import asyncio
from aiogram import Router, types, F, Bot
from database import get_user_data, increment_usage, set_thumbnail, is_banned

router = Router()

def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

@router.message(F.photo)
async def direct_photo_handler(message: types.Message):
    if await is_banned(message.from_user.id): return
    file_id = message.photo[-1].file_id
    await set_thumbnail(message.from_user.id, file_id)
    await message.reply(small_caps("✅ thumbnail saved successfully!"))

@router.message(F.video | F.document)
async def video_handler(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    if await is_banned(user_id): return
    
    user = await get_user_data(user_id)
    if not user or not user.get("thumbnail"):
        return await message.reply(small_caps("❌ please set a thumbnail first by sending a photo!"))

    file_obj = message.video or message.document
    if not file_obj: return

    # Sticker Animation
    status_sticker = await message.reply_sticker("CAACAgUAAxkBAAKGfGnNPmV4Bwsx_0W1Qk8h6p3Q423nAALbEAACdYaYVO2S9fNnW52THgQ")
    await asyncio.sleep(2) 

    # Clean Name
    raw_name = getattr(file_obj, 'file_name', 'video.mp4')
    clean_name = os.path.splitext(raw_name)[0].replace("_", " ").replace(".", " ")
    
    # Caption Replace
    user_caption = user.get("caption", "{filename}")
    final_caption = user_caption.replace("{filename}", clean_name)

    try:
        # এখানে reply_markup দেওয়া হয়নি, তাই ভিডিওর নিচে কোনো বাটন থাকবে না
        await bot.send_video(
            chat_id=message.chat.id,
            video=file_obj.file_id,
            caption=final_caption,
            cover=user["thumbnail"],
            supports_streaming=True
        )
        await increment_usage(user_id, file_obj.file_id)
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
    finally:
        await status_sticker.delete()
