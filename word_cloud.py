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


def stopwordslist(filepath):
    stopwords = [
        line.strip()
        for line in open(filepath, 'r', encoding='utf-8').readlines()
    ]
    return stopwords

stop_words = stopwordslist('StopWords.txt')


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
