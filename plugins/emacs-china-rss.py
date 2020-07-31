#!/usr/bin/env python3

import datetime
import socket

import aiocron
import requests
from dateutil.parser import parse
from dateutil.tz import tzlocal
from telethon import events

rssbot = bots["emacs-china"]


@rssbot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """Send a message when the command /start is issued."""
    logger.info("有人瞎撩 bot!")
    await event.respond("不许瞎撩 bot!")
    raise events.StopPropagation


class EmacsChina:
    """emacs-china.org 论坛."""

    def __init__(self, since=datetime.datetime.now(tzlocal()), timeout=5) -> None:
        """论坛内容.

        since 为从何时开始的帖子被视为新帖子，需要带时区信息.
        timeout 超时时间，单位为秒.
        """
        self.since = since
        self.timeout = timeout
        self.url = "https://emacs-china.org"
        self.topicsurl = f"{self.url}/latest.json"
        self.categoriesurl = f"{self.url}/categories.json"

        socket.setdefaulttimeout(self.timeout)

    def category(self, id: int) -> str:
        """通过 topic ID，获取帖子的分区名称."""
        # TODO: 这个很少变化，应该做个 cache 避免频繁请求服务器
        socket.setdefaulttimeout(self.timeout)
        r = requests.get(self.categoriesurl)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            return str(e)
        try:
            categories = r.json()
        except ValueError as e:
            return str(e)

        for category in categories["category_list"]["categories"]:
            if category["id"] == id:
                return category["name"]

        return "NULL"

    def author(self, id: int) -> str:
        """通过 post ID，获取作者信息."""
        socket.setdefaulttimeout(self.timeout)
        r = requests.get(f"{self.url}/posts/{id}.json")
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            return str(e)
        try:
            author = r.json()
        except ValueError as e:
            return str(e)

        return f'{author["username"]}（{author["display_username"]}）'

    def firstpost(self, id: int) -> int:
        """通过 topic ID，获取第一个 post 的信息."""
        socket.setdefaulttimeout(self.timeout)
        r = requests.get(f"{self.url}/t/{id}/posts.json")
        try:
            r.raise_for_status()
        except requests.HTTPError:
            return 0
        try:
            post = r.json()
        except ValueError:
            return 0

        return int(post["post_stream"]["posts"][0]["id"])

    def __iter__(self):
        """返回新帖子."""

        socket.setdefaulttimeout(self.timeout)
        r = requests.get(self.topicsurl)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            logger.info(str(e))
            raise StopIteration
        try:
            topics = r.json()["topic_list"]["topics"]
        except ValueError as e:
            logger.info(str(e))
            raise StopIteration

        max_createtime = self.since
        ids = []
        for topic in topics:
            createtime = parse(topic["created_at"])
            if createtime > self.since:
                if topic["id"] not in ids:
                    yield self.parse_topic(topic)
                    ids.append(topic["id"])
                if createtime > max_createtime:
                    max_createtime = createtime
        if max_createtime > self.since:
            self.since = max_createtime

        return self

    def parse_topic(self, topic):
        """Parse topic."""
        result = (
            f"论坛新帖子："
            f'{self.url}/t/{topic["slug"]}/{topic["id"]}\n'
            f'作者：{self.author(self.firstpost(topic["id"]))}\n'
            f'分区：{self.category(topic["category_id"])}\n'
        )
        return result


emacschina = EmacsChina()


@aiocron.crontab("* * * * *")
async def get_post_from_emacs_china(channel: str = "@steamedfish") -> None:
    for post in emacschina:
        await rssbot.send_message(channel, post)
