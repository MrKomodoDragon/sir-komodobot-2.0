import re
from discord.ext import commands
import discord
class KomodoContext(commands.Context):
    def embed(self, **kwargs):
        color = kwargs.pop('color', self.bot.embed_color)
        embed = discord.Embed(**kwargs, color=color)
        embed.timestamp = self.message.created_at
        embed.set_footer(
            text=f'Requested by {self.author}', icon_url=self.author.avatar.url # type: ignore
        )
        return embed

    @property
    def clean_prefix(self) -> str:
        """:class:`str`: The cleaned up invoke prefix. i.e. mentions are ``@name`` instead of ``<@id>``."""
        user = self.guild.me if self.guild else self.bot.user # type: ignore
        # this breaks if the prefix mention is not the bot itself but I
        # consider this to be an *incredibly* strange use case. I'd rather go
        # for this common use case rather than waste performance for the
        # odd one.
        pattern: re.Pattern = re.compile(r'<@!?%s>' % user.id)
        return pattern.sub(
            '@%s' % user.display_name.replace('\\', r'\\'), self.prefix
        )
