import discord
from discord.ext import commands
import asyncio
import time
import datetime

from discord.ext.commands.cooldowns import BucketType


class Counter(discord.ui.Button):
    def __init__(self, author, now, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.author = author
        self.now = datetime.datetime.utcnow()
        self.has_clicked = False

    async def callback(self, interaction: discord.Interaction):
        if interaction.user != self.author:
            return
        end = datetime.datetime.utcnow() - self.now

        await interaction.response.edit_message(
            content=f'It took you: {end.total_seconds():.2f} seconds!'
        )
        self.disabled = True
        await interaction.message.edit(view=self.view)

    async def update_now(self, now: datetime.datetime):
        self.now = now


class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 3, BucketType.default)
    async def clickspeed(self, ctx):
        thing = await ctx.send('Press the button as fast as you can!')
        await asyncio.sleep(2.0)
        button = Counter(
            ctx.author,
            datetime.datetime.utcnow(),
            style=discord.ButtonStyle.green,
            label='Test',
        )
        view = discord.ui.View()
        view.add_item(button)
        await asyncio.sleep(0.4)
        await thing.edit(
            content='Press the button as fast as you can!', view=view
        )
        await button.update_now(datetime.datetime.utcnow())

    @commands.command()
    @commands.is_owner()
    async def reload(self, ctx, file: str):
        try:
            self.bot.reload_extension(f'cogs.{file}')
        except Exception as e:
            return await ctx.send(str(e))
        else:
            await ctx.message.add_reaction('<:greenTick:596576670815879169>')


async def setup(bot):
    await bot.add_cog(Test(bot))
