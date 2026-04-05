from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_data, set_caption, is_banned, toggle_setting, remove_thumbnail

router = Router()

def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

# ✅ BUTTON UI
def get_settings_buttons(user):
    cap_on = "✅ ON" if user.get("caption_on", True) else "❌ OFF"
    wm_on = "✅ ON" if user.get("watermark_on", False) else "❌ OFF"

    keyboard = [
        [InlineKeyboardButton(text=f"📝 Caption: {cap_on}", callback_data="toggle_caption")],
        [InlineKeyboardButton(text=f"⚡ Watermark: {wm_on}", callback_data="toggle_watermark")],
        [InlineKeyboardButton(text="🖼️ View Thumbnail", callback_data="view_thumb")],
        [InlineKeyboardButton(text="📊 My Stats", callback_data="history")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# ✅ SETTINGS MAIN
@router.message(Command("settings"))
@router.callback_query(F.data == "settings_menu")
async def settings_handler(event):
    user_id = event.from_user.id
    if await is_banned(user_id): return

    user = await get_user_data(user_id)

    thumb_status = "✅ Set" if user.get("thumbnail") else "❌ Not Set"
    wm_text = user.get("watermark") if user.get("watermark") else "Not Set"
    caption_text = user.get("caption", "{filename}")

    text = (
        f"<b>⚙️ Settings</b>\n\n"
        f"🖼️ Thumbnail: <code>{thumb_status}</code>\n"
        f"📝 Caption: <code>{caption_text}</code>\n"
        f"⚡ Watermark: <code>{wm_text}</code>"
    )

    # 🔥 FIX START HERE
    if isinstance(event, types.Message):
        await event.reply(text, reply_markup=get_settings_buttons(user), parse_mode="HTML")
    else:
        try:
            await event.message.edit_text(text, reply_markup=get_settings_buttons(user), parse_mode="HTML")
        except:
            await event.message.answer(text, reply_markup=get_settings_buttons(user), parse_mode="HTML")
# ✅ TOGGLE CAPTION
@router.callback_query(F.data == "toggle_caption")
async def toggle_caption_cb(query: types.CallbackQuery):
    await toggle_setting(query.from_user.id, "caption_on")
    user = await get_user_data(query.from_user.id)
    await query.message.edit_reply_markup(reply_markup=get_settings_buttons(user))
    await query.answer("Caption toggled!")

# ✅ TOGGLE WATERMARK
@router.callback_query(F.data == "toggle_watermark")
async def toggle_wm_cb(query: types.CallbackQuery):
    user = await get_user_data(query.from_user.id)

    if not user.get("watermark"):
        return await query.answer("❌ Set watermark first using /watermark", show_alert=True)

    await toggle_setting(query.from_user.id, "watermark_on")
    user = await get_user_data(query.from_user.id)

    await query.message.edit_reply_markup(reply_markup=get_settings_buttons(user))
    await query.answer("Watermark toggled!")

# ✅ VIEW THUMBNAIL
@router.callback_query(F.data == "view_thumb")
async def view_thumb(query: types.CallbackQuery):
    user = await get_user_data(query.from_user.id)

    if user and user.get("thumbnail"):
        btn = [[InlineKeyboardButton(text="🗑️ Delete Thumbnail", callback_data="delete_thumb_direct")]]

        await query.message.answer_photo(
            photo=user["thumbnail"],
            caption=small_caps("your current thumbnail"),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=btn)
        )
    else:
        await query.answer("❌ No thumbnail set!", show_alert=True)

# ✅ DELETE FROM IMAGE
@router.callback_query(F.data == "delete_thumb_direct")
async def delete_thumb_direct(query: types.CallbackQuery):
    await remove_thumbnail(query.from_user.id)
    await query.message.delete()
    await query.answer("✅ Thumbnail deleted!", show_alert=True)

# ✅ HISTORY
@router.callback_query(F.data == "history")
async def history_cb(query: types.CallbackQuery):
    user = await get_user_data(query.from_user.id)
    total = user.get("usage_count", 0)
    await query.answer(f"📊 Total Processed: {total}", show_alert=True)
    
