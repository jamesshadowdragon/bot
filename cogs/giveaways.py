import discord
import time
import re

from discord.ext import commands, tasks
from discord import app_commands

import config
import database


# -------------------------
# Time Parser
# -------------------------

TIME_PATTERN = re.compile(r"^(\d+)([smhd])$")


def parse_time(text: str):

    text = text.lower()

    match = TIME_PATTERN.match(text)

    if match is None:
        return None

    amount = int(match.group(1))
    unit = match.group(2)

    if unit == "s":
        return amount

    if unit == "m":
        return amount * 60

    if unit == "h":
        return amount * 3600

    if unit == "d":
        return amount * 86400

    return None


# -------------------------
# Giveaway Button
# -------------------------

class GiveawayButton(discord.ui.Button):

    def __init__(self):

        super().__init__(
            label="Enter Giveaway",
            style=discord.ButtonStyle.green,
            custom_id="giveaway_enter"
        )

    async def callback(self, interaction: discord.Interaction):

        message_id = interaction.message.id

        await database.add_entry(
            message_id,
            interaction.user.id
        )

        await interaction.response.send_message(
            "You have entered this giveaway.",
            ephemeral=True
        )


# -------------------------
# Giveaway View
# -------------------------

class GiveawayView(discord.ui.View):

    def __init__(self):

        super().__init__(timeout=None)

        self.add_item(GiveawayButton())
        # -------------------------
# Giveaway Cog
# -------------------------

class Giveaways(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        # Register the persistent button
        self.bot.add_view(GiveawayView())

        # Start background task
        self.giveaway_loop.start()

    def cog_unload(self):
        self.giveaway_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Giveaway system loaded.")

    # -------------------------
    # Giveaway Loop
    # -------------------------

    @tasks.loop(seconds=30)
    async def giveaway_loop(self):
        """
        Checks every 30 seconds for giveaways that have ended.
        Winner selection will be added in Part 5.3.
        """

        giveaways = await database.get_active_giveaways()

        now = int(time.time())

        for giveaway in giveaways:

            message_id = giveaway[0]
            channel_id = giveaway[1]
            prize = giveaway[2]
            winners = giveaway[3]
            end_time = giveaway[4]

            if now >= end_time:

                print(
                    f"Giveaway ended: {message_id} ({prize})"
                )

                # Placeholder
                # Winner selection will be implemented later.

                await database.end_giveaway(message_id)

    @giveaway_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()
