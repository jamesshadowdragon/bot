import discord
import time
import re
from discord.ext import commands, tasks
from discord import app_commands

import config
import database

TIME_PATTERN = re.compile(r"^(\d+)([smhd])$")

def parse_time(text:str):
    m = TIME_PATTERN.match(text.lower())
    if not m:
        return None
    n = int(m.group(1))
    u = m.group(2)
    return {"s":n,"m":n*60,"h":n*3600,"d":n*86400}[u]

class GiveawayButton(discord.ui.Button):
    def __init__(self):
        super().__init__(label="Enter Giveaway",
                         style=discord.ButtonStyle.green,
                         custom_id="giveaway_enter")

    async def callback(self, interaction: discord.Interaction):
        await database.add_entry(interaction.message.id, interaction.user.id)
        await interaction.response.send_message(
            "You have entered this giveaway.",
            ephemeral=True
        )

class GiveawayView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(GiveawayButton())

class Giveaways(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_view(GiveawayView())
        self.giveaway_loop.start()

    def cog_unload(self):
        self.giveaway_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Giveaway system loaded.")

    @tasks.loop(seconds=30)
    async def giveaway_loop(self):
        giveaways = await database.get_active_giveaways()
        now = int(time.time())
        for message_id, channel_id, prize, winners, end_time in giveaways:
            if now >= end_time:
                print(f"Giveaway ended: {message_id}")
                await database.end_giveaway(message_id)

    @giveaway_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="gcreate", description="Create a giveaway.")
    @app_commands.describe(
        duration="Example: 30m, 2h, 1d",
        winners="Number of winners",
        prize="Prize"
    )
    async def gcreate(
        self,
        interaction: discord.Interaction,
        duration: str,
        winners: app_commands.Range[int,1,50],
        prize: str
    ):
        if interaction.guild is None or interaction.guild.id != config.GUILD_ID:
            return

        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "You do not have permission.",
                ephemeral=True
            )
            return

        seconds = parse_time(duration)
        if seconds is None:
            await interaction.response.send_message(
                "Invalid duration. Example: 30m, 2h, 7d",
                ephemeral=True
            )
            return

        end_timestamp = int(time.time()) + seconds

        embed = discord.Embed(title=prize, color=config.INFO_COLOR)
        embed.add_field(name="Winners", value=str(winners), inline=False)
        embed.add_field(
            name="Ends",
            value=f"<t:{end_timestamp}:F>\n<t:{end_timestamp}:R>",
            inline=False
        )
        embed.set_footer(text=f"Hosted by {interaction.user}")

        await interaction.response.send_message(
            "Creating giveaway...",
            ephemeral=True
        )

        message = await interaction.channel.send(
            embed=embed,
            view=GiveawayView()
        )

        await database.create_giveaway(
            message.id,
            interaction.channel.id,
            prize,
            winners,
            end_timestamp
        )

        await interaction.edit_original_response(
            content="Giveaway created successfully."
        )

async def setup(bot):
    await bot.add_cog(
        Giveaways(bot),
        guild=discord.Object(id=config.GUILD_ID)
    )
