import os, time, uuid
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from database import get_user_data, increment_usage, set_thumbnail, is_banned, set_watermark
from PIL import Image, ImageDraw, ImageFont

router = Router()
TEMP_THUMBS = {}

# --- Small Caps ---
def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

# --- ওয়াটারমার্ক ফাংশন ---
async def apply_watermark(bot, photo_file_id, text):
    path = f"wm_{time.time()}.jpg"
    file = await bot.get_file(photo_file_id)
    await bot.download_file(file.file_path, path)

    with Image.open(path) as img:
        img = img.convert("RGB")
        draw = ImageDraw.Draw(img)
        width, height = img.size
        font_size = int(width / 18)

        try:
            # সার্ভারে ফন্ট না থাকলে ডিফল্ট লোড হবে
            font = ImageFont.load_default() 
        except:
            font = ImageFont.load_default()

        text_bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        x = (width - tw) // 2
        y = height - th - 40
        
        padding = 10
        draw.rectangle([x - padding, y - padding, x + tw + padding, y + th + padding], fill=(0, 0, 0))
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
        img.save(path, "JPEG", quality=95)
    return path

# --- PHOTO → Thumbnail ---
@router.message(F.photo)
async def direct_photo_handler(message: types.Message):
    if await is_banned(message.from_user.id): return
    file_id = message.photo[-1].file_id
    await set_thumbnail(message.from_user.id, file_id)
    await message.reply(small_caps("✅ thumbnail saved successfully!"))

# --- WATERMARK SET ---
@router.message(Command("watermark"))
async def set_wm_cmd(message: types.Message):
    if await is_banned(message.from_user.id): return
    args = message.text.split(None, 1)
    if len(args) < 2:
        return await message.reply(small_caps("❌ usage: /watermark YourText"))
    await set_watermark(message.from_user.id, args[1])
    await message.reply(f"✅ {small_caps('watermark saved:')} <code>{args[1]}</code>", parse_mode="HTML")

# --- EXTRACT THUMBNAIL ---
@router.message(Command("extract"))
async def extract_handler(message: types.Message, bot: Bot):
    if await is_banned(message.from_user.id): return
    if not message.reply_to_message: return await message.reply("❌ Reply to a video/file!")
    target = message.reply_to_message.video or message.reply_to_message.document
    if not target: return await message.reply("❌ No valid file!")

    msg = await message.reply("⏳ Extracting thumbnail...")
    thumb = getattr(target, "thumbnail", None) or getattr(target, "thumb", None)
    
    if not thumb: return await msg.edit_text("❌ No thumbnail found!")

    try:
        file = await bot.get_file(thumb.file_id)
        path = f"ex_{time.time()}.jpg"
        await bot.download_file(file.file_path, path)
        key = str(uuid.uuid4())[:8]
        TEMP_THUMBS[key] = thumb.file_id

        btn = [[types.InlineKeyboardButton(text="🖼️ USE THIS", callback_data=f"use_this_{key}")]]
        await bot.send_photo(chat_id=message.chat.id, photo=types.FSInputFile(path), caption="✅ Extracted!", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btn))
        os.remove(path)
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Failed: {str(e)}")

# --- MAIN VIDEO HANDLER ---
@router.message(F.video | F.document)
async def video_handler(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    if await is_banned(user_id): return
    user = await get_user_data(user_id)
    if not user or not user.get("thumbnail"):
        return await message.reply(small_caps("❌ send a photo first!"))

    file_obj = message.video or message.document
    status = await message.reply_sticker("CAACAgUAAxkBAAKGfGnNPmV4Bwsx_0W1Qk8h6p3Q423nAALbEAACdYaYVO2S9fNnW52THgQ")
    
    clean_name = os.path.splitext(getattr(file_obj, 'file_name', 'video.mp4'))[0].replace("_", " ")
    final_caption = user.get("caption", "{filename}").replace("{filename}", clean_name) if user.get("caption_on", True) else (message.caption or "")

    temp_path = None
    thumb_id = user["thumbnail"]

    try:
        if user.get("watermark_on") and user.get("watermark"):
            temp_path = await apply_watermark(bot, thumb_id, user["watermark"])
            cover = types.FSInputFile(temp_path)
        else:
            # সরাসরি file_id না দিয়ে ডাউনলোড করে পাঠানো Aiogram 3 এ নিরাপদ
            path = f"t_{user_id}.jpg"
            f = await bot.get_file(thumb_id)
            await bot.download_file(f.file_path, path)
            cover = types.FSInputFile(path)
            temp_path = path

        if message.video:
            await bot.send_video(chat_id=message.chat.id, video=file_obj.file_id, caption=final_caption, thumbnail=cover, supports_streaming=True)
        else:
            await bot.send_document(chat_id=message.chat.id, document=file_obj.file_id, caption=final_caption, thumbnail=cover)
        await increment_usage(user_id)
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
    finally:
        await status.delete()
        if temp_path and os.path.exists(temp_path): os.remove(temp_path)

@router.callback_query(F.data.startswith("use_this_"))
async def cb_use_thumb(query: types.CallbackQuery):
    key = query.data.replace("use_this_", "")
    file_id = TEMP_THUMBS.get(key)
    if not file_id: return await query.answer("❌ Expired!", show_alert=True)
    await set_thumbnail(query.from_user.id, file_id)
    await query.answer("✅ Thumbnail Saved!", show_alert=True)
    await query.message.edit_caption(caption="✅ Saved as default!")
    TEMP_THUMBS.pop(key, None) # ব্র্যাকেট ফিক্স করা হয়েছে
