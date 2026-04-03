import os, time
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from database import get_user_data, increment_usage, set_thumbnail, is_banned, set_watermark
from PIL import Image, ImageDraw, ImageFont

router = Router()

# --- Small Caps ---
def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

# --- ওয়াটারমার্ক ফাংশন (UPDATED) ---
async def apply_watermark(bot, photo_file_id, text):
    path = f"wm_{time.time()}.jpg"
    file = await bot.get_file(photo_file_id)
    await bot.download_file(file.file_path, path)

    with Image.open(path) as img:
        img = img.convert("RGB")
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # 🔥 SUPER BIG FONT
        font_size = int(width / 8)   # আগের চেয়ে অনেক বড়

        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()

        text_bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]

        # center bottom (visible)
        x = (width - tw) // 2
        y = height - th - 80

        # 🔥 BLACK BOX (strong visibility)
        draw.rectangle(
            [x - 25, y - 25, x + tw + 25, y + th + 25],
            fill=(0, 0, 0)
        )

        # 🔥 WHITE TEXT + BORDER EFFECT
        draw.text((x-2, y-2), text, font=font, fill=(0,0,0))
        draw.text((x+2, y+2), text, font=font, fill=(0,0,0))
        draw.text((x, y), text, font=font, fill=(255,255,255))

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
    await message.reply(
        f"✅ {small_caps('watermark saved:')} <code>{args[1]}</code>\n{small_caps('enable from /settings')}",
        parse_mode="HTML"
    )

# --- EXTRACT THUMBNAIL (FIXED) ---
@router.message(Command("extract"))
async def extract_handler(message: types.Message, bot: Bot):
    if await is_banned(message.from_user.id): return

    if not message.reply_to_message:
        return await message.reply("❌ Reply to a video or file!")

    target = message.reply_to_message.video or message.reply_to_message.document

    if not target:
        return await message.reply("❌ No valid file found!")

    # 🔥 DEBUG MESSAGE (important)
    await message.reply("⏳ Extracting thumbnail...")

    thumb = None

    try:
        if getattr(target, "thumbnail", None):
            thumb = target.thumbnail
        elif getattr(target, "thumb", None):
            thumb = target.thumb
    except Exception as e:
        return await message.reply(f"❌ Error: {e}")

    # ❗ যদি thumbnail না থাকে
    if not thumb:
        return await message.reply("❌ This file has NO thumbnail!")

    btn = [[types.InlineKeyboardButton(
        text="🖼️ USE THIS",
        callback_data=f"use_this_{thumb.file_id}"
    )]]

    await bot.send_photo(
        chat_id=message.chat.id,
        photo=thumb.file_id,
        caption="✅ Thumbnail Extracted!",
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btn)
        )

# --- MAIN VIDEO HANDLER ---
@router.message(F.video | F.document)
async def video_handler(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    if await is_banned(user_id): return

    user = await get_user_data(user_id)
    if not user or not user.get("thumbnail"):
        return await message.reply(small_caps("❌ send a photo first to set thumbnail!"))

    file_obj = message.video or message.document

    status = await message.reply_sticker("CAACAgUAAxkBAAKGfGnNPmV4Bwsx_0W1Qk8h6p3Q423nAALbEAACdYaYVO2S9fNnW52THgQ")

    raw_name = getattr(file_obj, 'file_name', 'video.mp4')
    clean_name = os.path.splitext(raw_name)[0].replace("_", " ").replace(".", " ")

    user_caption = user.get("caption", "{filename}")
    final_caption = user_caption.replace("{filename}", clean_name) if user.get("caption_on", True) else (message.caption or "")

    temp_path = None
    thumb_id = user["thumbnail"]

    try:
        # 🔥 WATERMARK APPLY
        if user.get("watermark_on") and user.get("watermark"):
            temp_path = await apply_watermark(bot, thumb_id, user["watermark"])
            cover = types.FSInputFile(temp_path)
        else:
            cover = thumb_id

        if message.video:
            await bot.send_video(
                chat_id=message.chat.id,
                video=file_obj.file_id,
                caption=final_caption,
                cover=cover,
                supports_streaming=True
            )
        else:
            await bot.send_document(
                chat_id=message.chat.id,
                document=file_obj.file_id,
                caption=final_caption,
                thumbnail=cover
            )

        await increment_usage(user_id)

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")

    finally:
        await status.delete()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

# --- CALLBACK SAVE THUMB ---
@router.callback_query(F.data.startswith("use_this_"))
async def use_extracted_thumb(query: types.CallbackQuery):
    file_id = query.data.replace("use_this_", "")
    await set_thumbnail(query.from_user.id, file_id)
    await query.answer("✅ Thumbnail Saved!", show_alert=True)
    await query.message.edit_caption(
        caption=small_caps("✅ this is now your default thumbnail!")
            )
