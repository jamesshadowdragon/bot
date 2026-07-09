import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

import config
import database

load_dotenv()

TOKEN = os.getenv("TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

COGS = [
    "cogs.invites",
    "cogs.rewards",
    "cogs.giveaways",
    "cogs.logging",
    "cogs.leaderboard"
]


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    guild = discord.Object(id=config.GUILD_ID)

    try:
        synced = await bot.tree.sync(guild=guild)
        print(f"Synced {len(synced)} slash commands.")
    except Exception as e:
        print(e)


async def load_extensions():
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"Loaded {cog}")
        except Exception as e:
            print(f"Failed loading {cog}: {e}")


async def main():
    async with bot:
        await load_extensions()
        await bot.start(TOKEN)


import asyncio
asyncio.run(main())
