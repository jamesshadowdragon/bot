import discord
from discord.ext import commands
from discord import app_commands

import config
import database

class InviteTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.invites = {}

    async def cache_invites(self):
        guild = self.bot.get_guild(config.GUILD_ID)

        if guild is None:
            return

        try:
            self.invites[guild.id] = await guild.invites()
            print(f"Cached {len(self.invites[guild.id])} invites.")
        except discord.Forbidden:
            print("Missing Manage Server permission to read invites.")

    @commands.Cog.listener()
    async def on_ready(self):
        await self.cache_invites()

    @commands.Cog.listener()
    async def on_invite_create(self, invite):
        if invite.guild.id != config.GUILD_ID:
            return

        self.invites[invite.guild.id] = await invite.guild.invites()

    @commands.Cog.listener()
    async def on_invite_delete(self, invite):
        if invite.guild.id != config.GUILD_ID:
            return

        self.invites[invite.guild.id] = await invite.guild.invites()

    @commands.Cog.listener()
    async def on_member_join(self, member):

        if member.guild.id != config.GUILD_ID:
            return

        before = self.invites.get(member.guild.id, [])
        after = await member.guild.invites()

        inviter = None

        for old in before:
            for new in after:
                if old.code == new.code and new.uses > old.uses:
                    inviter = new.inviter
                    break

        self.invites[member.guild.id] = after

        if inviter is None:
            return

        await database.add_invite(inviter.id)
        await database.save_inviter(member.id, inviter.id)

        total = await database.get_invites(inviter.id)

        if config.LOG_CHANNEL_ID != 0:
            channel = member.guild.get_channel(config.LOG_CHANNEL_ID)

            if channel:

                embed = discord.Embed(
                    title="Member Joined",
                    color=config.SUCCESS_COLOR
                )

                embed.add_field(
                    name="Member",
                    value=f"{member.mention}\n{member.id}",
                    inline=False
                )

                embed.add_field(
                    name="Invited By",
                    value=f"{inviter.mention}",
                    inline=False
                )

                embed.add_field(
                    name="Total Invites",
                    value=str(total),
                    inline=False
                )

                embed.set_thumbnail(url=member.display_avatar.url)

                await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        if member.guild.id != config.GUILD_ID:
            return

        inviter_id = await database.get_inviter(member.id)

        if inviter_id:
            await database.remove_invite(inviter_id)

            self.invites[member.guild.id] = await member.guild.invites()

    @app_commands.command(
        name="invites",
        description="Shows your invite count."
    )
    async def invites(self, interaction: discord.Interaction):

        if interaction.guild.id != config.GUILD_ID:
            return

        invites = await database.get_invites(interaction.user.id)

        embed = discord.Embed(
            title="Invite Count",
            description=f"You currently have **{invites}** invites.",
            color=config.INFO_COLOR
        )

        await interaction.response.send_message(embed=embed)

    @app_commands.command(
        name="inviter",
        description="Shows who invited you."
    )
    async def inviter(self, interaction: discord.Interaction):

        if interaction.guild.id != config.GUILD_ID:
            return

        inviter = await database.get_inviter(interaction.user.id)

        if inviter is None:
            await interaction.response.send_message(
                "No inviter could be found.",
                ephemeral=True
            )
            return

        user = interaction.guild.get_member(inviter)

        if user is None:
            text = f"User ID: {inviter}"
        else:
            text = user.mention

        embed = discord.Embed(
            title="Your Inviter",
            description=text,
            color=config.INFO_COLOR
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    cog = InviteTracker(bot)

    await bot.add_cog(cog, guild=discord.Object(id=config.GUILD_ID))
