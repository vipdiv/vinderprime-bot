import feedparser
import requests

SUBREDDITS = [
    # include both, because people use both spellings
    "CircuitOfTheAmerica",
    "CircuitOfTheAmericas",
    "Austin",
    "aclfestival",
    "SXSW",
]

KEYWORDS = [
    "cota",
    "circuit of the americas",
    "f1",
    "motogp",
    "nascar",
    "parking",
    "rideshare",
    "uber",
    "lyft",
    "pickup",
    "drop off",
    "dropoff",
    "shuttle",
    "traffic",
    "leaving",
    "exit",
    "wait",
    "line",
    "surge",
    "lot",
    "bus",
    "transit",
    "capmetro",
    "driving",
    "drive",
    "taxi",
    "rides",
    "riding",
    "ride",
    # racing/moto terms
    "racer",
    "race",
    "aprilia",
    "motorcycle",
    "motorcycles",
    "motorbike",
    "motorbikes",
]

UA = "VinderPrimeBot/1.0 (RouteRadar.pro; contact: admin@routeradar.pro)"


def _get_feed(url: str):
    """Fetch RSS with a User-Agent so Reddit doesn't silently block."""
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
        print(f"[reddit] GET {url} -> {r.status_code}")
        if r.status_code != 200:
            print(f"[reddit] WARN {r.status_code} for {url}")
            return feedparser.parse("")
        return feedparser.parse(r.content)
    except Exception as e:
        print(f"[reddit] ERROR fetching {url}: {e}")
        return feedparser.parse("")


def _contains_keywords(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in KEYWORDS)


def fetch_reddit_rss(query: str = "", limit: int = 15):
    items = []
    raw_total = 0
    kept_total = 0

    for sub in SUBREDDITS:
        # Use new.rss for better coverage of recent posts
        url = f"https://www.reddit.com/r/{sub}/new.rss"
        feed = _get_feed(url)

        if getattr(feed, "bozo", False):
            bozo_exc = getattr(feed, "bozo_exception", None)
            if bozo_exc:
                print(f"[reddit] BOZO for r/{sub}: {bozo_exc}")

        raw = len(feed.entries)
        raw_total += raw

        kept_here = 0
        for e in feed.entries:
            title = e.get("title", "") or ""
            link = e.get("link", "") or ""
            published = e.get("published", "") or ""

            # Reddit RSS often has summary/content; we normalize to "summary"
            summary = e.get("summary", "") or ""
            if not summary and "content" in e and e["content"]:
                try:
                    summary = e["content"][0].get("value", "") or ""
                except Exception:
                    summary = ""

            if sub in ("CircuitOfTheAmerica", "CircuitOfTheAmericas"):
                # core community: keep all
                items.append(
                    {
                        "title": title,
                        "link": link,
                        "published": published,
                        "summary": summary,
                        "subreddit": sub,
                    }
                )
                kept_here += 1
            else:
                # strict filtering for Austin/SXSW/ACL
                hay = f"{title} {summary}"
                if _contains_keywords(hay):
                    items.append(
                        {
                            "title": title,
                            "link": link,
                            "published": published,
                            "summary": summary,
                            "subreddit": sub,
                        }
                    )
                    kept_here += 1

        kept_total += kept_here
        print(f"[reddit] r/{sub}: raw={raw} kept={kept_here}")

    # newest first (published is string but ok)
    items.sort(key=lambda x: x.get("published", ""), reverse=True)

    # simple link dedupe (judge.py does smarter dedupe later too)
    seen = set()
    deduped = []
    for it in items:
        link = (it.get("link") or "").strip()
        if link and link in seen:
            continue
        if link:
            seen.add(link)
        deduped.append(it)

    print(f"[reddit] TOTAL raw={raw_total} kept={kept_total} deduped={len(deduped)} returning={min(limit, len(deduped))}")
    return deduped[:limit]
