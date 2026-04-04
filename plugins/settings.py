from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_user_data, toggle_setting, remove_thumbnail, is_banned

router = Router()

def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

def get_buttons(user):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📝 Caption: {'ON' if user.get('caption_on') else 'OFF'}", callback_data="toggle_caption")],
        [InlineKeyboardButton(text=f"⚡ Watermark: {'ON' if user.get('watermark_on') else 'OFF'}", callback_data="toggle_wm")],
        [InlineKeyboardButton(text="🖼️ View Thumbnail", callback_data="view_thumb")],
        [InlineKeyboardButton(text="📊 My Stats", callback_data="history")],  # 🔥 ADDED BACK
        [InlineKeyboardButton(text="🔙 Back", callback_data="back")]
    ])

@router.message(Command("settings"))
async def settings(msg: types.Message):
    if await is_banned(msg.from_user.id): return
    user = await get_user_data(msg.from_user.id)
    await msg.reply("⚙️ Settings", reply_markup=get_buttons(user))

@router.callback_query(F.data == "view_thumb")
async def view_thumb(q: types.CallbackQuery):
    user = await get_user_data(q.from_user.id)

    if not user or not user.get("thumbnail"):
        return await q.answer("❌ No thumbnail!", show_alert=True)

    btn = [[InlineKeyboardButton(text="🗑️ Delete", callback_data="del_thumb")]]

    await q.message.answer_photo(
        photo=user["thumbnail"],
        caption="🖼️ Your Thumbnail",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=btn)
    )

@router.callback_query(F.data == "history")
async def history(q: types.CallbackQuery):
    user = await get_user_data(q.from_user.id)
    total = user.get("usage_count", 0)

    await q.answer(f"📊 Total Processed: {total}", show_alert=True)

@router.callback_query(F.data == "del_thumb")
async def delete_thumb(q: types.CallbackQuery):
    await remove_thumbnail(q.from_user.id)
    await q.message.delete()
    await q.answer("✅ Deleted!", show_alert=True)
