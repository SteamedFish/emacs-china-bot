#!/usr/bin/env python3

from telethon import events

rssbot = bots["emacs-china"]


@rssbot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """Send a message when the command /start is issued."""
    logger.info("有人瞎撩 bot!")
    await event.respond("不许瞎撩 bot!")
    raise events.StopPropagation
