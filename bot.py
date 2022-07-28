from discord.ext import commands
from discord import Intents
import os
from core.custombot import KomodoBot
from dotenv import load_dotenv
import toml
load_dotenv()
intents=Intents.all()
bot = KomodoBot(command_prefix="2.0 ", help_command=commands.MinimalHelpCommand(), intents=intents)
print(toml.load('config.toml'))
bot.run(os.getenv('DISCORD_TOKEN'))
