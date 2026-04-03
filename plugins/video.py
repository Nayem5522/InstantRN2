import os, asyncio, time
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import get_user_data, increment_usage, set_thumbnail, is_banned, set_watermark
from PIL import Image, ImageDraw, ImageFont

router = Router()

class VideoStates(StatesGroup):
    waiting_for_extract = State()

def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

# --- ওয়াটারমার্ক ফাংশন ---
async def apply_watermark(bot, photo_file_id, text):
    path = f"temp_{time.time()}.jpg"
    await bot.download(photo_file_id, destination=path)
    
    with Image.open(path) as img:
        draw = ImageDraw.Draw(img)
        width, height = img.size
        # সাধারণ ফন্ট সাইজ (ছবির ১০% সাইজ অনুযায়ী)
        font_size = int(height * 0.05)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # ডানদিকের নিচে ওয়াটারমার্ক বসানো
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = width - text_width - 20
        y = height - text_height - 20
        
        # হালকা ব্যাকগ্রাউন্ড বক্স (যাতে টেক্সট বোঝা যায়)
        draw.rectangle([x-5, y-5, x+text_width+5, y+text_height+5], fill=(0,0,0,100))
        draw.text((x, y), text, font=font, fill=(255, 255, 255, 200))
        img.save(path)
    
    return path

# --- ফটো থাম্বনেইল হিসেবে সেভ করা ---
@router.message(F.photo)
async def direct_photo_handler(message: types.Message):
    if await is_banned(message.from_user.id): return
    file_id = message.photo[-1].file_id
    await set_thumbnail(message.from_user.id, file_id)
    await message.reply(small_caps("✅ thumbnail saved successfully!"))

# --- এক্সট্র্যাক্ট কমান্ড ---
@router.message(Command("extract"))
async def extract_cmd(message: types.Message, state: FSMContext):
    await message.reply(small_caps("📤 send the video now to extract its thumbnail!"))
    await state.set_state(VideoStates.waiting_for_extract)

# --- ওয়াটারমার্ক সেট করা ---
@router.message(Command("watermark"))
async def set_wm_cmd(message: types.Message):
    args = message.text.split(None, 1)

    if len(args) < 2:
        return await message.reply(
            small_caps("❌ usage: /watermark @PrimeXBots")
        )

    wm_text = args[1].strip()

    await set_watermark(message.from_user.id, wm_text)
    await message.reply(
        f"✅ {small_caps('watermark set to:')} <code>{wm_text}</code>",
        parse_mode="HTML"
    )


@router.message(Command("watermark_off"))
async def remove_wm_cmd(message: types.Message):
    await set_watermark(message.from_user.id, None)
    await message.reply(small_caps("✅ watermark disabled!"))
# --- ভিডিও এবং ডকুমেন্ট হ্যান্ডলার ---
@router.message(F.video | F.document)
async def video_handler(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    if await is_banned(user_id): return
    
    current_state = await state.get_state()
    file_obj = message.video or message.document
    if not file_obj: return

    # যদি এক্সট্র্যাক্ট মোড চালু থাকে
    if current_state == VideoStates.waiting_for_extract:
        await state.clear()
        if not file_obj.thumbnail:
            return await message.reply(small_caps("❌ this file doesn't have a thumbnail to extract!"))
        
        btn = [[types.InlineKeyboardButton(text="🖼️ USE THIS AS THUMBNAIL", callback_data=f"use_this_{file_obj.thumbnail.file_id}")]]
        markup = types.InlineKeyboardMarkup(inline_keyboard=btn)
        return await bot.send_photo(chat_id=user_id, photo=file_obj.thumbnail.file_id, caption=small_caps("extracted thumbnail!"), reply_markup=markup)

    # সাধারণ থাম্বনেইল প্রসেসিং
    user = await get_user_data(user_id)
    if not user or not user.get("thumbnail"):
        return await message.reply(small_caps("❌ please set a thumbnail first by sending a photo!"))

    status_sticker = await message.reply_sticker("CAACAgUAAxkBAAKGfGnNPmV4Bwsx_0W1Qk8h6p3Q423nAALbEAACdYaYVO2S9fNnW52THgQ")
    
    raw_name = getattr(file_obj, 'file_name', 'video.mp4')
    clean_name = os.path.splitext(raw_name)[0].replace("_", " ").replace(".", " ")
    user_caption = user.get("caption", "{filename}")
    final_caption = user_caption.replace("{filename}", clean_name)

    # ওয়াটারমার্ক থাকলে সেটি যোগ করা
    thumb_to_use = user["thumbnail"]
    temp_path = None
    if user.get("watermark"):
        temp_path = await apply_watermark(bot, thumb_to_use, user["watermark"])
        thumb_to_use = types.FSInputFile(temp_path)

    try:
        if message.video:
            await bot.send_video(
                chat_id=message.chat.id,
                video=file_obj.file_id,
                caption=final_caption,
                thumbnail=thumb_to_use,
                supports_streaming=True
            )
        else:
            await bot.send_document(
                chat_id=message.chat.id,
                document=file_obj.file_id,
                caption=final_caption,
                thumbnail=thumb_to_use
            )
        await increment_usage(user_id)
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
    finally:
        await status_sticker.delete()
        if temp_path and os.path.exists(temp_path): os.remove(temp_path)

# --- থাম্বনেইল বাটনের কলব্যাক ---
@router.callback_query(F.data.startswith("use_this_"))
async def use_extracted_thumb(query: types.CallbackQuery):
    file_id = query.data.replace("use_this_", "")
    await set_thumbnail(query.from_user.id, file_id)
    await query.answer("✅ Thumbnail Set Successfully!", show_alert=True)
    await query.message.edit_caption(caption=small_caps("✅ this is now your default thumbnail!"))
    
