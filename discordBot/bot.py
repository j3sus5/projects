import asyncio
import discord
from discord.ext import commands

from config import DISCORD_BOT_TOKEN, TEST_GUILD_ID
from database import init_db

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id: {bot.user.id})")

    if TEST_GUILD_ID:
        guild = discord.Object(id=TEST_GUILD_ID)
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
    else:
        synced = await bot.tree.sync()

    print(f"Synced {len(synced)} slash command(s).")
    print("------")


async def load_cogs():
    await bot.load_extension("cogs.trades")


async def main():
    init_db()
    async with bot:
        await load_cogs()
        await bot.start(DISCORD_BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())