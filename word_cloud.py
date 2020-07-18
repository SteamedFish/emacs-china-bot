#!/usr/bin/env python3

import configparser
import io
from collections import defaultdict

import jieba
from telethon import TelegramClient, events
from wordcloud import WordCloud

config = configparser.ConfigParser()
config.read("config.ini")
if "SteamedFish" in config:
    api_id = config["SteamedFish"]["api_id"]
    api_hash = config["SteamedFish"]["api_hash"]
    bot_token = config["emacs-china"]["token"]

# bot = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)
bot = TelegramClient("me", api_id, api_hash).start()

stop_words = {
    "www",
    "com",
    "https",
    "http",
    "htm",
    "html",
    "还是",
    "就是",
    "这是",
    "以前",
    "不过",
    "不行",
    "这个",
    "那个",
    "什么",
    "感觉",
    "现在",
    "可以",
    "不是",
    "知道",
    "好像",
    "但是",
    "还有",
    "怎么",
    "然后",
    "你们",
    "我们",
    "时候",
    "没有",
    "自己",
    "一个",
    "这么",
    "觉得",
    "而且",
    "这种",
    "已经",
    "不到",
    "开始",
    "很多",
    "这样",
    "可能",
    "有点",
    "之前",
    "以后",
    "最近",
    "所以",
    "应该",
    "里面",
    "不会",
    "出来",
    "真的",
    "只有",
    "地方",
    "真的",
    "看到",
    "不了",
    "那么",
    "不用",
    "主要",
    "反正",
    "其实",
    "的话",
    "起来",
    "肯定",
    "如果",
    "只是",
    "问题",
    "事情",
    "估计",
    "直接",
    "因为",
    "不能",
    "需要",
    "一样",
    "确实",
    "不然",
    "估计",
    "发现",
    "大家",
    "今天",
    "或者",
    "这边",
    "为了",
    "本来",
    "东西",
    "是不是",
    "不要",
    "基本",
    "一般",
    "多少",
    "以下",
    "一下",
    "有些",
    "有人",
    "他们",
    "这次",
    "其他",
    "只能",
    "这些",
    "看看",
    "那种",
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


def main():
    """Start the bot."""
    words = defaultdict(int)

    for msg in bot.iter_messages("@emacs_zh"):
        if msg.from_id in [799930206, 801249359]:
            # ignore emacs-china-rss and keyboard bot
            continue
        if msg.text:
            # print(msg.text)
            for word in jieba.cut(msg.text):
                if (word.lower() == "哇" or
                        (len(word) > 1 and word.lower() not in stop_words)):
                    words[word.lower()] += 1

    for msg in bot.iter_messages("@emacszh"):
        if msg.from_id in [799930206, 801249359]:
            # ignore emacs-china-rss and keyboard bot
            continue
        if msg.text:
            # print(msg.text)
            for word in jieba.cut(msg.text):
                if (word.lower() == "哇" or
                        (len(word) > 1 and word.lower() not in stop_words)):
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

    # with open("test.png", mode="wb") as file:
    #     file.write(stream.getvalue())

    # bot.loop.run_until_complete(bot.send_message(676179719, "test"))
    bot.loop.run_until_complete(
        bot.send_message("@emacs_zh",
                         "TEST: emacs_zh 新旧两个群所有历史消息词云",
                         file=stream.getvalue())
    )
    # bot.send_message(676179719, msg.text)
    # bot.run_until_disconnected()


if __name__ == "__main__":
    main()
