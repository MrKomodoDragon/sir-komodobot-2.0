from .context import KomodoContext
from discord.ext import commands
import aiohttp
import asyncio
import asyncpg
import toml

class KomodoBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.afk = {}
        self.loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession()
        self.exts = ['utility', 'test', 'rtfm']
        self.config = toml.load('config.toml')

    async def get_context(self, message, *, cls=None):
        return await super().get_context(message, cls=cls or KomodoContext)

    async def start(self, token, *, reconnect=True):
        for i in self.exts:
            await self.load_extension(f'cogs.{i}')
        await self.load_extension('jishaku')
        import os

        os.environ['JISHAKU_NO_UNDERSCORE'] = 'True'
        os.environ['JISHAKU_NO_DM_TRACEBACK'] = 'True'
        os.environ['JISHAKU_HIDE'] = 'True'
        await self.reload_extension('jishaku')

        return await super().start(token, reconnect=reconnect)

    async def close(self):
        for i in self.exts:
            await self.unload_extension(f'cogs.{i}')
        await self.session.close()
        return await super().close()

    async def on_message_edit(self, before, after):
        await self.process_commands(after)
