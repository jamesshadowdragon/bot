import discord
from discord.ext import commands

import config
import database


class RewardRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def update_rewards(self, member: discord.Member):
        invites = await database.get_invites(member.id)

        # Sort rewards from lowest to highest
        rewards = sorted(config.INVITE_REWARDS.items())

        for required, role_id in rewards:

            role = member.guild.get_role(role_id)

            if role is None:
                continue

            if invites >= required:

                if role not in member.roles:
                    try:
                        await member.add_roles(
                            role,
                            reason="Invite reward"
                        )
                    except discord.Forbidden:
                        pass

            else:

                if role in member.roles:
                    try:
                        await member.remove_roles(
                            role,
                            reason="Invite reward removed"
                        )
                    except discord.Forbidden:
                        pass

    @commands.Cog.listener()
    async def on_member_join(self, member):

        if member.guild.id != config.GUILD_ID:
            return

        inviter_id = await database.get_inviter(member.id)

        if inviter_id is None:
            return

        inviter = member.guild.get_member(inviter_id)

        if inviter:
            await self.update_rewards(inviter)

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        if member.guild.id != config.GUILD_ID:
            return

        inviter_id = await database.get_inviter(member.id)

        if inviter_id is None:
            return

        inviter = member.guild.get_member(inviter_id)

        if inviter:
            await self.update_rewards(inviter)


async def setup(bot):
    await bot.add_cog(
        RewardRoles(bot),
        guild=discord.Object(id=config.GUILD_ID)
    )
