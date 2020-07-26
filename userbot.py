#!/usr/bin/env python3

"""telegram user bot."""

import importlib
import logging
import sys
from configparser import ConfigParser
from os import listdir, path

from telethon import TelegramClient


class tgbot:
    """telegram user bot class."""

    def __init__(self):
        """init the bot.

        Including userbot and all the real bots.
        """

        self.logger = logging.getLogger("userbot")
        config = ConfigParser()
        config.read(path.join(path.dirname(__file__), "config.ini"))

        bots = []
        for configsection in config:
            if (
                "api_id" in config[configsection]
                and "api_hash" in config[configsection]
            ):
                self.api_id = config[configsection]["api_id"]
                self.api_hash = config[configsection]["api_hash"]
                self.name = configsection
            elif "token" in config[configsection]:
                bot_token = config[configsection]["token"]
                bots.append((configsection, bot_token))
            elif configsection == "DEFAULT":
                continue
            else:
                self.logger.warning(f"Invalid configration in {configsection}")

        self.bots = {}
        try:
            client = TelegramClient(self.name, self.api_id, self.api_hash)
        except (NameError, AttributeError):
            raise ValueError("Invalid configration: need api_id and api_hash")
        self.logger.info(f"Starting userbot {self.name}")
        self.userbot = client.start()
        for botname, bot_token in bots:
            self.logger.info(f"Starting bot {botname}")
            self.bots[botname] = TelegramClient(
                botname, self.api_id, self.api_hash
            ).start(bot_token=bot_token)
        print(self.bots['emacs-china'])
        print(self.userbot)

    def load_plugins(self) -> None:
        """load all files from plugins dir."""
        pluginpath = path.join(path.dirname(__file__), "plugins")
        for pluginfile in listdir(pluginpath):
            if pluginfile.endswith(".py"):
                filename = path.join(path.dirname(__file__), "plugins", pluginfile)
                self.load_plugin_from_file(filename)

    def load_plugin_from_file(self, filepath: str) -> None:
        """load file as plugin."""

        filename, _ = path.splitext(path.basename(filepath))
        modulename = f"userbot_module_{filename}"
        spec = importlib.util.spec_from_file_location(modulename, filepath)
        module = importlib.util.module_from_spec(spec)

        # 给 plugin 传递这些对象
        module.userbot = self.userbot
        module.bots = self.bots
        module.logger = self.logger

        sys.modules[modulename] = module
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            self.logger.error(f"load plugin {filepath} error {e}")
        self.logger.info(f"loaded plugin {filepath} as module {modulename}")

    def run(self):
        """run the bot."""
        self.userbot.run_until_disconnected()



def main():
    bot = tgbot()
    bot.load_plugins()
    bot.run()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
