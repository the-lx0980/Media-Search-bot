import asyncio
import re
import logging
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
logger = logging.getLogger(__name__)

# Setup database yourself. If you need setup database contact @Hansaka_Anuhas for paid edits
CURRENT = {}
CANCEL = {}
FORWARDING = {}

@Client.on_callback_query(filters.regex(r'^forward'))
async def forward(bot, query):
    _, ident, chat, lst_msg_id = query.data.split("#")
    if ident == 'yes':
        if FORWARDING.get(query.from_user.id):
            return await query.answer('Wait until previous process complete.', show_alert=True)

        msg = query.message
        await msg.edit('Starting Forwarding...')
        try:
            chat = int(chat)
        except:
            chat = chat
        await forward_files(int(lst_msg_id), chat, msg, bot, query.from_user.id)

    elif ident == 'close':
        await query.answer("Okay!")
        await query.message.delete()

    elif ident == 'cancel':
        await query.message.edit("Trying to cancel forwarding...")
        CANCEL[query.from_user.id] = True


@Client.on_message((filters.forwarded | (filters.regex("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")) & filters.text) & filters.private & filters.incoming)
async def send_for_forward(bot, message):
    if message.text:
        regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(message.text)
        if not match:
            return await message.reply('Invalid link for forward!')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric():
            chat_id  = int(("-100" + chat_id))
    elif message.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    else:
        return

    try:
        source_chat = await bot.get_chat(chat_id)
    except Exception as e:
        return await message.reply(f'Error - {e}')

    if source_chat.type != enums.ChatType.CHANNEL:
        return await message.reply("I can forward only channels.")

    skip = CURRENT.get(message.from_user.id)
    if skip:
        skip = skip
    else:
        skip = 0
    # last_msg_id is same to total messages
    buttons = [[
        InlineKeyboardButton('YES', callback_data=f'forward#yes#{chat_id}#{last_msg_id}')
    ],[
        InlineKeyboardButton('CLOSE', callback_data=f'forward#close#{chat_id}#{last_msg_id}')
    ]]
    await message.reply(f"Source Channel: {source_chat.title}\nTarget Channel: {target_chat.title}\nSkip messages: <code>{skip}</code>\nTotal Messages: <code>{last_msg_id}</code>\nFile Caption: {caption}\n\nDo you want to forward?", reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_message(filters.private & filters.command(['set_skip']))
async def set_skip_number(bot, message):
    try:
        _, skip = message.text.split(" ")
    except:
        return await message.reply("Give me a skip number.")
    try:
        skip = int(skip)
    except:
        return await message.reply("Only support in numbers.")
    CURRENT[message.from_user.id] = int(skip)
    await message.reply(f"Successfully set <code>{skip}</code> skip number.")

@Client.on_message(filters.private & filters.command(['set_caption']))
async def set_caption(bot, message):
    try:
        caption = message.text.split(" ", 1)[1]
    except:
        return await message.reply("Give me a caption.")
    CAPTION[message.from_user.id] = caption
    await message.reply(f"Successfully set file caption.\n\n{caption}")
    
    
    
async def forward_files(lst_msg_id, chat, msg, bot, user_id):
    current = CURRENT.get(user_id) if CURRENT.get(user_id) else 0
    indexed = 0
    deleted = 0
    unsupported = 0
    fetched = 0
    CANCEL[user_id] = False
    FORWARDING[user_id] = True
    # lst_msg_id is same to total messages

    try:
        async for message in bot.iter_messages(chat, lst_msg_id, CURRENT.get(user_id) if CURRENT.get(user_id) else 0):
            if CANCEL.get(user_id):
                await msg.edit(f"Successfully Forward Canceled!")
                break
            current += 1
            fetched += 1
            if current % 20 == 0:
                btn = [[
                    InlineKeyboardButton('CANCEL', callback_data=f'forward#cancel#{chat}#{lst_msg_id}')
                ]]
                await msg.edit_text(text=f"Index Processing...\n\nTotal Messages: <code>{lst_msg_id}</code>\nCompleted Messages: <code>{current} / {lst_msg_id}</code>\nIndexed Files: <code>{indexed}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nUnsupported Files Skipped: <code>{unsupported}</code>", reply_markup=InlineKeyboardMarkup(btn))
            if message.empty:
                deleted += 1
                continue
            elif not message.media:
                unsupported += 1
                continue
            elif message.media not in [enums.MessageMediaType.DOCUMENT, enums.MessageMediaType.VIDEO]:  # Non documents and videos files skipping
                unsupported += 1
                continue
            media = getattr(message, message.media.value, None)
            if not media:
                unsupported += 1
                continue
            elif media.mime_type not in ['video/mp4', 'video/x-matroska']:  # Non mp4 and mkv files types skipping
                unsupported += 1
                continue
            media.file_type = message.media.value
            media.caption = message.caption
            await save_file(media)
                
    except Exception as e:
        logger.exception(e)
        await msg.reply(f"Index Canceled!\n\nError - {e}")
    else:
        await msg.edit(f'Index Completed!\n\nTotal Messages: <code>{lst_msg_id}</code>\nCompleted Messages: <code>{current} / {lst_msg_id}</code>\nFetched Messages: <code>{fetched}</code>\nTotal Indexed Files: <code>{indexed}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nUnsupported Files Skipped: <code>{unsupported}</code>')
        ghh
        FORWARDING[user_id] = False


def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return "%.2f %s" % (size, units[i])
