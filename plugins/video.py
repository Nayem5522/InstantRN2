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

# --- বুদ্ধিমান ওয়াটারমার্ক ফাংশন ---
async def apply_watermark(bot, photo_file_id, text):
    path = f"temp_{time.time()}.jpg"
    file = await bot.get_file(photo_file_id)
    await bot.download_file(file.file_path, path)
    
    with Image.open(path) as img:
        img = img.convert("RGB")
        draw = ImageDraw.Draw(img)
        width, height = img.size
        
        # ডাইনামিক ফন্ট সাইজ
        font_size = int(height * 0.04)
        try:
            # সার্ভারে অনেক সময় arial থাকে না, তাই ডিফল্ট ফন্ট হ্যান্ডেল করা হয়েছে
            font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # ওয়াটারমার্কের টেক্সট সাইজ বের করা
        text_bbox = draw.textbbox((0, 0), text, font=font)
        tw = text_bbox[2] - text_bbox[0]
        th = text_bbox[3] - text_bbox[1]
        
        # বটম রাইট পজিশন
        x, y = width - tw - 25, height - th - 25
        
        # টেক্সটের নিচে একটি হালকা কালো আভা দেওয়া (Background overlay)
        draw.rectangle([x-5, y-5, x+tw+5, y+th+5], fill=(0,0,0,120))
        draw.text((x, y), text, font=font, fill=(255, 255, 255))
        
        img.save(path, "JPEG", quality=95)
    
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
    if await is_banned(message.from_user.id): return
    await message.reply(small_caps("📤 send the video now to extract its thumbnail!"))
    await state.set_state(VideoStates.waiting_for_extract)

# --- ওয়াটারমার্ক সেট করা ---
@router.message(Command("watermark"))
async def set_wm_cmd(message: types.Message):
    if await is_banned(message.from_user.id): return
    args = message.text.split(None, 1)
    if len(args) < 2:
        return await message.reply(small_caps("❌ usage: /watermark @PrimeXBots\nTo disable: /watermark off"))
    
    wm_text = args[1].strip()
    if wm_text.lower() == "off":
        await set_watermark(message.from_user.id, None)
        await message.reply(small_caps("✅ watermark disabled!"))
    else:
        await set_watermark(message.from_user.id, wm_text)
        await message.reply(f"✅ {small_caps('watermark set to:')} <code>{wm_text}</code>", parse_mode="HTML")

# --- ভিডিও এবং ডকুমেন্ট হ্যান্ডলার ---
@router.message(F.video | F.document)
async def video_handler(message: types.Message, bot: Bot, state: FSMContext):
    user_id = message.from_user.id
    if await is_banned(user_id): return
    
    current_state = await state.get_state()
    file_obj = message.video or message.document
    if not file_obj: return

    # --- এক্সট্র্যাক্ট লজিক ---
    if current_state == VideoStates.waiting_for_extract:
        await state.clear()
        if not file_obj.thumbnail:
            return await message.reply(small_caps("❌ this file has no thumbnail to extract!"))
        
        btn = [[types.InlineKeyboardButton(text="🖼️ USE THIS AS THUMBNAIL", callback_data=f"use_this_{file_obj.thumbnail.file_id}")]]
        markup = types.InlineKeyboardMarkup(inline_keyboard=btn)
        return await bot.send_photo(chat_id=user_id, photo=file_obj.thumbnail.file_id, caption=small_caps("here is the extracted thumbnail!"), reply_markup=markup)

    # --- রেগুলার প্রসেসিং লজিক ---
    user = await get_user_data(user_id)
    if not user or not user.get("thumbnail"):
        return await message.reply(small_caps("❌ please set a thumbnail first!"))

    sticker = await message.reply_sticker("CAACAgUAAxkBAAKGfGnNPmV4Bwsx_0W1Qk8h6p3Q423nAALbEAACdYaYVO2S9fNnW52THgQ")
    
    file_name = getattr(file_obj, 'file_name', 'video.mp4')
    clean_name = os.path.splitext(file_name)[0].replace("_", " ").replace(".", " ")
    caption_template = user.get("caption", "{filename}")
    final_caption = caption_template.replace("{filename}", clean_name)

    # ওয়াটারমার্ক চেক
    thumb_id = user["thumbnail"]
    temp_file = None
    if user.get("watermark"):
        try:
            temp_file = await apply_watermark(bot, thumb_id, user["watermark"])
            thumb_input = types.FSInputFile(temp_file)
        except Exception as e:
            print(f"Watermark Error: {e}")
            thumb_input = thumb_id
    else:
        thumb_input = thumb_id

    try:
        if message.video:
            await bot.send_video(
                chat_id=message.chat.id,
                video=file_obj.file_id,
                caption=final_caption,
                thumbnail=thumb_input,
                supports_streaming=True
            )
        else:
            await bot.send_document(
                chat_id=message.chat.id,
                document=file_obj.file_id,
                caption=final_caption,
                thumbnail=thumb_input
            )
        await increment_usage(user_id)
    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
    finally:
        await sticker.delete()
        if temp_file and os.path.exists(temp_file):
            os.remove(temp_file)

# --- বাটন কলব্যাক ---
@router.callback_query(F.data.startswith("use_this_"))
async def cb_use_thumb(query: types.CallbackQuery):
    thumb_id = query.data.replace("use_this_", "")
    await set_thumbnail(query.from_user.id, thumb_id)
    await query.answer("✅ Thumbnail Updated!", show_alert=True)
    await query.message.edit_caption(caption=small_caps("✅ this thumbnail is now saved as your default!"))

