import os
import json
import asyncio
from datetime import datetime
from typing import Any, Dict, List
from urllib.parse import urljoin

import aiohttp
import discord
from discord.ext import commands
from zoneinfo import ZoneInfo

# -----------------------------
# ENV
# -----------------------------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "")
CONTROL_ROOM_CHANNEL_ID = os.getenv("CONTROL_ROOM_CHANNEL_ID", "")
MISSION_CONTROL_BASE_URL = os.getenv("MISSION_CONTROL_BASE_URL", "http://localhost:3000")
VP_TZ = os.getenv("VP_TZ", "America/Chicago")

if not DISCORD_TOKEN:
    raise RuntimeError("Missing DISCORD_TOKEN")
if not CONTROL_ROOM_CHANNEL_ID:
    raise RuntimeError("Missing CONTROL_ROOM_CHANNEL_ID")

CONTROL_ROOM_CHANNEL_ID_INT = int(CONTROL_ROOM_CHANNEL_ID)
TZ = ZoneInfo(VP_TZ)

# -----------------------------
# TIME HELPERS
# -----------------------------
def now_local() -> datetime:
    return datetime.now(TZ)

def now_utc_iso_z() -> str:
    # ISO UTC ending with Z
    return datetime.utcnow().replace(tzinfo=ZoneInfo("UTC")).isoformat().replace("+00:00", "Z")

def vp_date(dt_local: datetime) -> str:
    # Chicago local calendar day
    return dt_local.date().isoformat()

def fmt_local(dt_local: datetime) -> str:
    return dt_local.strftime("%a %b %d, %Y %I:%M:%S %p %Z")

# -----------------------------
# MISSION CONTROL API
# -----------------------------
async def post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, timeout=30) as resp:
            text = await resp.text()
            if resp.status >= 400:
                raise RuntimeError(f"POST {url} failed {resp.status}: {text[:500]}")
            try:
                return json.loads(text)
            except Exception:
                return {"raw": text}

def build_today_tasks() -> List[Dict[str, str]]:
    # Replace these with your real generated tasks if you want.
    return [
        {"title": "Cluster COTA pain points into 3 themes", "notes": "Use Reddit + YouTube signals; write bullets."},
        {"title": "Write 8 How-Might-We questions for the top theme", "notes": "Make them testable."},
        {"title": "Create impact/effort matrix for 10 solution ideas", "notes": "Mark top 3 quick wins."},
        {"title": "Draft a 'COTA Pickup Survival' message template", "notes": "Short SMS + longer version."},
        {"title": "Define 1 experiment to validate demand this week", "notes": "No live posting; prep only."},
    ]

async def push_tasks_to_mission_control(tasks: List[Dict[str, str]]) -> Dict[str, Any]:
    dt_local = now_local()
    vpdate = vp_date(dt_local)
    createdAt = now_utc_iso_z()
    createdAtLocal = fmt_local(dt_local)

    enriched = []
    for t in tasks:
        enriched.append({
            "title": t["title"],
            "notes": t.get("notes", ""),
            "lane": "backlog",
            "source": "vinderprime",
            "createdAt": createdAt,              # UTC storage
            "createdAtLocal": createdAtLocal,    # pretty display
            "vpDate": vpdate,                    # ✅ local calendar day key
        })

    url = urljoin(MISSION_CONTROL_BASE_URL, "/api/tasks/bulk")
    return await post_json(url, {"tasks": enriched})

# -----------------------------
# DISCORD BOT
# -----------------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

async def send_control_room(message: str):
    ch = bot.get_channel(CONTROL_ROOM_CHANNEL_ID_INT)
    if not ch:
        ch = await bot.fetch_channel(CONTROL_ROOM_CHANNEL_ID_INT)
    await ch.send(message)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Control room channel: {CONTROL_ROOM_CHANNEL_ID_INT}")
    print(f"Mission Control URL: {MISSION_CONTROL_BASE_URL}")
    print(f"VP_TZ: {VP_TZ}")

@bot.command(name="runnow")
async def runnow(ctx: commands.Context):
    # Force this command to run only in the Control Room channel
    if ctx.channel.id != CONTROL_ROOM_CHANNEL_ID_INT:
        await ctx.reply("Run `!runnow` in the Control Room channel only.")
        return

    dt_local = now_local()
    vpdate = vp_date(dt_local)

    await send_control_room(
        "Running daily cycle now…\n"
        f"🗓️ Local day: **{vpdate}** ({VP_TZ})\n"
        f"⏰ {fmt_local(dt_local)}"
    )

    tasks = build_today_tasks()

    try:
        res = await push_tasks_to_mission_control(tasks)
        added = res.get("added", "unknown")

        await send_control_room(
            f"VinderPrime audit complete. See daily brief.\n\n"
            f"**Today’s tasks (Local day: {vpdate} {VP_TZ})**\n"
            + "\n".join([f"- {t['title']}" for t in tasks])
            + "\n\n"
            f"✅ Tasks pushed to Mission Control. (added={added})\n"
            "Done ✅"
        )
    except Exception as e:
        await send_control_room(f"❌ Push failed: `{e}`")

bot.run(DISCORD_TOKEN)