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

from aiogram.filters import Command, CommandObject

@router.message(Command("watermark"))
async def set_wm_cmd(message: types.Message, command: CommandObject):
    if await is_banned(message.from_user.id):
        return

    wm_text = command.args

    if not wm_text:
        return await message.reply(
            "❌ Usage:\n<code>/watermark Your Text Here</code>",
            parse_mode="HTML"
        )

    try:
        await set_watermark(message.from_user.id, wm_text)

        await message.reply(
            f"✅ Watermark Saved:\n<code>{wm_text}</code>\n\n⚙️ Enable it from Settings",
            parse_mode="HTML"
        )
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# ✅ EXTRACT (FIXED FULL)
@router.message(Command("extract"))
async def extract_handler(message: types.Message, bot: Bot):
    if await is_banned(message.from_user.id): return

    if not message.reply_to_message:
        return await message.reply("❌ Reply to a video/file!")

    target = message.reply_to_message.video or message.reply_to_message.document

    if not target:
        return await message.reply("❌ Invalid file!")

    # 🔥 PROCESSING STICKER
    status = await message.reply_sticker(
        "CAACAgUAAxkBAAKGfGnNPmV4Bwsx_0W1Qk8h6p3Q423nAALbEAACdYaYVO2S9fNnW52THgQ"
    )

    thumb = getattr(target, "thumbnail", None) or getattr(target, "thumb", None)

    if not thumb:
        await status.delete()
        return await message.reply("❌ No thumbnail found!")

    try:
        file = await bot.get_file(thumb.file_id)
        path = f"thumb_{time.time()}.jpg"
        await bot.download_file(file.file_path, path)

        sent = await bot.send_photo(
            chat_id=message.chat.id,
            photo=types.FSInputFile(path),
            caption="🖼️ Extracted Thumbnail"
        )

        new_file_id = sent.photo[-1].file_id

        import uuid
        key = str(uuid.uuid4())[:8]
        TEMP_THUMBS[key] = new_file_id

        btn = [[types.InlineKeyboardButton(
            text="✅ USE THIS AS THUMBNAIL",
            callback_data=f"use_this_{key}"
        )]]

        await bot.send_message(
            chat_id=message.chat.id,
            text="👇 Click below to set this thumbnail",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btn)
        )

        os.remove(path)

    except Exception as e:
        await message.reply(f"❌ Failed: {e}")

    finally:
        # 🔥 STICKER DELETE
        await status.delete()
        
# ✅ CALLBACK SAVE (FIXED MAIN ISSUE)
@router.callback_query(F.data.startswith("use_this_"))
async def use_thumb(query: types.CallbackQuery):
    key = query.data.replace("use_this_", "")
    file_id = TEMP_THUMBS.get(key)

    if not file_id:
        return await query.answer("❌ Expired!", show_alert=True)

    await set_thumbnail(query.from_user.id, file_id)

    await query.answer("✅ Thumbnail Saved!", show_alert=True)
    await query.message.edit_text("✅ Saved as your thumbnail!")

    TEMP_THUMBS.pop(key, None)

# ✅ VIDEO HANDLER (same but stable)
@router.message(F.video | F.document)
async def video_handler(message: types.Message, bot: Bot):
    user = await get_user_data(message.from_user.id)

    if not user or not user.get("thumbnail"):
        return await message.reply("❌ Set thumbnail first!")

    file_obj = message.video or message.document
    thumb_id = user["thumbnail"]

    # 🔥 PROCESSING STICKER
    status = await message.reply_sticker(
        "CAACAgUAAxkBAAKGfGnNPmV4Bwsx_0W1Qk8h6p3Q423nAALbEAACdYaYVO2S9fNnW52THgQ"
    )

    # ✅ CAPTION FIX
    raw_name = getattr(file_obj, 'file_name', 'video.mp4')
    clean_name = os.path.splitext(raw_name)[0]

    user_caption = user.get("caption", "{filename}")

    if user.get("caption_on", True):
        final_caption = user_caption.replace("{filename}", clean_name)
    else:
        final_caption = message.caption or ""

    temp_path = None

    try:
        if user.get("watermark_on") and user.get("watermark"):
            temp_path = await apply_watermark(bot, thumb_id, user["watermark"])
            cover = types.FSInputFile(temp_path)
        else:
            cover = thumb_id

        if message.video:
            await bot.send_video(
                message.chat.id,
                file_obj.file_id,
                caption=final_caption,
                cover=cover,
                supports_streaming=True
            )
        else:
            await bot.send_document(
                message.chat.id,
                file_obj.file_id,
                caption=final_caption,
                thumbnail=cover
            )

        await increment_usage(message.from_user.id)

    except Exception as e:
        await message.reply(f"❌ Error: {e}")

    finally:
        await status.delete()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
