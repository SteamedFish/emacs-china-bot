#!/usr/bin/env python3

import re

import aiocron
import httpx
from packaging import version
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_random,
)

rssbot = bots["emacs-china"]


class EmacsVersion:
    """check emacs new version."""

    def __init__(self, timeout: int = 10) -> None:
        self.checkurl = "http://ftp.gnu.org/gnu/emacs/"
        self.timeout = timeout
        self.version = None

    async def get_current_version(self) -> version.Version:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(5),
                    reraise=True,
                    retry=retry_if_exception_type(httpx.ConnectTimeout),
                    wait=wait_random(min=self.timeout, max=self.timeout * 10),
                ):
                    with attempt:
                        r = await client.get(self.checkurl)
            except (httpx.HTTPStatusError, httpx.ReadTimeout):
                return None
        webpage = r.text

        # FIXME: this is a hardcode
        tarball_regex = re.compile(r"\bemacs-[0-9.]+\.tar\.[a-z]*\b")
        version_regex = re.compile(r"\b[0-9.]+\b")

        currentversion = None

        for tarball in tarball_regex.findall(webpage):
            versionstring = version_regex.findall(tarball)[0]
            if versionstring.endswith("."):
                versionstring = versionstring[:-1]
            emacsversion = version.parse(versionstring)
            if currentversion is None or currentversion < emacsversion:
                currentversion = emacsversion
        return emacsversion

    async def check_new_version(self) -> bool:
        current_version = await self.get_current_version()
        if self.version is None:
            self.version = current_version
        elif current_version > self.version:
            self.version = current_version
            return True
        return False


emacsversion = EmacsVersion()


@aiocron.crontab("13 * * * *")
async def check_new_emacs_version(channel: str = "@emacs_zh") -> None:
    if await emacsversion.check_new_version():
        versioninfo = emacsversion.version
        await rssbot.send_message(channel, f"普天同庆！！！发现 Emacs 新版本：{versioninfo.public}")
