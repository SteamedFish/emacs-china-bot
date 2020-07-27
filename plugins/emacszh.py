#!/usr/bin/env python3

import aiocron
from telethon import events, utils, errors


@userbot.on(events.ChatAction(chats="@emacszh"))
async def remove_join_messages(event) -> None:
    """remove messages of join."""
    if event.user_joined:
        await event.delete()
        logger.info(f"删了 {channel} 的入群消息")


@aiocron.crontab("* 2 * * *")
async def remove_deleted_account(channel: str = "@emacszh") -> None:
    """remove all deleted account from channel everyday."""
    async for user in userbot.iter_participants(channel):
        if user.deleted:
            try:
                await userbot.kick_participant(channel, user)
            except errors.rpcerrorlist.UserAdminInvalidError:
                # 群主踢不掉
                pass
            else:
                logger.info(f"踢了 {channel} 的 {utils.get_display_name(user)}")
