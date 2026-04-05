from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from database import add_user, is_banned

router = Router()

async def is_subscribed(bot: Bot, user_id: int, channels: list):
    btn = []
    for ch in channels:
        try:
            chat = await bot.get_chat(int(ch))
            member = await bot.get_chat_member(int(ch), user_id)

            if member.status in ["left", "kicked"]:
                btn.append([
                    InlineKeyboardButton(
                        text=f"✇ Join {chat.title} ✇",
                        url=chat.invite_link
                    )
                ])
        except:
            btn.append([
                InlineKeyboardButton(
                    text="✇ Join Channel ✇",
                    url="https://t.me/PrimeXBots"
                )
            ])
    return btn

def small_caps(text):
    mapping = {"a": "ᴀ", "b": "ʙ", "c": "ᴄ", "d": "ᴅ", "e": "ᴇ", "f": "ꜰ", "g": "ɢ", "h": "ʜ", "i": "ɪ", "j": "ᴊ", "k": "ᴋ", "l": "ʟ", "m": "ᴍ", "n": "ɴ", "o": "ᴏ", "p": "ᴘ", "q": "ǫ", "r": "ʀ", "s": "s", "t": "ᴛ", "u": "ᴜ", "v": "ᴠ", "w": "ᴡ", "x": "x", "y": "ʏ", "z": "ᴢ"}
    return "".join(mapping.get(c.lower(), c) for c in text)

def get_start_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ sᴇᴛᴛɪɴɢs", callback_data="settings_menu")],
        [
            InlineKeyboardButton(text="〄 ᴍᴏᴠɪᴇ ᴄʜᴀɴɴᴇʟ 〄", url=MOVIE_CHANNEL),
            InlineKeyboardButton(text="✪ ꜱᴜᴘᴘᴏʀᴛ ɢʀᴏᴜᴘ ✪", url=SUPPORT_GROUP)
        ],
        [InlineKeyboardButton(text="〄 ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ 〄", url=CHANNEL_URL)],
        [
            InlineKeyboardButton(text="〆 ʜᴇʟᴘ 〆", callback_data="help_cmd"),
            InlineKeyboardButton(text="〆 ᴀʙᴏᴜᴛ 〆", callback_data="about_cmd")
        ],
        [InlineKeyboardButton(text="✧ ᴄʀᴇᴀᴛᴏʀ ✧", url=CREATOR_URL)]
    ])


# =========================
# ✅ START MESSAGE FUNCTION
# =========================
async def send_start(message: types.Message):
    user_mention = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>"

    welcome = f"""
<b>🔥 ᴡᴇʟᴄᴏᴍᴇ {user_mention} ᴛᴏ ᴘʀɪᴍᴇ ᴄᴏᴠᴇʀ ᴄʜᴀɴɢᴇʀ ʙᴏᴛ 🔥</b>

━━━━━━━━━━━━━━━━━━━
✨ <b>ᴀɴᴅ ᴀᴅᴠᴀɴᴄᴇᴅ ꜰᴇᴀᴛᴜʀᴇs</b> ✨

🎬 <b>ᴜʟᴛʀᴀ ᴘʀᴏ ᴠɪᴅᴇᴏ ᴄᴜꜱᴛᴏᴍɪᴢᴀᴛɪᴏɴ ꜱʏꜱᴛᴇᴍ</b>

🚀 🎞️ ꜱᴍᴀʀᴛ ᴛʜᴜᴍʙɴᴀɪʟ ᴇɴɢɪɴᴇ  
⚡ 🖼️ ɪɴꜱᴛᴀɴᴛ ᴄᴏᴠᴇʀ ᴄʜᴀɴɢᴇ ꜱʏꜱᴛᴇᴍ  
💎 ✍️ ᴀᴅᴠᴀɴᴄᴇᴅ ᴄᴀᴘᴛɪᴏɴ ꜱᴛʏʟɪɴɢ ᴛᴏᴏʟꜱ  
🔥 🎨 ᴘʀᴇᴍɪᴜᴍ ᴡᴀᴛᴇʀᴍᴀʀᴋ ᴅᴇꜱɪɢɴᴇʀ  
🧠 📥 ᴀᴜᴛᴏ ᴛʜᴜᴍʙɴᴀɪʟ ᴇxᴛʀᴀᴄᴛᴏʀ  
🎯 🛠️ ᴏɴᴇ-ᴄʟɪᴄᴋ ᴍᴇᴅɪᴀ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ  

━━━━━━━━━━━━━━━━━━━
⚙️ <b>ʜᴏᴡ ᴛᴏ ᴜꜱᴇ?</b>

1️⃣ ꜱᴇɴᴅ ᴀ ᴘʜᴏᴛᴏ → ꜱᴇᴛ ᴛʜᴜᴍʙɴᴀɪʟ  
2️⃣ ꜱᴇɴᴅ ᴀ ᴠɪᴅᴇᴏ → ᴀᴜᴛᴏ ꜱᴍᴀʀᴛ ᴄᴏᴠᴇʀ ᴀᴘᴘʟʏ  
3️⃣ /set_caption → ᴛᴏ ᴜꜱᴇ ʏᴏᴜʀ ᴏᴡɴ ᴄᴜꜱᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ. ᴛɪᴘꜱ😉: ᴜꜱᴇ <code>{filename}</code> ᴛᴏ ꜱᴇᴛ ᴏʀɪɢɪɴᴀʟ ꜰɪʟᴇ ɴᴀᴍᴇ.
4️⃣ /extract → ɢᴇᴛ ᴛʜᴜᴍʙɴᴀɪʟ ꜰʀᴏᴍ ᴀɴʏ ᴠɪᴅᴇᴏ    
5️⃣ ꜱᴇᴛᴛɪɴɢꜱ → ꜰᴜʟʟ ᴄᴏɴᴛʀᴏʟ ᴀᴄᴄᴇꜱꜱ  
6️⃣
━━━━━━━━━━━━━━━━━━━
💎 <b>ᴘʀᴇᴍɪᴜᴍ ᴇxᴘᴇʀɪᴇɴᴄᴇ</b>

✔️ ᴜʟᴛʀᴀ ꜰᴀꜱᴛ ᴘʀᴏᴄᴇꜱꜱɪɴɢ  
✔️ ᴄʟᴇᴀɴ & ᴍᴏᴅᴇʀɴ ᴜɪ  
✔️ 24/7 ꜱᴛᴀʙʟᴇ ꜱʏꜱᴛᴇᴍ  
✔️ ɴᴏ ʟᴀɢ • ɴᴏ ᴅᴇʟᴀʏ  

━━━━━━━━━━━━━━━━━━━
🚀 <b>ᴘᴏᴡᴇʀ ᴄᴏɴᴛʀᴏʟ ᴘᴀɴᴇʟ</b>  
👉 ᴛᴀᴘ ⚙️ ꜱᴇᴛᴛɪɴɢꜱ ᴛᴏ ᴜɴʟᴏᴄᴋ ᴀʟʟ ꜰᴇᴀᴛᴜʀᴇꜱ
"""

    await message.reply_photo(
        photo=START_PIC,
        caption=welcome,
        parse_mode="HTML"
    )


# =========================
# ✅ START COMMAND
# =========================
@router.message(Command("start"))
async def start_cmd(message: types.Message, bot: Bot):
    if await is_banned(message.from_user.id):
        return

    await add_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name
    )

    # 🔥 FORCE SUB CHECK
    if AUTH_CHANNEL:
        btn = await is_subscribed(bot, message.from_user.id, AUTH_CHANNEL)

        if btn:
            btn.append([
                InlineKeyboardButton("♻️ Refresh ♻️", callback_data="check_sub")
            ])

            await message.reply_photo(
                photo="https://i.postimg.cc/xdkd1h4m/IMG-20250715-153124-952.jpg",
                caption=(
                    f"<b>👋 Hello {message.from_user.mention},\n\n"
                    "To use this bot, you must join our updates channel first.\n\n"
                    "1️⃣ Click on Join button\n"
                    "2️⃣ Join the channel\n"
                    "3️⃣ Then click Refresh\n\n"
                    "⚠️ Otherwise you cannot use the bot!</b>"
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=btn),
                parse_mode="HTML"
            )
            return

    # ✅ যদি already join করা থাকে
    await send_start(message)


# =========================
# ✅ CALLBACK HANDLER
# =========================
@router.callback_query(F.data == "check_sub")
async def check_sub_callback(query: types.CallbackQuery, bot: Bot):

    btn = await is_subscribed(bot, query.from_user.id, AUTH_CHANNEL)

    if btn:
        # ❌ join করে নাই
        await query.answer(
            "⚠️ You haven't joined all channels yet!",
            show_alert=True
        )
    else:
        # ✅ join হয়ে গেছে
        await query.answer(
            "✅ Thank you for joining!",
            show_alert=True
        )

        await query.message.delete()

        # 🔥 AUTO CONTINUE
        fake_message = query.message
        fake_message.from_user = query.from_user

        await send_start(fake_message)
        
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

@router.callback_query(F.data == "help_cmd")
async def help_handler(query: types.CallbackQuery):
    help_text = (
        f"<b>📖 {small_caps('how to use this bot')}</b>\n\n"
        f"1. <b>sᴇɴᴅ ᴀ ᴘʜᴏᴛᴏ:</b> sᴇɴᴅ ᴀɴʏ ɪᴍᴀɢᴇ ᴛᴏ sᴇᴛ ɪᴛ ᴀs ʏᴏᴜʀ ᴄᴜsᴛᴏᴍ ᴛʜᴜᴍʙɴᴀɪʟ.\n"
        f"2. <b>sᴇɴᴅ ᴠɪᴅᴇᴏ/ᴅᴏᴄ:</b> ғᴏʀᴡᴀʀᴅ ᴏʀ ᴜᴘʟᴏᴀᴅ ᴀɴʏ ᴠɪᴅᴇᴏ ᴛᴏ ᴛʜᴇ ʙᴏᴛ.\n"
        f"3. <b>ɪɴsᴛᴀɴᴛ ʀᴇsᴜʟᴛ:</b> ᴛʜᴇ ʙᴏᴛ ᴡɪʟʟ ᴘʀᴏᴄᴇss ᴀɴᴅ ʀᴇᴘʟʏ ᴡɪᴛʜ ʏᴏᴜʀ ᴄᴜsᴛᴏᴍ ᴛʜᴜᴍʙɴᴀɪʟ.\n\n"
        f"📝 <b>sᴇᴛ ᴄᴀᴘᴛɪᴏɴ:</b> ᴜsᴇ <code>/set_caption [text]</code> ᴛᴏ ᴀᴅᴅ ᴀ ᴄᴜsᴛᴏᴍ ᴄᴀᴘᴛɪᴏɴ.\n"
        f"💡 <i>ᴛɪᴘ: ᴜsᴇ</i> <code>{{filename}}</code> <i>ɪɴ ᴄᴀᴘᴛɪᴏɴ ᴛᴏ ᴋᴇᴇᴘ ᴛʜᴇ ᴏʀɪɢɪɴᴀʟ ɴᴀᴍᴇ.</i>\n\n"
        f"⚙️ ᴜsᴇ ᴛʜᴇ sᴇᴛᴛɪɴɢs ʙᴜᴛᴛᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ᴅᴀᴛᴀ."
    )
    
    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ sᴇᴛᴛɪɴɢs", callback_data="settings_menu")],
        [InlineKeyboardButton(text="🔙 ʙᴀᴄᴋ", callback_data="back_home")]
    ])
    
    await query.message.edit_caption(
        caption=help_text, 
        reply_markup=buttons, 
        parse_mode="HTML"
    )
