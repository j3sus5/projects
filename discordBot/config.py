import os
from dotenv import load_dotenv
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

if not DISCORD_BOT_TOKEN:
    raise RuntimeError(
        "DISCORD_BOT_TOKEN is not set. Copy .env.example to .env and add your bot token."
    )

DATABASE_PATH = os.getenv("DATABASE_PATH", "bot.db")

_test_guild = os.getenv("TEST_GUILD_ID")
TEST_GUILD_ID = int(_test_guild) if _test_guild else None