from typing import Dict, List, Any

DISCORD_SAFE_LIMIT = 3800


def _short(s: str, n: int = 180) -> str:
    s = (s or "").replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def _chunk_for_discord(text: str, limit: int = DISCORD_SAFE_LIMIT) -> List[str]:
    lines = text.split("\n")
    chunks = []
    buf = ""

    for line in lines:
        if len(buf) + len(line) + 1 > limit:
            if buf.strip():
                chunks.append(buf.rstrip())
            buf = line + "\n"
        else:
            buf += line + "\n"

    if buf.strip():
        chunks.append(buf.rstrip())

    return chunks


def _fmt(items: List[Dict[str, Any]], max_items: int = 12) -> str:
    if not items:
        return "- (none)"

    shown = items[:max_items]
    lines = []

    for i in shown:
        title = _short(i.get("title", ""), 160)
        link = (i.get("link", "") or "").strip()
        lines.append(f"- {title} — {link}" if link else f"- {title}")

    remaining = len(items) - len(shown)
    if remaining > 0:
        lines.append(f"\n_(+ {remaining} more items pulled but not shown)_")

    return "\n".join(lines)


def vinderprime_daily_brief(signals: Dict) -> Dict:
    reddit = signals.get("reddit", {})
    reddit_items = reddit.get("accepted", [])
    audit = reddit.get("audit", {})

    youtube = signals.get("youtube", [])
    x_items = signals.get("x", [])

    volume_snapshot = (
        "## Volume Snapshot\n"
        f"- Pulled (raw): **{audit.get('raw_pulled', 0)}**\n"
        f"- After dedupe: **{audit.get('after_dedupe', 0)}**\n"
        f"- Judged: **{audit.get('judged', 0)}**\n"
        f"- Accepted: **{audit.get('accepted', 0)}**\n"
        f"- Rejected: **{audit.get('rejected', 0)}**\n"
    )

    if audit.get("top_rejections"):
        volume_snapshot += "\n**Top Rejection Reasons:**\n"
        for reason, count in audit["top_rejections"]:
            volume_snapshot += f"- {reason}: {count}\n"

    daily_full = (
        "# Daily Brief — VinderPrime\n\n"
        + volume_snapshot
        + "\n## Reddit Signals (Accepted)\n"
        + _fmt(reddit_items, max_items=15)
        + "\n\n## YouTube Signals\n"
        + _fmt(youtube, max_items=10)
        + "\n\n## X Signals (stub)\n"
        + _fmt(x_items, max_items=10)
    )

    return {
        "control_room_summary": "VinderPrime audit complete. See daily brief.",
        "daily_brief_full": _chunk_for_discord(daily_full),
        "tasks": [],
        "push_candidates": [],
    }