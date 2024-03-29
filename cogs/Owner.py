import datetime
import inspect
import io
import logging
import textwrap
import traceback
import os
import json
import typing
import discord
import import_expression
import tabulate
from discord.ext import commands, menus
from dotenv import load_dotenv

from jishaku.paginators import PaginatorInterface, WrappedPaginator

load_dotenv()


class CmdSource(menus.ListPageSource):
    async def format_page(self, menu, commands):
        return menu.ctx.embed(
            title=f'{commands[0].cog.qualified_name} commands',
            description='\n'.join(
                f'`{menu.ctx.clean_prefix}{i.name} {i.signature}` -'
                f'{i.description or i.help or "help not found"}'
                for i in commands
            ),
        )


class TestPages(menus.MenuPages):
    @menus.button('\N{BLACK SQUARE FOR STOP}\ufe0f', position=menus.Last(2))
    async def end_menu(self, _):
        await self.message.delete()
        self.stop()


class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    class Test(menus.Menu):
        async def send_initial_message(self, ctx, channel):
            embed = ctx.embed(
                title='Sir KomodoBot Help',
                description='```[args] mean the arguments is optional\n'
                '<args> means the argument is required```',
            )
            embed.add_field(
                name='Categories',
                value='🎉: Fun\n⚙️: Utility\n🎵: Music\n💵: Economy\n📷: Images',
            )
            return await ctx.send(embed=embed)

        @menus.button('🎉')
        async def Fun(self, payload):
            source = CmdSource(
                self.bot.get_cog('Fun').get_commands(), per_page=10
            )
            p1 = TestPages(source)
            await p1.start(self.ctx)
            await self.message.delete()

        @menus.button('⚙️')
        async def Utility(self, payload):
            source = CmdSource(
                self.bot.get_cog('Utility').get_commands(), per_page=10
            )
            p1 = TestPages(source)
            await p1.start(self.ctx)
            await self.message.delete()

        @menus.button('🎵')
        async def Music(self, payload):
            source = CmdSource(
                self.bot.get_cog('Music').get_commands(), per_page=10
            )
            p1 = TestPages(source)
            await p1.start(self.ctx)
            await self.message.delete()

        @menus.button('💵')
        async def Economy(self, payload):
            source = CmdSource(
                self.bot.get_cog('Economy').get_commands(), per_page=10
            )
            p1 = TestPages(source)
            await p1.start(self.ctx)
            await self.message.delete()

        @menus.button('📷')
        async def Images(self, payload):
            source = CmdSource(
                self.bot.get_cog('Images').get_commands(), per_page=10
            )
            p1 = TestPages(source)
            await p1.start(self.ctx)
            await self.message.delete()

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command()
    @commands.is_owner()
    async def blacklist(
        self,
        ctx,
        member: typing.Union[discord.Member, discord.User],
        *,
        reason='Spamming the bot',
    ):
        self.bot.blacklists[member.id] = reason
        await self.bot.pg.execute(
            'INSERT INTO blacklist VALUES ($1, $2)', member.id, reason
        )
        await ctx.send(
            embed=ctx.embed(
                title='Succesfully blacklisted user '
                f'`{str(member)}` for reason: `{str(reason)}`'
            )
        )

    @commands.command()
    async def test(self, ctx):
        test = self.Test()
        await test.start(ctx)

    @commands.command()
    async def fun(self, ctx):
        source = self.FunSource(self.bot.get_cog('Fun').get_commands())
        p1 = menus.MenuPages(source)
        await p1.start(ctx)

    @commands.command()
    async def clean(self, ctx, Number=None):
        def check(m):
            return m.author == self.bot.user

        if Number is None:
            return (
                await ctx.message.reference.resolved.delete()
                if ctx.message.reference
                else await ctx.send('No Message to delete')
            )
        await ctx.channel.purge(check=check)

    @commands.group()
    async def dev(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.send_help(str(ctx.command))

    @dev.command()
    async def sql(self, ctx, *, query: str):
        thing = await self.bot.pg.fetch(query)
        if len(thing) == 0:
            return await ctx.message.add_reaction(
                '<:greenTick:596576670815879169>'
            )
        thing = tabulate.tabulate(thing, headers='keys', tablefmt='psql')
        if len(thing) > 2000:
            return await ctx.send(
                file=discord.File(
                    fp=io.BytesIO(thing.encode('utf-8')), filename='table.txt'
                )
            )
        await ctx.send(
            embed=ctx.embed(
                title='SQL OUTPUT', description=f'```py\n{thing}```'
            )
        )

    @dev.command()
    async def eval(self, ctx, *, code: str):
        env = {
            'ctx': ctx,
            'author': ctx.author,
            'message': ctx.message,
            'guild': ctx.guild,
            'bot': self.bot,
            'reference': ctx.message.reference,
            'resolved': ctx.message.reference.resolved
            if ctx.message.reference
            else None,
        }
        env.update(globals())
        imports = 'import asyncio\n'
        'import discord\nfrom discord.ext import commands\nimport aiohttp\n'
        body = 'async def func():\n' + textwrap.indent(imports + code, '    ')
        try:
            import_expression.exec(body, env, locals())
        except Exception as e:
            etype = type(e)
            trace = e.__traceback__
            lines = traceback.format_exception(etype, e, trace)
            paginator = WrappedPaginator(
                max_size=500, prefix='A weird error occured```py', suffix='```'
            )
            paginator.add_line(''.join(lines))
            interface = PaginatorInterface(
                ctx.bot, paginator, owner=ctx.author
            )
            return await interface.send_to(ctx)
        try:
            maybe_coro = locals()['func']()
            if inspect.isasyncgen(maybe_coro):
                async for i in maybe_coro:
                    await ctx.send(i)
                return
            thing = await maybe_coro
            if thing:
                if isinstance(thing, discord.Embed):
                    return await ctx.send(embed=thing)
                if isinstance(thing, discord.File):
                    return await ctx.send(file=thing)
                else:
                    await ctx.send(thing)
        except Exception as e:
            await ctx.send(e)

    @dev.command()
    async def reload(self, ctx, file: str):
        if file == '*':
            errors = []
            extensions = [
                'Fun',
                'Utility',
                'Images',
                'jishaku',
                'Music',
                'Economy',
                'Help',
                'Owner',
                'Prefix',
            ]
            for cog in extensions:
                try:
                    self.bot.reload_extension(f'Cogs.{cog}')
                except Exception as e:
                    errors.append(str(e))
            if errors:
                await ctx.send('\n'.join(errors))
            else:
                await ctx.message.add_reaction(
                    '<:greenTick:596576670815879169>'
                )
        else:
            try:
                self.bot.reload_extension(f'Cogs.{file.lower().capitalize()}')
            except Exception as e:
                await ctx.send(e)
            else:
                await ctx.message.add_reaction(
                    '<:greenTick:596576670815879169>'
                )

    @dev.command()
    async def load(self, ctx, file: str):
        if file == '*':
            errors = []
            extensions = [
                'Fun',
                'Utility',
                'Images',
                'jishaku',
                'Music',
                'Economy',
                'Help',
                'Owner',
                'Prefix',
            ]
            for cog in extensions:
                try:
                    self.bot.load_extension(f'Cogs.{cog}')
                except Exception as e:
                    errors.append(str(e))
            if errors:
                await ctx.send('\n'.join(errors))
            else:
                await ctx.message.add_reaction(
                    '<:greenTick:596576670815879169>'
                )
        else:
            try:
                self.bot.load_extension(f'Cogs.{file.lower().capitalize()}')
            except Exception as e:
                await ctx.send(e)
            else:
                await ctx.message.add_reaction(
                    '<:greenTick:596576670815879169>'
                )

    @dev.command()
    async def unload(self, ctx, file: str):
        if file == '*':
            errors = []
            extensions = [
                'Fun',
                'Utility',
                'Images',
                'jishaku',
                'Music',
                'Economy',
                'Help',
                'Owner',
                'Prefix',
            ]
            for cog in extensions:
                try:
                    self.bot.unload_extension(f'Cogs.{cog}')
                except Exception as e:
                    errors.append(str(e))
            if errors:
                await ctx.send('\n'.join(errors))
            else:
                await ctx.message.add_reaction(
                    '<:greenTick:596576670815879169>'
                )
        else:
            try:
                self.bot.unload_extension(f'Cogs.{file.lower().capitalize()}')
            except Exception as e:
                await ctx.send(e)
            else:
                await ctx.message.add_reaction(
                    '<:greenTick:596576670815879169>'
                )

    @sql.error
    async def on_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original
            await ctx.send(error)

    @commands.command()
    async def botcdn(
        self, ctx, *, title: str = 'Image Uploaded By MrKomododDragon'
    ):
        time = datetime.datetime.now()
        image = await ctx.message.attachments[0].read()
        time = time.strftime('%A, %B %d %Y, at %X')
        embeds_dict = {
            'color': '#525a32',
            'title': title,
            'description': f'Uploaded by MrKomodoDragon at {time} PDT',
        }
        data_ = {
            'image': image,
            'token': os.getenv('SXCU'),
            'og_properties': json.dumps(embeds_dict),
        }
        async with self.bot.session.post(
            'https://komodo.has-no-bra.in/upload', data=data_
        ) as resp:
            data = await resp.json()
        await ctx.send(data.get('url'))


def setup(bot):
    bot.add_cog(Owner(bot))
