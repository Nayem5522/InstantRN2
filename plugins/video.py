import os, asyncio, time
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_user_data, increment_usage, set_thumbnail, is_banned, set_watermark
from PIL import Image, ImageDraw, ImageFont

router = Router()

# পেন্ডিং ভিডিওর জন্য স্টেট
class VideoStates(StatesGroup):
    waiting_for_custom_thumb = State()

def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

# --- ওয়াটারমার্ক প্রসেসিং ---
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

# --- ফটো হ্যান্ডলার (Permanent Save Logic) ---
@router.message(F.photo)
async def photo_handler(message: types.Message, state: FSMContext, bot: Bot):
    if await is_banned(message.from_user.id): return
    
    file_id = message.photo[-1].file_id
    await set_thumbnail(message.from_user.id, file_id) # পার্মানেন্ট সেভ
    
    current_state = await state.get_state()
    if current_state == VideoStates.waiting_for_custom_thumb:
        data = await state.get_data()
        video_msg = data.get("video_msg")
        await state.clear()
        await message.reply(small_caps("✅ thumbnail saved permanently and processing your video..."))
        await process_video_final(video_msg, bot, custom_thumb_id=file_id)
    else:
        await message.reply(small_caps("✅ thumbnail saved as your permanent default!"))

# --- এক্সট্র্যাক্ট কমান্ড (Reply Mode) ---
@router.message(Command("extract"))
async def extract_cmd(message: types.Message, bot: Bot):
    if await is_banned(message.from_user.id): return
    if not message.reply_to_message or not (message.reply_to_message.video or message.reply_to_message.document):
        return await message.reply(small_caps("❌ reply to a video with /extract to get its thumbnail!"))

    target = message.reply_to_message.video or message.reply_to_message.document
    if not target.thumbnail: return await message.reply(small_caps("❌ no thumbnail found!"))
    
    btn = [[types.InlineKeyboardButton(text="🖼️ USE THIS AS THUMBNAIL", callback_data=f"use_this_{target.thumbnail.file_id}")]]
    await bot.send_photo(chat_id=message.chat.id, photo=target.thumbnail.file_id, caption=small_caps("✅ thumbnail extracted!"), reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btn))

# --- ভিডিও হ্যান্ডলার ---
@router.message(F.video | F.document)
async def video_handler(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    if await is_banned(user_id): return
    
    user = await get_user_data(user_id)
    if not user.get("thumbnail"):
        if user.get("watermark"):
            btn = [
                [types.InlineKeyboardButton(text="🖼️ Add Custom Thumbnail", callback_data="prompt_thumb")],
                [types.InlineKeyboardButton(text="⚡ Use Original + Watermark", callback_data="use_orig_wm")]
            ]
            await state.update_data(video_msg=message)
            return await message.reply(small_caps("you haven't set a thumbnail yet. choose an option:"), reply_markup=types.InlineKeyboardMarkup(inline_keyboard=btn))
        else:
            return await message.reply(small_caps("❌ please set a thumbnail first by sending a photo!"))

    await process_video_final(message, bot)

# --- বাটন কলব্যাক হ্যান্ডলার ---
@router.callback_query(F.data == "prompt_thumb")
async def prompt_thumb_cb(query: types.CallbackQuery, state: FSMContext):
    await query.message.edit_text(small_caps("📤 please send the photo now for this video!"))
    await state.set_state(VideoStates.waiting_for_custom_thumb)

@router.callback_query(F.data == "use_orig_wm")
async def use_orig_wm_cb(query: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    video_msg = data.get("video_msg")
    await state.clear()
    file_obj = video_msg.video or video_msg.document
    if not file_obj.thumbnail: return await query.answer("❌ Video has no thumbnail!", show_alert=True)
    await query.message.delete()
    await process_video_final(video_msg, bot, custom_thumb_id=file_obj.thumbnail.file_id)

# --- ফাইনাল প্রসেসিং (Actual Video Sender) ---
async def process_video_final(message: types.Message, bot: Bot, custom_thumb_id=None):
    user_id = message.from_user.id
    user = await get_user_data(user_id)
    file_obj = message.video or message.document
    
    thumb_id = custom_thumb_id if custom_thumb_id else user.get("thumbnail")
    sticker = await message.reply_sticker("CAACAgUAAxkBAAKGfGnNPmV4Bwsx_0W1Qk8h6p3Q423nAALbEAACdYaYVO2S9fNnW52THgQ")
    
    clean_name = os.path.splitext(getattr(file_obj, 'file_name', 'video.mp4'))[0].replace("_", " ")
    final_caption = user.get("caption", "{filename}").replace("{filename}", clean_name) if user.get("caption_on", True) else (message.caption or "")

    temp_path = None
    try:
        # ওয়াটারমার্ক অন থাকলে অথবা Use Original+WM মোডে থাকলে
        if user.get("watermark_on") or (custom_thumb_id and user.get("watermark")):
            temp_path = await apply_watermark(bot, thumb_id, user["watermark"])
            thumb_input = types.FSInputFile(temp_path)
        else:
            temp_path = f"thumb_{user_id}_{time.time()}.jpg"
            file = await bot.get_file(thumb_id)
            await bot.download_file(file.file_path, temp_path)
            thumb_input = types.FSInputFile(temp_path)

        if message.video:
            await bot.send_video(chat_id=message.chat.id, video=file_obj.file_id, caption=final_caption, thumbnail=thumb_input, supports_streaming=True)
        else:
            await bot.send_document(chat_id=message.chat.id, document=file_obj.file_id, caption=final_caption, thumbnail=thumb_input)
        await increment_usage(user_id)
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
    finally:
        await sticker.delete()
        if temp_path and os.path.exists(temp_path): os.remove(temp_path)

@router.callback_query(F.data.startswith("use_this_"))
async def cb_use_thumb(query: types.CallbackQuery):
    await set_thumbnail(query.from_user.id, query.data.replace("use_this_", ""))
    await query.answer("✅ Permanent Thumbnail Updated!", show_alert=True)
    await query.message.edit_caption(caption=small_caps("✅ this is now saved as your default thumbnail!"))
    
