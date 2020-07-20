#!/usr/bin/env python3

"""telegram userbot."""

import configparser
import io
from collections import defaultdict
from datetime import datetime, timedelta

from telethon import TelegramClient, events

import aiocron
import jieba
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzlocal
from wordcloud import WordCloud

config = configparser.ConfigParser()
config.read("config.ini")
if "SteamedFish" in config:
    api_id = config["SteamedFish"]["api_id"]
    api_hash = config["SteamedFish"]["api_hash"]
    bot_token = config["emacs-china"]["token"]

userbot = TelegramClient("SteamedFish", api_id, api_hash).start()

stop_words = {
    "www",
    "com",
    "https",
    "http",
    "htm",
    "html",
    "的",
    "我",
    ",",
    "，",
    ".",
    "…",
    "?",
    "？",
    "(",
    ")",
    "（",
    "）",
    "...",
}


async def generate_word_cloud(
    channel="@emacs_zh",
    from_user: str = None,
    from_time: datetime = datetime.now(tzlocal()) - timedelta(days=1),
    end_time: datetime = datetime.now(tzlocal()),
):
    """生成词云."""
    words = defaultdict(int)

    async for msg in userbot.iter_messages(
        channel, from_user=from_user, offset_date=end_time
    ):
        if msg.date < from_time:
            break
        # if msg.via_bot:
        #     # ignore bots
        #     # 这个不太对，这个其实是 inline bot，不应该忽略
        #     continue
        if msg.from_id in [799930206, 801249359]:
            # ignore emacs-china-rss and keyboard bot
            continue
        if msg.text:
            for word in jieba.cut(msg.text):
                if word.lower() == "哇" or (
                    len(word) > 1 and word.lower() not in stop_words
                ):
                    words[word.lower()] += 1

    image = (
        WordCloud(
            font_path="/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
            width=800,
            height=400,
        )
        .generate_from_frequencies(words)
        .to_image()
    )
    stream = io.BytesIO()
    image.save(stream, "PNG")

    await userbot.send_message(
        channel, f"{channel} 频道从 {from_time} 到现在的消息词云", file=stream.getvalue()
    )


@aiocron.crontab("0 0 * * *")
async def generate_word_cloud_for_channels_daily(
    channels=["@emacs_zh", "@keyboard_cn"],
    from_time=datetime.now(tzlocal()) - timedelta(days=1),
) -> None:
    for channel in channels:
        await generate_word_cloud(channel, None, from_time)


@aiocron.crontab("0 0 * * 1")
async def generate_word_cloud_for_channels_weekly(
    channels=["@emacs_zh", "@keyboard_cn"],
    from_time=datetime.now(tzlocal()) - timedelta(weeks=1),
) -> None:
    for channel in channels:
        await generate_word_cloud(channel, None, from_time)


@aiocron.crontab("0 0 1 * *")
async def generate_word_cloud_for_channels_monthly(
    channels=["@emacs_zh", "@keyboard_cn"],
    from_time=datetime.now(tzlocal()) - relativedelta(months=1),
) -> None:
    for channel in channels:
        await generate_word_cloud(channel, None, from_time)


@aiocron.crontab("0 0 1 1 *")
async def generate_word_cloud_for_channels_yealy(
    channels=["@emacs_zh", "@keyboard_cn"],
    from_time=datetime.now(tzlocal()) - relativedelta(years=1),
) -> None:
    for channel in channels:
        await generate_word_cloud(channel, None, from_time)


@userbot.on(events.ChatAction(chats="@emacszh"))
async def remove_join_messages(event) -> None:
    """remove messages of join."""
    if event.user_joined:
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
