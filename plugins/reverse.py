#!/usr/bin/env python3

from telethon import events
import grapheme

reversebot = bots["reverse"]


@reversebot.on(events.NewMessage(pattern="/start"))
async def start(event):
    """Send a message when the command /start is issued."""
    reply = reverse_string("像火锅佬那样说话！")
    await event.respond(reply)
    raise events.StopPropagation


@reversebot.on(events.InlineQuery())
async def handler(event):
    """reverse what user has type."""
    if not event.text:
        return
    builder = event.builder
    text = reverse_string(event.text)
    title = reverse_string("像火锅佬那样说话！")

    await event.answer([builder.article(title, text=text)])


def reverse_string(string: str) -> str:
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

    return "".join(reversed(list(grapheme.graphemes(string)))).translate(trans)
