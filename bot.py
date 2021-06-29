from discord.ext import commands
import os
from core.custombot import KomodoBot
from dotenv import load_dotenv
import toml
load_dotenv()
bot = KomodoBot(command_prefix="2.0 ", help_command=commands.MinimalHelpCommand())
print(toml.load('config.toml'))
#bot.run(os.getenv('DISCORD_TOKEN'))
#self._BotBase__cogs = commands.core._CaseInsensitiveDict()