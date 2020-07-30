#!/usr/bin/env python3

from telethon import events

reversebot = bots["reverse"]


@reversebot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """Send a message when the command /start is issued."""
    reply = await reverse_string("像火锅佬那样说话！")
    await event.respond(reply)
    raise events.StopPropagation


@reversebot.on(events.InlineQuery())
async def handler(event):
    """reverse what user has type."""
    if not event.text:
        return
    builder = event.builder
    text = await reverse_string(event.text)
    title = await reverse_string("像火锅佬那样说话！")

    await event.answer([builder.article(title, text=text)])


async def reverse_string(string: str) -> str:
    """reverse string."""
    trans = str.maketrans(
        {
            ",": "،",
            "，": "،",
            "?": "¿",
            "？": "¿",
            "(": ")",
            ")": "(",
            "（": "）",
            "）": "（",
            "《": "》",
            "》": "《",
            "«": "»",
            "»": "«",
            "/": "\\",
            "\\": "/",
            "“": "”",
            "”": "“",
            ">": "<",
            "<": ">",
            "〔": "〕",
            "〕": "〔",
            "[": "]",
            "]": "[",
            "{": "}",
            "}": "{",
            "「": "」",
            "」": "「",
            "【": "】",
            "】": "【",
            "［": "］",
            "］": "［",
        }
    )

    return string[::-1].translate(trans)
