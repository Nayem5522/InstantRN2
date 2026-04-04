from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_data, set_caption, is_banned, toggle_setting, remove_thumbnail

router = Router()

def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

def get_settings_buttons(user_data):
    cap_on = "✅ ON" if user_data.get("caption_on", True) else "❌ OFF"
    wm_on = "✅ ON" if user_data.get("watermark_on", False) else "❌ OFF"
    
    keyboard = [
        [InlineKeyboardButton(text=f"📝 Caption: {cap_on}", callback_data="toggle_caption")],
        [InlineKeyboardButton(text=f"⚡ Watermark: {wm_on}", callback_data="toggle_watermark")],
        [InlineKeyboardButton(text="🖼️ View Thumbnail", callback_data="view_thumb")]
    ]
    
    # যদি থাম্বনেইল সেট করা থাকে তবেই ডিলিট বাটন দেখাবে
    if user_data.get("thumbnail"):
        keyboard.append([InlineKeyboardButton(text="🗑️ Delete Thumbnail", callback_data="delete_thumb")])
        
    keyboard.append([InlineKeyboardButton(text="📊 My Stats", callback_data="history_callback")])
    keyboard.append([InlineKeyboardButton(text="🔙 Back", callback_data="back_home")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@router.message(Command("settings"))
@router.callback_query(F.data == "settings_menu")
async def settings_handler(event):
    user_id = event.from_user.id
    if await is_banned(user_id): return
    
    user = await get_user_data(user_id)
    thumb_status = "✅ Set" if user.get("thumbnail") else "❌ Not Set"
    wm_text = user.get("watermark") if user.get("watermark") else "Not Set"

    text = (
        f"<b>⚙️ {small_caps('bot settings')}</b>\n\n"
        f"🖼️ <b>ᴛʜᴜᴍʙɴᴀɪʟ:</b> <code>{thumb_status}</code>\n"
        f"📝 <b>ᴄᴀᴘᴛɪᴏɴ:</b> <code>{user.get('caption', '{filename}')}</code>\n"
        f"📡 <b>ᴡᴍ ᴛᴇxᴛ:</b> <code>{wm_text}</code>\n\n"
        f"{small_caps('use buttons below to toggle options:')}"
    )

    if isinstance(event, types.Message):
        await event.reply(text, reply_markup=get_settings_buttons(user), parse_mode="HTML")
    else:
        await event.message.edit_caption(caption=text, reply_markup=get_settings_buttons(user), parse_mode="HTML")

@router.callback_query(F.data == "toggle_caption")
async def toggle_cap_cb(query: types.CallbackQuery):
    await toggle_setting(query.from_user.id, "caption_on")
    user = await get_user_data(query.from_user.id)
    await query.message.edit_reply_markup(reply_markup=get_settings_buttons(user))
    await query.answer("Caption Toggled!")

@router.callback_query(F.data == "toggle_watermark")
async def toggle_wm_cb(query: types.CallbackQuery):
    user = await get_user_data(query.from_user.id)
    if not user.get("watermark"):
        return await query.answer("❌ Set watermark text first using /watermark", show_alert=True)
    await toggle_setting(query.from_user.id, "watermark_on")
    user = await get_user_data(query.from_user.id)
    await query.message.edit_reply_markup(reply_markup=get_settings_buttons(user))
    await query.answer("Watermark Toggled!")

@router.callback_query(F.data == "delete_thumb")
async def delete_thumb_cb(query: types.CallbackQuery):
    await remove_thumbnail(query.from_user.id)
    user = await get_user_data(query.from_user.id)
    await query.message.edit_reply_markup(reply_markup=get_settings_buttons(user))
    await query.answer("✅ Thumbnail Deleted Successfully!", show_alert=True)

@router.callback_query(F.data == "view_thumb")
async def view_thumb(query: types.CallbackQuery):
    user = await get_user_data(query.from_user.id)
    
    if user and user.get("thumbnail"):
        # ছবির নিচে ডিলিট বাটন তৈরি
        btn = [[InlineKeyboardButton(text="🗑️ Delete Thumbnail", callback_data="delete_thumb_direct")]]
        markup = InlineKeyboardMarkup(inline_keyboard=btn)
        
        await query.message.answer_photo(
            photo=user["thumbnail"], 
            caption=small_caps("your current thumbnail"),
            reply_markup=markup
        )
    else:
        await query.answer("No thumbnail set!", show_alert=True)

# ছবির নিচের ডিলিট বাটনের কাজ
@router.callback_query(F.data == "delete_thumb_direct")
async def delete_thumb_direct(query: types.CallbackQuery):
    await remove_thumbnail(query.from_user.id)
    
    # ছবিটি ডিলিট করে দেওয়া
    await query.message.delete()
    
    await query.answer("✅ Thumbnail Deleted Successfully!", show_alert=True)

@router.callback_query(F.data == "history_callback")
async def history_callback(query: types.CallbackQuery):
    user = await get_user_data(query.from_user.id)
    await query.answer(f"Total Processed: {user.get('usage_count', 0)}", show_alert=True)
    
