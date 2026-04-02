from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from database import add_user, is_banned

router = Router()

def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

def get_start_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✪ ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ ✪", url=SUPPORT_GROUP),
            InlineKeyboardButton(text="〄 ᴍᴏᴠɪᴇ ᴄʜᴀɴɴᴇʟ 〄", url=MOVIE_CHANNEL)
        ],
        [InlineKeyboardButton(text="〄 ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ 〄", url=CHANNEL_URL)],
        [
            InlineKeyboardButton(text="〆 ʜᴇʟᴘ 〆", callback_data="help_cmd"),
            InlineKeyboardButton(text="〆 ᴀʙᴏᴜᴛ 〆", callback_data="about_cmd")
        ],
        [
            InlineKeyboardButton(text="⚙️ sᴇᴛᴛɪɴɢs", callback_data="settings_menu"),
            InlineKeyboardButton(text="✧ ᴄʀᴇᴀᴛᴏʀ ✧", url=CREATOR_URL)
        ]
    ])

@router.message(Command("start"))
async def start_cmd(message: types.Message):
    if await is_banned(message.from_user.id): return
    await add_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    welcome = small_caps(f"welcome {message.from_user.first_name}!\ninstantly update thumbnails and captions using me.")
    await message.reply_photo(photo=START_PIC, caption=welcome, reply_markup=get_start_buttons())

@router.callback_query(F.data == "about_cmd")
async def about_handler(query: types.CallbackQuery, bot: Bot):
    me = await bot.get_me()
    about_text = (
        f"<b><blockquote>⍟───[  <a href='{CHANNEL_URL}'>ᴍʏ ᴅᴇᴛᴀɪʟꜱ ʙʏ ᴘʀɪᴍᴇXʙᴏᴛꜱ</a> ]───⍟</blockquote></b>\n\n"
        f"‣ ᴍʏ ɴᴀᴍᴇ : <a href='https://t.me/{me.username}'>{me.first_name}</a>\n"
        "‣ ʙᴇꜱᴛ ꜰʀɪᴇɴᴅ : <a href='tg://settings'>ᴛʜɪꜱ ᴘᴇʀꜱᴏɴ</a>\n"
        f"‣ ᴅᴇᴠᴇʟᴏᴘᴇʀ : <a href='{CREATOR_URL}'>ᴍʀ.ᴘʀɪᴍᴇ</a>\n"
        f"‣ ᴜᴘᴅᴀᴛᴇꜱ ᴄʜᴀɴɴᴇʟ : <a href='{CHANNEL_URL}'>ᴘʀɪᴍᴇXʙᴏᴛꜱ</a>\n"
        f"‣ ᴍᴀɪɴ ᴄʜᴀɴɴᴇʟ : <a href='{MOVIE_CHANNEL}'>ᴘʀɪᴍᴇ ᴄɪɴᴇᴢᴏɴᴇ</a>\n"
        f"‣ ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ : <a href='{SUPPORT_GROUP}'>ᴘʀɪᴍᴇX ꜱᴜᴘᴘᴏʀᴛ</a>\n"
        "‣ ᴅᴀᴛᴀʙᴀꜱᴇ : <a href='https://www.mongodb.com/'>ᴍᴏɴɢᴏᴅʙ</a>\n"
        "‣ ʙᴏᴛ ꜱᴇʀᴠᴇʀ : <a href='https://heroku.com'>ʜᴇʀᴏᴋᴜ</a>\n"
        "‣ ʙᴜɪʟᴅ ꜱᴛᴀᴛᴜꜱ : v2.7.1 [ꜱᴛᴀʙʟᴇ]\n"
    )
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧑‍💻 ꜱᴏᴜʀᴄᴇ ᴄoᴅᴇ 🧑‍💻", callback_data="source_prime")],
        [InlineKeyboardButton(text="🔙 ʙᴀᴄᴋ", callback_data="back_home")]
    ])
    await query.message.edit_caption(caption=about_text, reply_markup=buttons, parse_mode="HTML")

@router.callback_query(F.data == "source_prime")
async def source_handler(query: types.CallbackQuery):
    caption = (
        f"👋 Hello Dear 👋,\n\n"
        "⚠️ ᴛʜɪꜱ ʙᴏᴛ ɪꜱ ᴀ ᴘʀɪᴠᴀᴛᴇ ꜱᴏᴜʀᴄᴇ ᴘʀᴏᴊᴇᴄᴛ\n\n"
        "ᴛʜɪs ʙᴏᴛ ʜᴀs ʟᴀsᴛᴇsᴛ ᴀɴᴅ ᴀᴅᴠᴀɴᴄᴇᴅ ꜰᴇᴀᴛᴜʀᴇs⚡️\n"
        "▸ ɪꜰ ʏᴏᴜ ᴡᴀɴᴛ ꜱᴏᴜʀᴄᴇ ᴄoᴅᴇ oʀ ʟɪᴋᴇ ᴛʜɪꜱ ʙᴏᴛ ᴄᴏɴᴛᴀᴄᴛ ᴍᴇ..!\n"
        "▸ ɪ ᴡɪʟʟ ᴄʀᴇᴀᴛᴇ ᴀ ʙᴏᴛ ꜰᴏʀ ʏᴏᴜ oʀ ꜱᴏᴜʀᴄᴇ ᴄoᴅᴇ\n"
        "⇒ ᴄᴏɴᴛᴀᴄᴛ ᴍᴇ - ♚ ᴀᴅᴍɪɴ ♚."
    )
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="♚ ᴀᴅᴍɪɴ ♚", url=ADMIN_URL)],
        [InlineKeyboardButton(text="• ᴄʟᴏsᴇ •", callback_data="closes")]
    ])
    await query.message.delete()
    await query.message.answer_photo(photo=SOURCE_PIC, caption=caption, reply_markup=buttons)

@router.callback_query(F.data == "back_home")
async def back_home(query: types.CallbackQuery):
    await query.message.edit_caption(caption=small_caps("welcome back!"), reply_markup=get_start_buttons())

@router.callback_query(F.data == "closes")
async def closes(query: types.CallbackQuery):
    await query.message.delete()
