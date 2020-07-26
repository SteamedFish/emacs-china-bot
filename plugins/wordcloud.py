#!/usr/bin/env python3


import io
from collections import defaultdict
from datetime import datetime, timedelta

from telethon import events, hints, utils

import aiocron
import jieba
from async_lru import alru_cache
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzlocal
from wordcloud import WordCloud

with open("StopWords-simple.txt", mode="r", encoding="utf-8") as file:
    stop_words = set(map(str.strip, map(str.lower, file.read().splitlines())))


@alru_cache(None)
async def isbot(userid: int) -> bool:
    # get_entity 操作比较耗时，独立出来做个 cache
    user = await userbot.get_entity(userid)
    return user.bot


async def generate_word_cloud(
    channel: hints.EntityLike,
    from_user: hints.EntityLike,
    from_time: datetime,
    end_time: datetime,
) -> None:
    """从 channel 生成词云并发送."""

    logger.info("开始生成词云…")

    words = defaultdict(int)
    me = await userbot.get_me()

    async for msg in userbot.iter_messages(
        channel, from_user=from_user, offset_date=end_time
    ):
        if msg.date < from_time:
            break
        if not msg.text:
            continue
        if msg.text.startswith("/wordcloud"):
            # 忽略命令消息
            continue
        if me.id == msg.from_id and msg.text.endswith("的消息词云"):
            # 忽略之前自己发送的词云消息
            continue
        fromuserisbot = await isbot(msg.from_id)
        if fromuserisbot:
            # ignore messages from bot
            continue
        for word in jieba.cut(msg.text):
            if word.lower() not in stop_words:
                words[word.lower()] += 1

    if words:
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
        channel,
        f"{utils.get_display_name(channel)} 频道 "
        f"{'' if from_user is None else utils.get_display_name(from_user)}"
        f" 从 {from_time.isoformat(sep=' ',timespec='seconds')} 到 "
        f"{end_time.isoformat(sep=' ',timespec='seconds')} 的消息词云",
        file=(stream.getvalue() if words else None),
    )


@userbot.on(events.NewMessage(pattern="/wordcloud"))
async def generate_word_cloud_from_event(event) -> None:
    """generate word cloud based on event."""
    defaultdays = "30"
    msg = event.message
    if (not msg.text) or (not msg.text.lower().startswith("/wordcloud")):
        return
    to_chat = await event.get_chat()

    _, *rest = msg.text.lower().split(" ")

    if len(rest) > 1 and rest[1] == "full":
        # 生成所有用户的词云
        user = None
    elif msg.is_reply:
        # 生成被回复用户的
        reply = await msg.get_reply_message()
        user = await reply.get_sender()
    else:
        # 生成发送者的
        user = await msg.get_sender()

    if not rest:
        days = defaultdays
    else:
        days = rest[0]

    try:
        days = int(days)
    except ValueError:
        days = int(defaultdays)

    await generate_word_cloud(
        to_chat,
        user,
        datetime.now(tzlocal()) - timedelta(days=days),
        datetime.now(tzlocal()),
    )
    logger.info("终于生成出来了")


@aiocron.crontab("0 0 * * 1")
async def generate_word_cloud_for_channels_weekly() -> None:
    channels = ["@emacs_zh", "@keyboard_cn"]
    from_time = datetime.now(tzlocal()) - timedelta(weeks=1)
    end_time = datetime.now(tzlocal())
    for channel in channels:
        await generate_word_cloud(channel, None, from_time, end_time)


@aiocron.crontab("0 0 1 * *")
async def generate_word_cloud_for_channels_monthly() -> None:
    channels = ["@emacs_zh", "@keyboard_cn"]
    from_time = datetime.now(tzlocal()) - relativedelta(months=1)
    end_time = datetime.now(tzlocal())
    for channel in channels:
        await generate_word_cloud(channel, None, from_time, end_time)


@aiocron.crontab("0 0 1 1 *")
async def generate_word_cloud_for_channels_yealy() -> None:
    channels = ["@emacs_zh", "@keyboard_cn"]
    from_time = datetime.now(tzlocal()) - relativedelta(years=1)
    end_time = datetime.now(tzlocal())
    for channel in channels:
        await generate_word_cloud(channel, None, from_time, end_time)
