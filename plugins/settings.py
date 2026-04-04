from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_data, is_banned, toggle_setting, remove_thumbnail

router = Router()

def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

def get_settings_markup(user):
    cap = "✅ ON" if user.get("caption_on", True) else "❌ OFF"
    wm = "✅ ON" if user.get("watermark_on", False) else "❌ OFF"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📝 Caption: {cap}", callback_data="tg_cap")],
        [InlineKeyboardButton(text=f"⚡ Watermark: {wm}", callback_data="tg_wm")],
        [InlineKeyboardButton(text="🖼️ View Thumbnail", callback_data="view_thumb")],
        [InlineKeyboardButton(text="🔙 Back", callback_data="back_home")]
    ])

@router.message(Command("settings"))
@router.callback_query(F.data == "settings_menu")
async def settings_handler(event):
    user = await get_user_data(event.from_user.id)
    text = f"<b>⚙️ {small_caps('bot settings')}</b>\n\n🖼️ ᴛʜᴜᴍʙ: {'✅' if user.get('thumbnail') else '❌'}\n📝 ᴄᴀᴘ: <code>{user.get('caption')}</code>"
    if isinstance(event, types.Message):
        await event.reply(text, reply_markup=get_settings_markup(user), parse_mode="HTML")
    else:
        await event.message.edit_caption(caption=text, reply_markup=get_settings_markup(user), parse_mode="HTML")

@router.callback_query(F.data == "tg_cap")
async def tg_cap(q: types.CallbackQuery):
    await toggle_setting(q.from_user.id, "caption_on")
    user = await get_user_data(q.from_user.id)
    await q.message.edit_reply_markup(reply_markup=get_settings_markup(user))

@router.callback_query(F.data == "tg_wm")
async def tg_wm(q: types.CallbackQuery):
    user = await get_user_data(q.from_user.id)
    if not user.get("watermark"): return await q.answer("Set watermark text first!", show_alert=True)
    await toggle_setting(q.from_user.id, "watermark_on")
    user = await get_user_data(q.from_user.id)
    await q.message.edit_reply_markup(reply_markup=get_settings_markup(user))

@router.callback_query(F.data == "view_thumb")
async def view_thumb(q: types.CallbackQuery):
    user = await get_user_data(q.from_user.id)
    if user.get("thumbnail"):
        btn = [[InlineKeyboardButton(text="🗑️ Delete Thumbnail", callback_data="del_thumb_now")]]
        await q.message.answer_photo(photo=user["thumbnail"], caption=small_caps("current thumbnail"), reply_markup=InlineKeyboardMarkup(inline_keyboard=btn))
    else: await q.answer("No thumbnail set!", show_alert=True)

@router.callback_query(F.data == "del_thumb_now")
async def del_thumb_now(q: types.CallbackQuery):
    await remove_thumbnail(q.from_user.id)
    await q.message.delete()
    await q.answer("Deleted ✅", show_alert=True)
