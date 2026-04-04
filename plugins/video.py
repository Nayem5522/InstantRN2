import os, time, asyncio
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from database import get_user_data, increment_usage, set_thumbnail, is_banned, set_watermark
from PIL import Image, ImageDraw, ImageFont

router = Router()

def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

async def apply_watermark(bot, photo_id, text):
    path = f"wm_{time.time()}.jpg"
    f = await bot.get_file(photo_id)
    await bot.download_file(f.file_path, path)
    with Image.open(path) as img:
        img = img.convert("RGB")
        draw = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        draw.text((20, 20), text, font=font, fill=(255,255,255))
        img.save(path)
    return path

@router.message(F.photo)
async def photo_handler(message: types.Message):
    if await is_banned(message.from_user.id): return
    await set_thumbnail(message.from_user.id, message.photo[-1].file_id)
    await message.reply(small_caps("✅ thumbnail saved successfully!"))

@router.message(Command("watermark"))
async def wm_cmd(message: types.Message):
    args = message.text.split(None, 1)
    if len(args) < 2: return await message.reply("Usage: /watermark [text]")
    await set_watermark(message.from_user.id, args[1])
    await message.reply("✅ Watermark saved!")

@router.message(Command("extract"))
async def extract_handler(message: types.Message, bot: Bot):
    if not message.reply_to_message: return await message.reply("Reply to a video!")
    target = message.reply_to_message.video or message.reply_to_message.document
    if not target or not target.thumbnail: return await message.reply("No thumbnail found!")
    
    btn = [[types.InlineKeyboardButton(text="🖼️ USE THIS", callback_data=f"use_ex_{target.thumbnail.file_id}")]]
    await bot.send_photo(chat_id=message.chat.id, photo=target.thumbnail.file_id, caption="✅ Extracted!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btn))

@router.callback_query(F.data.startswith("use_ex_"))
async def use_ex(q: types.CallbackQuery):
    await set_thumbnail(q.from_user.id, q.data.replace("use_ex_", ""))
    await q.answer("Saved ✅", show_alert=True)

@router.message(F.video | F.document)
async def video_handler(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    if await is_banned(user_id): return
    user = await get_user_data(user_id)
    if not user or not user.get("thumbnail"): return await message.reply("Set a thumbnail first!")

    file_obj = message.video or message.document
    status = await message.reply_sticker("CAACAgUAAxkBAAKGfGnNPmV4Bwsx_0W1Qk8h6p3Q423nAALbEAACdYaYVO2S9fNnW52THgQ")
    
    clean_name = os.path.splitext(getattr(file_obj, 'file_name', 'video.mp4'))[0].replace("_", " ")
    caption = user.get("caption", "{filename}").replace("{filename}", clean_name) if user.get("caption_on") else (message.caption or "")

    temp_path = None
    # Validation Error এড়াতে থাম্বনেইল ডাউনলোড করে পাঠানো হচ্ছে
    path = f"t_{user_id}.jpg"
    f = await bot.get_file(user["thumbnail"])
    await bot.download_file(f.file_path, path)
    
    if user.get("watermark_on") and user.get("watermark"):
        temp_path = await apply_watermark(bot, user["thumbnail"], user["watermark"])
        thumb = types.FSInputFile(temp_path)
    else:
        thumb = types.FSInputFile(path)
        temp_path = path

    try:
        if message.video:
            await bot.send_video(chat_id=message.chat.id, video=file_obj.file_id, caption=caption, thumbnail=thumb, supports_streaming=True)
        else:
            await bot.send_document(chat_id=message.chat.id, document=file_obj.file_id, caption=caption, thumbnail=thumb)
        await increment_usage(user_id)
    except Exception as e: await message.reply(f"Error: {e}")
    finally:
        await status.delete()
        if temp_path and os.path.exists(temp_path): os.remove(temp_path)
        if os.path.exists(path): os.remove(path)
            
