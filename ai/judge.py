import os
import json
from typing import Any, Dict, List
from difflib import SequenceMatcher
from collections import Counter
from pathlib import Path

from ai.cache import load_cache, save_cache, cache_get, cache_set
from ai.providers import GeminiProvider, GroqProvider, make_key

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

ACCEPTED_LOG = LOG_DIR / "accepted.jsonl"
REJECTED_LOG = LOG_DIR / "rejected.jsonl"


def _norm(s: str) -> str:
    s = (s or "").lower()
    s = "".join(c for c in s if c.isalnum() or c.isspace())
    return " ".join(s.split())


def dedupe(items: List[Dict[str, Any]], threshold: float = 0.88) -> List[Dict[str, Any]]:
    seen_links = set()
    kept = []
    kept_texts = []

    for it in items:
        link = (it.get("link") or "").strip()
        if link and link in seen_links:
            continue
        if link:
            seen_links.add(link)

        text = _norm((it.get("title") or "") + " " + (it.get("summary") or ""))
        near_dup = any(
            SequenceMatcher(None, text, prev).ratio() >= threshold
            for prev in kept_texts
        )
        if near_dup:
            continue

        kept.append(it)
        kept_texts.append(text)

    return kept


def _log(path: Path, payload: Dict[str, Any]):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def judge_items(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    provider_mode = os.getenv("AI_PROVIDER", "gemini").strip().lower()

    raw_count = len(items)
    items = dedupe(items)
    deduped_count = len(items)

    gemini = GeminiProvider()
    groq = GroqProvider()
    cache = load_cache()

    accepted = []
    rejected = []
    rejection_reasons = Counter()

    def run_provider(name: str, title: str, summary: str, link: str, subreddit: str):
        key = make_key(name, title, summary, link, subreddit)
        cached = cache_get(cache, key)
        if cached:
            return cached
        if name == "gemini":
            res = gemini.judge(title, summary, link, subreddit)
        else:
            res = groq.judge(title, summary, link, subreddit)
        cache_set(cache, key, res, name)
        save_cache(cache)
        return res

    for it in items:
        title = it.get("title", "") or ""
        summary = it.get("summary", "") or ""
        link = it.get("link", "") or ""
        subreddit = it.get("subreddit", "") or ""

        if provider_mode == "off":
            verdict = {
                "relevant": True,
                "confidence": 0.0,
                "why": "ai_off",
                "tags": [],
            }
        else:
            if provider_mode == "groq":
                verdict = (
                    run_provider("groq", title, summary, link, subreddit)
                    if groq.available()
                    else {"relevant": False, "confidence": 0.0, "why": "groq_key_missing", "tags": []}
                )
            else:
                verdict = (
                    run_provider("gemini", title, summary, link, subreddit)
                    if gemini.available()
                    else {"relevant": False, "confidence": 0.0, "why": "gemini_key_missing", "tags": []}
                )

        record = {
            "title": title,
            "link": link,
            "subreddit": subreddit,
            "verdict": verdict,
        }

        if verdict.get("relevant"):
            accepted.append({**it, "ai": verdict})
            _log(ACCEPTED_LOG, record)
        else:
            rejected.append({**it, "ai": verdict})
            rejection_reasons[verdict.get("why", "unknown")] += 1
            _log(REJECTED_LOG, record)

    return {
        "accepted": accepted,
        "audit": {
            "raw_pulled": raw_count,
            "after_dedupe": deduped_count,
            "judged": deduped_count,
            "accepted": len(accepted),
            "rejected": len(rejected),
            "top_rejections": rejection_reasons.most_common(5),
        },
    }