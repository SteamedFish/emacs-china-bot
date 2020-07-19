#!/usr/bin/env python3

"""telegram userbot."""

import configparser

from telethon import TelegramClient, events

import aiocron

config = configparser.ConfigParser()
config.read("config.ini")
if "SteamedFish" in config:
    api_id = config["SteamedFish"]["api_id"]
    api_hash = config["SteamedFish"]["api_hash"]
    bot_token = config["emacs-china"]["token"]

userbot = TelegramClient("SteamedFish", api_id, api_hash).start()


@userbot.on(events.ChatAction(chats="@emacszh"))
async def remove_join_messages(event) -> None:
    """remove messages of join."""
    if event.user_joined:
        print("deleting joining message")
        await event.delete()


@aiocron.crontab("10 * * * *")
async def remove_deleted_account(channel: str = "@emacszh") -> None:
    """remove all deleted account from channel everyday."""
    async for user in userbot.iter_participants(channel):
        if user.id == 349983830:
            # 这是群主，删不掉
            continue
        if user.deleted:
            await userbot.kick_participant(channel, user)


def main():
    userbot.run_until_disconnected()


if __name__ == "__main__":
    main()
