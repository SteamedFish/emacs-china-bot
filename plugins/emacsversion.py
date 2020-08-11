#!/usr/bin/env python3

import re
import socket

import aiocron
import requests
from packaging import version

rssbot = bots["emacs-china"]


class EmacsVersion:
    """check emacs new version."""

    def __init__(self, timeout: int = 10) -> None:
        self.checkurl = "http://ftp.gnu.org/gnu/emacs/"
        self.timeout = timeout
        socket.setdefaulttimeout(self.timeout)
        self.version = self.get_current_version()

    def get_current_version(self) -> version.Version:
        webpage = requests.get(self.checkurl).text

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

    def check_new_version(self) -> bool:
        current_version = self.get_current_version()
        if current_version > self.version:
            self.version = current_version
            return True
        return False


emacsversion = EmacsVersion()


@aiocron.crontab("13 * * * *")
async def check_new_emacs_version(channel: str = "@emacs_zh") -> None:
    if emacsversion.check_new_version():
        versioninfo = emacsversion.version
        await rssbot.send_message(channel, f"普天同庆！！！发现 Emacs 新版本：{versioninfo.public}")
