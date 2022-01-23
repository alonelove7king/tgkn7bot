from telethon import events,functions,errors
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from config import Config
import asyncio
import threading
import requests
import re
import time

def cronjob():
    threading.Timer(60*5, cronjob).start()
    requests.get(Config.DOMAIN)
    
cronjob()

client = TelegramClient(
            StringSession(),
            Config.API_ID,
            Config.API_HASH,
            # proxy=("socks5","127.0.0.1",9050)
            ).start(bot_token=Config.TOKEN)

w = dict()
v = dict()
username_bot = client.get_me().username

def get_file_name(message):
    if message.file.name:
        return message.file.name.replace(" ","-")
    ext = message.file.ext or ""
    return f"file{ext}"

@client.on(events.NewMessage)
async def download(event):
    if (pv := event.is_private) or event.is_group :
        if event.sender_id in w.keys():
            if w[event.sender_id] > time.time() - 1 :
                await event.reply(f"⛔️امکان ارسال همزمان چند فایل وجود ندارد⛔️")
                return
        w[event.sender_id] = time.time()
        if pv:
            try:
                await event.client(functions.channels.GetParticipantRequest(
                    channel = Config.CHANNEL_USERNAME_TW,
                    participant = event.sender_id
                    ))
            except errors.UserNotParticipantError:
                await event.reply(f"🌀برای استفاده از ربات ابتدا باید در کانال ما عضو بشی\n💠برای عضویت روی ایدی زیر کلیک کن سپس دستور /start رو ارسال کن\n\n🔸@{Config.CHANNEL_USERNAME_TW}")
                return
        if event.file :
            if not pv :
                if not event.file.size > 10_000_000:
                    return 
            sender = await event.get_sender()
            msg = await event.client.send_file(
                Config.CHANNEL,
                file=event.message.media,
                caption=f"◾️ID: @{sender.username}\n◽️UserID: [{event.sender_id}](tg://user?id={event.sender_id})\n♻️Converted By @{username_bot}")
            id_hex = hex(msg.id)[2:]
            id = f"{id_hex}/@{Config.CHANNEL_USERNAME_TW}-{get_file_name(msg)}"
            bot_url = f"t.me/{username_bot}?start={id_hex}"
            await event.reply(f"✅فایل شما با موفقیت به لینک تبدیل شد\n\n🌐 Link : {Config.DOMAIN}/{id}\n\n⚠️لینک های دانلود نیم بها میباشد، لذا قبل از دانلود فیلترشکن خود را خاموش کنید!\n\n‼️فایل های ارسالی بعد از 1 روز از روی سرور ها پاک مشوند‼️\n\n🆔 @{Config.CHANNEL_USERNAME_TW}",link_preview=False)
            return
        elif id_msg := re.search("/start (.*)", event.raw_text ):
            if id_hex := id_msg.group(1) :
                try:
                    id = int(id_hex,16)
                except ValueError:
                    return
                msg = await event.client.get_messages(Config.CHANNEL,ids=id)
                if not msg or not msg.file :
                    return await event.reply("404! File Not Found")
                if regex := re.search(r"(\d*)/(\d*)",msg.message):
                    if user_id := int(regex.group(1)) :
                        msg_id = int(regex.group(2))
                        file = await event.client.get_messages(user_id,ids=msg_id)
                        if not file or not file.file :
                            return await event.reply("404! File Not Found")
                        forward = await file.forward_to(event.chat_id)
                        id_name = f"{id_hex}/{get_file_name(msg)}"
                        bot_url = f"t.me/{username_bot}?start={id_hex}"
                        forward_reply = await forward.reply(f"will be deleted in 21 second. \n\n📎 : {Config.DOMAIN}/{id_name}\n\n🤖 : {bot_url}",link_preview=False)
                        await asyncio.sleep(12)
                        await forward_reply.edit(f"will be deleted in 10 second. \n\n📎 : {Config.DOMAIN}/{id_name}\n\n🤖 : {bot_url}")
                        await asyncio.sleep(10)
                        await forward.delete()
                        await forward_reply.edit(f"📎 : {Config.DOMAIN}/{id_name}\n\n🤖 : {bot_url}",link_preview=True)
                return
        if pv:
            await event.reply(f"🌀خوش آمدید\n🔰برای استفاده از ربات کافی است\nفایل خود را ارسال کرده و سپس لینک آن را دریافت کنید\n\n🆔 @{Config.CHANNEL_USERNAME_TW}")
    elif event.is_channel:
        if event.chat_id == Config.CHANNEL:
            if event.reply_to:
                msg = await event.get_reply_message()
                if regex := re.search(r"(\d*)/(\d*)",msg.message):
                    if user_id := int(regex.group(1)) :
                        msg_id = int(regex.group(2))
                        if await event.client.send_message(entity=user_id, message=event.message, reply_to=msg_id):
                            await event.client.edit_message("@King_Network7")
   
client.run_until_disconnected()
