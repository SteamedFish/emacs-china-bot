#!/usr/bin/env python3

import configparser
import datetime
import time
import socket
import requests
from dateutil.parser import parse
from dateutil.tz import tzlocal


class emacschina:
    """emacs-china.org 论坛."""

    def __init__(self,
                 since=datetime.datetime.now(tzlocal()),
                 period=10,
                 timeout=5) -> None:
        """论坛内容.

        since 为从何时开始的帖子被视为新帖子，需要带时区信息.
        period 检查新帖子的频率，单位为秒.
        timeout 超时时间，单位为秒.
        """
        self.since = since
        self.period = period
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
        r = requests.get(f'{self.url}/posts/{id}.json')
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
        r = requests.get(f'{self.url}/t/{id}/posts.json')
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
        """返回新帖子。永不退出，无限循环."""
        while True:
            time.sleep(self.period)

            socket.setdefaulttimeout(self.timeout)
            r = requests.get(self.topicsurl)
            try:
                r.raise_for_status()
            except requests.HTTPError as e:
                print(str(e))
                continue
            try:
                topics = r.json()["topic_list"]["topics"]
            except ValueError as e:
                print(str(e))
                continue

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
        result = (f'论坛新帖子：'
                  f'{self.url}/t/{topic["slug"]}/{topic["id"]}\n'
                  f'作者：{self.author(self.firstpost(topic["id"]))}\n'
                  f'分区：{self.category(topic["category_id"])}\n'
                  )
        return result


def post_message(message):
    """Send message to telegram and discord."""
    api = 'https://api.telegram.org/bot'
    userid = '@emacs_zh'

    config = configparser.ConfigParser()
    config.read('config.ini')
    if 'emacs-china' in config:
        token = config['emacs-china']['token']

    postdata = {
        "chat_id": userid,
        "text": message,
    }
    requests.post(api + token + "/sendMessage", data=postdata)

    # 这个是给 matterbridge 同步到 discord 用的
    postdata = {
        "text": message,
        "username": "emacs-china-rss",
        "gateway": "emacschinarss",
    }
    requests.post("http://localhost:4242/api/message", data=postdata)


for post in emacschina():
    post_message(post)
