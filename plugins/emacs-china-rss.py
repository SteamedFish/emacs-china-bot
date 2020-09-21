#!/usr/bin/env python3

import datetime

import aiocron
import httpx
from dateutil.parser import parse
from dateutil.tz import tzlocal
from telethon import events
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random,
)

rssbot = bots["emacs-china"]


async def fetch_url(url: str, timeout: int = 5, retry: int = 5):
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(5),
                reraise=True,
                retry=retry_if_exception_type(httpx.ConnectTimeout),
                wait=wait_random(min=timeout, max=timeout * 10),
            ):
                with attempt:
                    r = await client.get(url)
        except httpx.HTTPStatusError as e:
            return str(e)
    return r.json()


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

    async def category(self, id: int) -> str:
        """通过 topic ID，获取帖子的分区名称."""
        # TODO: 这个很少变化，应该做个 cache 避免频繁请求服务器
        try:
            categories = await fetch_url(url=self.categoriesurl, timeout=self.timeout)
        except ValueError as e:
            return str(e)

        for category in categories["category_list"]["categories"]:
            if category["id"] == id:
                return category["name"]

        return "NULL"

    async def author(self, id: int) -> str:
        """通过 post ID，获取作者信息."""
        try:
            author = await fetch_url(
                url=f"{self.url}/posts/{id}.json", timeout=self.timeout
            )
            author = r.json()
        except ValueError as e:
            return str(e)

        return f'{author["username"]}（{author["display_username"]}）'

    async def firstpost(self, id: int) -> int:
        """通过 topic ID，获取第一个 post 的信息."""
        try:
            post = await fetch_url(
                url=f"{self.url}/t/{id}/posts.json", timeout=self.timeout
            )
        except ValueError:
            return 0

        return int(post["post_stream"]["posts"][0]["id"])

    async def __aiter__(self):
        """返回新帖子."""

        try:
            content = await fetch_url(url=self.topicsurl, timeout=self.timeout)
            topics = content["topic_list"]["topics"]
        except ValueError as e:
            logger.info(str(e))
            raise StopIteration

        max_createtime = self.since
        ids = []
        for topic in topics:
            createtime = parse(topic["created_at"])
            print(topic)
            if createtime > self.since:
                if topic["id"] not in ids:
                    result = await self.parse_topic(topic)
                    yield result
                    ids.append(topic["id"])
                if createtime > max_createtime:
                    max_createtime = createtime
        if max_createtime > self.since:
            self.since = max_createtime

        return

    async def parse_topic(self, topic):
        """Parse topic."""
        firstpost = await self.firstpost(topic["id"])
        author = await self.author(firstpost)
        category = await self.category(topic["category_id"])
        result = (
            f"论坛新帖子："
            f'{self.url}/t/{topic["slug"]}/{topic["id"]}\n'
            f"作者：{author}\n"
            f"分区：{category}\n"
        )
        return result


emacschina = EmacsChina()


@aiocron.crontab("* * * * *")
async def get_post_from_emacs_china(channel: str = "@emacs_zh") -> None:
    async for post in emacschina:
        await rssbot.send_message(channel, post)
