import discord
from config import CATEGORY_NAME, CONTROL_ROOM, DAILY_BRIEF, PUSH_REQUESTS, FACTORY_LOG

AGENT_CHANNELS = [
    "agent-reddit-scout",
    "agent-youtube-scout",
    "agent-x-scout",
    "agent-pain-miner",
    "agent-hmw-smith",
    "agent-matrix-builder",
    "agent-build-lab",
]

async def ensure_factory_structure(guild: discord.Guild):
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if category is None:
        category = await guild.create_category(CATEGORY_NAME)

    async def ensure_text_channel(name: str):
        # Prefer a channel in our category; create if missing.
        ch = discord.utils.get(guild.text_channels, name=name)
        if ch and ch.category_id == category.id:
            return ch
        if ch is None:
            return await guild.create_text_channel(name=name, category=category)
        return ch

    control = await ensure_text_channel(CONTROL_ROOM)
    daily = await ensure_text_channel(DAILY_BRIEF)
    push = await ensure_text_channel(PUSH_REQUESTS)
    log = await ensure_text_channel(FACTORY_LOG)

    for name in AGENT_CHANNELS:
        await ensure_text_channel(name)

    return {
        "category": category,
        "control_room": control,
        "daily_brief": daily,
        "push_requests": push,
        "factory_log": log,
    }
