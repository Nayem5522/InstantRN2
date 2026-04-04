import os, time, uuid
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from database import get_user_data, increment_usage, set_thumbnail, is_banned, set_watermark
from PIL import Image, ImageDraw, ImageFont

router = Router()

TEMP_THUMBS = {}

def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

# ✅ WATERMARK
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
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()

        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]

        x = (width - tw) // 2
        y = height - th - 40

        draw.rectangle([x-10, y-10, x+tw+10, y+th+10], fill=(0,0,0))
        draw.text((x+1, y+1), text, font=font, fill=(0,0,0))
        draw.text((x, y), text, font=font, fill=(255,255,255))

        img.save(path, "JPEG", quality=95)

    return path

# ✅ SAVE THUMB
@router.message(F.photo)
async def save_thumb(message: types.Message):
    if await is_banned(message.from_user.id): return
    await set_thumbnail(message.from_user.id, message.photo[-1].file_id)
    await message.reply(small_caps("✅ thumbnail saved!"))

# ✅ EXTRACT (FIXED FULL)
@router.message(Command("extract"))
async def extract_handler(message: types.Message, bot: Bot):
    if await is_banned(message.from_user.id): return

    if not message.reply_to_message:
        return await message.reply("❌ Reply to a video/file!")

    target = message.reply_to_message.video or message.reply_to_message.document

    if not target:
        return await message.reply("❌ Invalid file!")

    msg = await message.reply("⏳ Extracting...")

    thumb = getattr(target, "thumbnail", None) or getattr(target, "thumb", None)

    if not thumb:
        return await msg.edit_text("❌ No thumbnail found!")

    try:
        file = await bot.get_file(thumb.file_id)
        path = f"thumb_{time.time()}.jpg"
        await bot.download_file(file.file_path, path)

        key = str(uuid.uuid4())[:8]

        # 🔥 SAVE REAL FILE_ID (important fix)
        TEMP_THUMBS[key] = thumb.file_id

        btn = [[types.InlineKeyboardButton(
            text="🖼️ USE THIS",
            callback_data=f"use_this_{key}"
        )]]

        await bot.send_photo(
            message.chat.id,
            types.FSInputFile(path),
            caption="✅ Thumbnail Extracted!",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btn)
        )

        os.remove(path)
        await msg.delete()

    except Exception as e:
        await msg.edit_text(f"❌ Failed: {e}")

# ✅ CALLBACK SAVE (FIXED MAIN ISSUE)
@router.callback_query(F.data.startswith("use_this_"))
async def use_thumb(query: types.CallbackQuery):
    key = query.data.replace("use_this_", "")
    file_id = TEMP_THUMBS.get(key)

    if not file_id:
        return await query.answer("❌ Expired!", show_alert=True)

    # 🔥 DIRECT SAVE (this fix your main issue)
    await set_thumbnail(query.from_user.id, file_id)

    await query.answer("✅ Thumbnail Saved!", show_alert=True)
    await query.message.edit_caption("✅ Saved as your thumbnail!")

    TEMP_THUMBS.pop(key, None)

# ✅ VIDEO HANDLER (same but stable)
@router.message(F.video | F.document)
async def video_handler(message: types.Message, bot: Bot):
    user = await get_user_data(message.from_user.id)
    if not user or not user.get("thumbnail"):
        return await message.reply("❌ Set thumbnail first!")

    file_obj = message.video or message.document
    thumb_id = user["thumbnail"]

    try:
        if user.get("watermark_on") and user.get("watermark"):
            temp = await apply_watermark(bot, thumb_id, user["watermark"])
            cover = types.FSInputFile(temp)
        else:
            cover = thumb_id

        if message.video:
            await bot.send_video(message.chat.id, file_obj.file_id, cover=cover)
        else:
            await bot.send_document(message.chat.id, file_obj.file_id, thumbnail=cover)

        await increment_usage(message.from_user.id)

    except Exception as e:
        await message.reply(f"❌ Error: {e}")
        
