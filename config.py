import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "")
GUILD_ID = int(os.getenv("GUILD_ID", "0"))

CATEGORY_NAME = os.getenv("CATEGORY_NAME", "🚦 Route Radar Pro — Factory")
CONTROL_ROOM = os.getenv("CONTROL_ROOM", "control-room")
DAILY_BRIEF = os.getenv("DAILY_BRIEF", "daily-brief")
PUSH_REQUESTS = os.getenv("PUSH_REQUESTS", "push-requests")
FACTORY_LOG = os.getenv("FACTORY_LOG", "factory-log")

MISSION_CONTROL_BASE_URL = os.getenv("MISSION_CONTROL_BASE_URL", "http://localhost:3000")

TIMEZONE = os.getenv("TIMEZONE", "America/Chicago")
RUN_HOUR = int(os.getenv("RUN_HOUR", "7"))
RUN_MINUTE = int(os.getenv("RUN_MINUTE", "45"))
