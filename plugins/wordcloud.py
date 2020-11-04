#!/usr/bin/env python3


import io
from collections import defaultdict
from datetime import datetime, timedelta

import aiocron
from async_lru import alru_cache
from dateutil.relativedelta import relativedelta
from dateutil.tz import tzlocal
from jieba import load_userdict, posseg
from telethon import events, hints, utils
from wordcloud import WordCloud


@alru_cache(None)
async def isbot(userid: hints.PeerID) -> bool:
    """用户是否是 bot"""
    # get_entity 操作比较多，存在大量重复，导致比较耗时，做个 cache
    user = await userbot.get_entity(userid)
    return user.bot


async def generate_word_cloud(
    channel: hints.EntityLike,
    from_user: hints.EntityLike,
    from_time: hints.DateLike,
    end_time: hints.DateLike,
    reply_to: hints.MessageIDLike = None,
) -> None:
    """从 channel 生成词云并发送."""

    with open("StopWords-simple.txt", mode="r", encoding="utf-8") as file:
        stop_words = set(
            map(str.strip,
                map(str.lower, file.read().splitlines())))

    load_userdict("userdict.txt")

    logger.info("开始生成词云…")

    stop_flags = set(
        [
            "d",  # 副词
            "f",  # 方位名词
            "x",  # 标点符号（文档说是 w 但是实际测试是 x
            "p",  # 介词
            "t",  # 时间
            "q",  # 量词
            "m",  # 数量词
            "nr",  # 人名，你我他
            "r",  # 代词
            "c",  # 连词
            "e",  # 文档没说，看着像语气词
            "xc",  # 其他虚词
            "zg",  # 文档没说，给出的词也没找到规律，但都不是想要的
            "y",  # 文档没说，看着像语气词
            # u 开头的都是助词，具体细分的分类文档没说
            "uj",
            "ug",
            "ul",
            "ud",
        ]
    )

    words = defaultdict(int)
    me = await userbot.get_me()

    if isinstance(channel, str):
        # 转换成 entity 才能有更多方法
        # 不然不能使用 utils.get_display_name(channel)
        channel = await userbot.get_entity(channel)

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
        if me.id == msg.from_id and (
            msg.text.endswith("的消息词云") or msg.text.startswith("发送 /wordcloud")
        ):
            # 忽略之前自己发送的词云消息
            continue
        fromuserisbot = await isbot(msg.from_id)
        if fromuserisbot:
            # ignore messages from bot
            continue
        words_cut = posseg.cut(msg.text, use_paddle=True)
        for word, flag in words_cut:
            word = word.lower().strip()
            if (word == "哇") or ((word not in stop_words) and (flag not in stop_flags)):
                words[word] += 1

    if words:
        image = (
            WordCloud(
                font_path="/usr/share/fonts/adobe-source-han-sans/SourceHanSansCN-Normal.otf",
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
        reply_to=reply_to,
    )


async def send_help(event) -> None:
    """send /wordcloud command help."""
    await event.reply(
        "发送 /wordcloud + 天数，查看自己的消息词云。\n"
        "回复 /wordcloud + 天数，查看别人的消息词云。\n"
        "发送 /wordcloud + 天数 + full，查看所有人的消息词云。\n"
        "\n"
        "天数必须是 float 类型，大于 0，小于等于 737644。\n"
        "数字较大时，生成可能需要较长时间，请耐心等待。\n"
        "\n"
        "例如： /wordcloud 7\n"
        "\n"
        "项目源码： "
        "https://github.com/SteamedFish/emacs-china-bot/blob/master/plugins/wordcloud.py"
    )


@userbot.on(events.NewMessage(pattern="/wordcloud"))
async def generate_word_cloud_from_event(event) -> None:
    """generate word cloud based on event."""
    msg = event.message
    if (not msg.text) or (not msg.text.lower().startswith("/wordcloud")):
        return
    to_chat = await event.get_chat()

    _, *rest = msg.text.lower().split(" ")

    if (not rest) or (len(rest) > 2):
        await send_help(event)
        return

    if len(rest) == 2:
        if rest[1] == "full":
            # 生成所有用户的词云
            user = None
        else:
            await send_help(event)
            return
    elif msg.is_reply:
        # 生成被回复用户的
        reply = await msg.get_reply_message()
        user = await reply.get_sender()
    else:
        # 生成发送者的
        user = await msg.get_sender()

    days = rest[0]
    try:
        days = float(days)
    except ValueError:
        await send_help(event)
        return

    if days <= 0 or days > 737644:
        await send_help(event)
        return

    await generate_word_cloud(
        to_chat,
        user,
        datetime.now(tzlocal()) - timedelta(days=days),
        datetime.now(tzlocal()),
        event.message,
    )
    logger.info("终于生成出来了")


@aiocron.crontab("0 0 * * 6")
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
