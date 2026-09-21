import asyncio
import discord
from discord.ext import commands
from config import DISCORD_BOT_TOKEN, TEST_GUILD_ID
from database import init_db
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # silence noisy request logs


def run_health_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()


threading.Thread(target=run_health_server, daemon=True).start()

intents = discord.Intents.default()

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id: {bot.user.id})")
    print(f"TEST_GUILD_ID is: {TEST_GUILD_ID}")

    try:
        if TEST_GUILD_ID:
            guild = discord.Object(id=TEST_GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
        else:
            synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s): {[c.name for c in synced]}")
    except Exception as e:
        print(f"SYNC ERROR: {e}")
        import traceback
        traceback.print_exc()

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