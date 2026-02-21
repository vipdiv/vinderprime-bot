import feedparser
import requests

# Pick a few "boots on the ground" channels that are likely to mention traffic/parking/shuttles.
# You can add/remove later.
YOUTUBE_CHANNEL_IDS = [
    # Example placeholders — swap in real IDs later:
    # "UCxxxxxxxxxxxxxxxxxxxxxx",  # COTA official (if you want)
    # "UCxxxxxxxxxxxxxxxxxxxxxx",  # local Austin news traffic
]

# If you leave this empty, it will return [] (safe).
# That way YouTube won't break your pipeline.
UA = "VinderPrimeBot/1.0 (RouteRadar.pro; contact: admin@routeradar.pro)"

TRANSPORT_KEYWORDS = [
    "parking", "rideshare", "uber", "lyft", "pickup", "drop off", "dropoff",
    "shuttle", "traffic", "exit", "leaving", "line", "wait", "lot",
    "bus", "transit", "capmetro", "taxi", "ride", "rides", "riding",
    "route", "detour", "closure", "closed", "walk", "walking",
]

EVENT_KEYWORDS = [
    "cota", "circuit of the americas", "f1", "formula 1", "motogp", "nascar",
    "acl", "aclfestival", "sxsw",
    "race", "racer", "racing", "aprilia", "motorcycle", "motorbikes", "motorbike",
]

def _contains_any(text: str, keywords) -> bool:
    t = (text or "").lower()
    return any(k in t for k in keywords)

def _get_feed(url: str):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=20)
        if r.status_code != 200:
            print(f"[youtube] WARN {r.status_code} for {url}")
            return feedparser.parse("")
        return feedparser.parse(r.content)
    except Exception as e:
        print(f"[youtube] ERROR fetching {url}: {e}")
        return feedparser.parse("")

def fetch_youtube_rss(query: str, limit: int = 8):
    """
    YouTube RSS does NOT support search_query in the official feed.
    So we pull from known channel feeds, then filter locally.
    """
    if not YOUTUBE_CHANNEL_IDS:
        # Safe behavior: don't break the pipeline if you haven't chosen channels yet.
        return []

    items = []

    for cid in YOUTUBE_CHANNEL_IDS:
        url = f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}"
        feed = _get_feed(url)

        for e in feed.entries:
            title = (e.get("title", "") or "").strip()
            link = (e.get("link", "") or "").strip()
            published = (e.get("published", "") or "").strip()
            summary = (e.get("summary", "") or "").strip()

            blob = f"{title}\n{summary}"

            # Keep only things likely relevant to our world
            if _contains_any(blob, EVENT_KEYWORDS) or _contains_any(blob, TRANSPORT_KEYWORDS):
                items.append({
                    "title": title,
                    "link": link,
                    "published": published,
                    "summary": summary,
                    "source": f"youtube:{cid}",
                })

    # newest-ish first
    items.sort(key=lambda x: x.get("published", ""), reverse=True)

    # de-dupe by link
    seen = set()
    out = []
    for it in items:
        if it["link"] in seen:
            continue
        seen.add(it["link"])
        out.append(it)

    return out[:limit]
