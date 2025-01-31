# Don't Remove Credit @VJ_Botz
# Subscribe YouTube Channel For Amazing Bot @Tech_VJ
# Ask Doubt on Telegram @KingVJ01

import logging
from pyrogram import Client, emoji, filters
from pyrogram.errors.exceptions.bad_request_400 import QueryIdInvalid
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultCachedDocument, InlineQuery
from database.ia_filterdb import get_search_results
from utils import is_subscribed, get_size, temp
from info import CACHE_TIME, AUTH_USERS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION
from database.connections_mdb import active_connection

logger = logging.getLogger(__name__)
cache_time = 0 if AUTH_USERS or AUTH_CHANNEL else CACHE_TIME

async def inline_users(query: InlineQuery):
    if AUTH_USERS:
        if query.from_user and query.from_user.id in AUTH_USERS:
            return True
        else:
            return False
    if query.from_user and query.from_user.id not in temp.BANNED_USERS:
        return True
    return False

def get_reply_markup(query):
    """Creates an inline keyboard with a Search Again button"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔍 Search Again", switch_inline_query_current_chat=query)]
    ])

@Client.on_inline_query()
async def answer(bot, query):
    """Show search results for given inline query"""
    chat_id = await active_connection(str(query.from_user.id))
    
    if not await inline_users(query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="Access Denied",
            switch_pm_parameter="access_denied"
        )
        return

    if AUTH_CHANNEL and not await is_subscribed(bot, query):
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="You have to subscribe to use this bot",
            switch_pm_parameter="subscribe"
        )
        return

    # Prevent empty searches (Ensures user types something)
    if not query.query.strip():
        await query.answer(
            results=[],
            cache_time=0,
            switch_pm_text="Type something to search 🤦🏻",
            switch_pm_parameter="start"
        )
        return

    # Extract search string and file type
    if '|' in query.query:
        string, file_type = query.query.split('|', maxsplit=1)
        string = string.strip()
        file_type = file_type.strip().lower()
    else:
        string = query.query.strip()
        file_type = None

    offset = int(query.offset or 0)

    # Get search results
    files, next_offset, total = await get_search_results(chat_id, string, file_type=file_type, max_results=10, offset=offset)

    if not files:
        await query.answer(
            results=[],
            is_personal=True,
            cache_time=cache_time,
            switch_pm_text=f"{emoji.CROSS_MARK} No results for '{string}'",
            switch_pm_parameter="okay"
        )
        return

    results = []

    # Add total files found message
    results.append(
        InlineQueryResultCachedDocument(
            title=f"✅ {total} files found for '{string}'",
            document_file_id=files[0]['file_id'],  # Dummy file to show summary
            caption=f"📂 {total} results found.\n\nSelect a file below 👇",
            description="Search results summary",
            reply_markup=get_reply_markup(string)  # "Search Again" button
        )
    )

    # Add actual file results
    for file in files:
        title = file['file_name']
        size = get_size(file['file_size'])
        f_caption = file.get('caption', title)  # Default caption

        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(
                    file_name=title or '',
                    file_size=size or '',
                    file_caption=f_caption or ''
                )
            except Exception as e:
                logger.exception(e)

        results.append(
            InlineQueryResultCachedDocument(
                title=title,
                document_file_id=file['file_id'],
                caption=f_caption,
                description=f"Size: {size}",
                reply_markup=get_reply_markup(string)  # "Search Again" button below each file
            )
        )

    # Send results
    try:
        await query.answer(
            results=results,
            is_personal=True,
            cache_time=cache_time,
            switch_pm_text=f"{emoji.FILE_FOLDER} {total} files found",
            switch_pm_parameter="start",
            next_offset=str(next_offset)
        )
    except QueryIdInvalid:
        pass
    except Exception as e:
        logger.exception(str(e))

