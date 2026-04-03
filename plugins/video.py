import os, asyncio, time
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from database import get_user_data, increment_usage, set_thumbnail, is_banned, set_watermark
from PIL import Image, ImageDraw, ImageFont

router = Router()

def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

# --- ওয়াটারমার্ক প্রসেসিং (শুধুমাত্র যখন ওয়াটারমার্ক অন থাকবে) ---
async def apply_watermark(bot, photo_file_id, text):
    path = f"wm_{time.time()}.jpg"
    file = await bot.get_file(photo_file_id)
    await bot.download_file(file.file_path, path)
    with Image.open(path) as img:
        img = img.convert("RGB")
        draw = ImageDraw.Draw(img)
        width, height = img.size
        font = ImageFont.load_default()
        text_bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = text_bbox[2]-text_bbox[0], text_bbox[3]-text_bbox[1]
        x, y = width - tw - 20, height - th - 20
        draw.rectangle([x-5, y-5, x+tw+5, y+th+5], fill=(0,0,0,140))
        draw.text((x, y), text, font=font, fill=(255,255,255))
        img.save(path, "JPEG", quality=90)
    return path

# --- ফটো থাম্বনেইল হিসেবে সেট করা ---
@router.message(F.photo)
async def direct_photo_handler(message: types.Message):
    if await is_banned(message.from_user.id): return
    file_id = message.photo[-1].file_id
    await set_thumbnail(message.from_user.id, file_id)
    await message.reply(small_caps("✅ thumbnail saved successfully!"))

# --- ওয়াটারমার্ক সেট করা ---
@router.message(Command("watermark"))
async def set_wm_cmd(message: types.Message):
    if await is_banned(message.from_user.id): return
    args = message.text.split(None, 1)
    if len(args) < 2: return await message.reply(small_caps("❌ usage: /watermark @PrimeXBots"))
    await set_watermark(message.from_user.id, args[1])
    await message.reply(f"✅ {small_caps('watermark text saved:')} <code>{args[1]}</code>\n{small_caps('enable it from /settings')}", parse_mode="HTML")

# --- এক্সট্র্যাক্ট কমান্ড (রিপ্লাই সিস্টেম) ---
@router.message(Command("extract"))
async def extract_handler(message: types.Message, bot: Bot):
    if await is_banned(message.from_user.id): return
    
    # রিপ্লাই চেক
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.reply(small_caps("❌ reply to a video with /extract to get its thumbnail!"))

    target = message.reply_to_message.video or message.reply_to_message.document
    if not target.thumbnail:
        return await message.reply(small_caps("❌ no thumbnail found in this file!"))

    btn = [[types.InlineKeyboardButton(text="🖼️ USE THIS AS THUMBNAIL", callback_data=f"use_this_{target.thumbnail.file_id}")]]
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=target.thumbnail.file_id,
        caption=small_caps("✅ thumbnail extracted successfully!"),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btn)
    )

# --- মেইন ভিডিও হ্যান্ডলার (আপনার অরিজিনাল কোড অনুযায়ী) ---
@router.message(F.video | F.document)
async def video_handler(message: types.Message, bot: Bot):
    user_id = message.from_user.id
    if await is_banned(user_id): return
    
    user = await get_user_data(user_id)
    if not user or not user.get("thumbnail"):
        return await message.reply(small_caps("❌ please set a thumbnail first by sending a photo!"))

    file_obj = message.video or message.document
    
    # Sticker Animation
    status_sticker = await message.reply_sticker("CAACAgUAAxkBAAKGfGnNPmV4Bwsx_0W1Qk8h6p3Q423nAALbEAACdYaYVO2S9fNnW52THgQ")

    # Clean Name
    raw_name = getattr(file_obj, 'file_name', 'video.mp4')
    clean_name = os.path.splitext(raw_name)[0].replace("_", " ").replace(".", " ")
    
    # Caption Logic
    user_caption = user.get("caption", "{filename}")
    if user.get("caption_on", True):
        final_caption = user_caption.replace("{filename}", clean_name)
    else:
        final_caption = message.caption if message.caption else ""

    temp_path = None
    thumb_id = user["thumbnail"]

    try:
        # যদি ওয়াটারমার্ক অন থাকে তবেই ছবি প্রসেস হবে
        if user.get("watermark_on") and user.get("watermark"):
            temp_path = await apply_watermark(bot, thumb_id, user["watermark"])
            cover_to_send = types.FSInputFile(temp_path)
        else:
            # যদি ওয়াটারমার্ক অফ থাকে তবে সরাসরি file_id ব্যবহার হবে (দ্রুততম পদ্ধতি)
            cover_to_send = thumb_id

        if message.video:
            await bot.send_video(
                chat_id=message.chat.id,
                video=file_obj.file_id,
                caption=final_caption,
                cover=cover_to_send, # অরিজিনাল কভার প্যারামিটার
                supports_streaming=True
            )
        else:
            # ডকুমেন্টের জন্য thumbnail প্যারামিটার ব্যবহার হয়
            await bot.send_document(
                chat_id=message.chat.id,
                document=file_obj.file_id,
                caption=final_caption,
                thumbnail=cover_to_send
            )
        
        await increment_usage(user_id)
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
    finally:
        await status_sticker.delete()
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)

# --- বাটন কলব্যাক ---
@router.callback_query(F.data.startswith("use_this_"))
async def use_extracted_thumb(query: types.CallbackQuery):
    file_id = query.data.replace("use_this_", "")
    await set_thumbnail(query.from_user.id, file_id)
    await query.answer("✅ Thumbnail Set Successfully!", show_alert=True)
    await query.message.edit_caption(caption=small_caps("✅ this is now your default thumbnail!"))
    
