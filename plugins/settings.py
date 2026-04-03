from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_data, set_caption, is_banned, db

router = Router()

def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

def get_settings_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🖼️ View Thumbnail", callback_data="view_thumb")],
        [InlineKeyboardButton(text="📝 Set Custom Caption", callback_data="set_cap_prompt")],
        [InlineKeyboardButton(text="📊 My History", callback_data="history_callback")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]
    ])

@router.message(Command("settings"))
@router.callback_query(F.data == "settings_menu")
async def settings_handler(event):
    message = event if isinstance(event, types.Message) else event.message
    user_id = event.from_user.id
    if await is_banned(user_id): return
    
    user = await get_user_data(user_id)
    thumb_status = "✅ Set" if user and user.get("thumbnail") else "❌ Not Set"
    wm_status = user.get("watermark") if user.get("watermark") else "❌ Disabled"
    cap_status = user.get("caption", "{filename}")

    text = (
        f"<b>⚙️ {small_caps('bot settings')}</b>\n\n"
        f"🖼️ <b>ᴛʜᴜᴍʙɴᴀɪʟ:</b> <code>{thumb_status}</code>\n"
        f"📝 <b>ᴄᴀᴘᴛɪᴏɴ:</b> <code>{cap_status}</code>\n"
        f"⚡ <b>ᴡᴀᴛᴇʀᴍᴀʀᴋ:</b> <code>{wm_status}</code>\n\n"
        f"{small_caps('choose an option to modify:')}"
    )

    if isinstance(event, types.Message):
        await message.reply(text, reply_markup=get_settings_buttons(), parse_mode="HTML")
    else:
        await event.message.edit_caption(caption=text, reply_markup=get_settings_buttons(), parse_mode="HTML")

@router.callback_query(F.data == "view_thumb")
async def view_thumb(query: types.CallbackQuery):
    user = await get_user_data(query.from_user.id)
    if user and user.get("thumbnail"):
        await query.message.answer_photo(photo=user["thumbnail"], caption=small_caps("your current thumbnail"))
    else:
        await query.answer(small_caps("no thumbnail set!"), show_alert=True)

@router.callback_query(F.data == "history_callback")
async def history_callback(query: types.CallbackQuery):
    user = await get_user_data(query.from_user.id)
    v_count = user.get("usage_count", 0)
    await query.answer(f"Total Videos Processed: {v_count}", show_alert=True)

@router.callback_query(F.data == "set_cap_prompt")
async def set_cap_prompt(query: types.CallbackQuery):
    await query.message.answer(small_caps("use /set_caption command to set your caption.\nExample: /set_caption movie: {filename}"))
    await query.answer()

@router.message(Command("set_caption"))
async def set_cap_cmd(message: types.Message):
    if len(message.text.split()) < 2:
        return await message.reply("❌ Usage: `/set_caption {filename} @PrimeXBots`")
    new_cap = message.text.split(None, 1)[1]
    await set_caption(message.from_user.id, new_cap)
    await message.reply(small_caps("✅ caption saved successfully!"))
