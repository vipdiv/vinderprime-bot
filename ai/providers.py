import json
import os
import hashlib
import re
import time
import random
from typing import Dict, Any, Optional, Callable

from ai.rate_limit import RateLimiter

# Gemini
from google import genai

# Groq
from groq import Groq

TAGS = [
    "rideshare", "pickup", "dropoff", "shuttle", "parking", "traffic",
    "timing", "route", "lot", "line", "surge", "transit", "capmetro",
    "walking", "rv", "accessibility", "pricing"
]

SYSTEM = f"""
You are VinderPrime's strict relevance filter for Route Radar.

Decide if a post is relevant to transportation/logistics for getting to/from:
- COTA (Circuit of the Americas)
- ACL Festival
- SXSW
- Major Austin event travel logistics

Transportation/logistics includes: pickup/dropoff points, rideshare/taxi, shuttle/bus, parking, traffic flow,
leaving/exiting, timing, lots, routes, RV/camping access, accessibility, surge/pricing.

Return STRICT JSON only with keys:
relevant (boolean), confidence (number 0-1), why (string <= 200 chars), tags (array of strings).

Allowed tags: {TAGS}

If it's general commuting, generic road news, politics, unrelated Austin chatter, or event seating/turn advice with no transport angle:
relevant=false.
""".strip()


def make_key(provider: str, title: str, summary: str, link: str, subreddit: str) -> str:
    base = f"{provider}|{link.strip()}|{subreddit.strip()}|{title.strip()}|{summary.strip()}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def normalize_result(obj: Dict[str, Any]) -> Dict[str, Any]:
    try:
        relevant = bool(obj.get("relevant", False))
        confidence = float(obj.get("confidence", 0.0))
        why = str(obj.get("why", ""))[:200]
        tags = obj.get("tags", [])
        if not isinstance(tags, list):
            tags = []
        tags = [t for t in tags if t in TAGS][:6]
        return {"relevant": relevant, "confidence": confidence, "why": why, "tags": tags}
    except Exception:
        return {"relevant": False, "confidence": 0.0, "why": "normalize_failed", "tags": []}


# -------------------------
# FIX 2: Safe JSON handling
# -------------------------
def _extract_json(text: str) -> str:
    """
    Try to extract a JSON object from model output.
    Handles:
      - empty responses
      - ```json ... ``` fences
      - extra prose before/after JSON
    """
    if not text:
        return ""

    t = text.strip()

    # Strip fenced blocks
    t = re.sub(r"^```json\s*", "", t, flags=re.IGNORECASE).strip()
    t = re.sub(r"^```\s*", "", t).strip()
    t = re.sub(r"\s*```$", "", t).strip()

    # If already JSON-shaped
    if t.startswith("{") and t.endswith("}"):
        return t

    # Try first {...} block
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        return t[start:end + 1]

    return ""


def safe_load_json(text: str) -> Optional[Dict[str, Any]]:
    raw = (text or "").strip()
    if not raw:
        return None

    payload = _extract_json(raw)
    if not payload:
        return None

    try:
        obj = json.loads(payload)
        if isinstance(obj, dict):
            return obj
        return None
    except Exception:
        return None


# -------------------------
# FIX 3: Backoff & retry
# -------------------------
def with_backoff(fn: Callable[[], Any], max_retries: int = 3, base_delay: float = 0.6) -> Any:
    """
    Retry on common transient errors: 429, RESOURCE_EXHAUSTED, timeouts.
    Exponential backoff with jitter.
    """
    for attempt in range(max_retries + 1):
        try:
            return fn()
        except Exception as e:
            msg = str(e)
            lower = msg.lower()

            retryable = (
                ("429" in msg) or
                ("resource_exhausted" in lower) or
                ("timeout" in lower) or
                ("timed out" in lower) or
                ("temporarily unavailable" in lower)
            )

            if (not retryable) or (attempt >= max_retries):
                raise

            delay = base_delay * (2 ** attempt) + (random.random() * 0.25)
            time.sleep(delay)


class GeminiProvider:
    def __init__(self):
        self.key = os.getenv("GEMINI_API_KEY", "").strip()
        self.model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip()
        rpm = int(os.getenv("GEMINI_RPM", "60"))
        self.limiter = RateLimiter(rpm)
        self.client = genai.Client(api_key=self.key) if self.key else None

    def available(self) -> bool:
        return bool(self.client)

    def judge(self, title: str, summary: str, link: str, subreddit: str) -> Dict[str, Any]:
        if not self.client:
            return {"relevant": False, "confidence": 0.0, "why": "gemini_key_missing", "tags": []}

        prompt = f"{SYSTEM}\n\nSUBREDDIT: {subreddit}\nTITLE: {title}\nSNIPPET: {summary}\nLINK: {link}\n"

        try:
            self.limiter.wait()

            def do_call():
                return self.client.models.generate_content(model=self.model, contents=prompt)

            resp = with_backoff(do_call, max_retries=3)
            text = (getattr(resp, "text", "") or "").strip()

            obj = safe_load_json(text)
            if not obj:
                # Don't crash if model returns blank/prose/garbage
                return {"relevant": False, "confidence": 0.0, "why": "gemini_bad_or_empty_json", "tags": []}

            return normalize_result(obj)

        except Exception as e:
            msg = str(e)
            lower = msg.lower()
            if ("429" in msg) or ("resource_exhausted" in lower):
                return {"relevant": False, "confidence": 0.0, "why": "gemini_quota_429", "tags": []}
            return {"relevant": False, "confidence": 0.0, "why": f"gemini_failed:{type(e).__name__}", "tags": []}


class GroqProvider:
    def __init__(self):
        self.key = os.getenv("GROQ_API_KEY", "").strip()
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()
        rpm = int(os.getenv("GROQ_RPM", "60"))
        self.limiter = RateLimiter(rpm)
        self.client = Groq(api_key=self.key) if self.key else None

    def available(self) -> bool:
        return bool(self.client)

    def judge(self, title: str, summary: str, link: str, subreddit: str) -> Dict[str, Any]:
        if not self.client:
            return {"relevant": False, "confidence": 0.0, "why": "groq_key_missing", "tags": []}

        prompt = f"{SYSTEM}\n\nSUBREDDIT: {subreddit}\nTITLE: {title}\nSNIPPET: {summary}\nLINK: {link}\n"

        try:
            self.limiter.wait()

            def do_call():
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0,
                )

            chat = with_backoff(do_call, max_retries=3)
            text = (chat.choices[0].message.content or "").strip()

            obj = safe_load_json(text)
            if not obj:
                return {"relevant": False, "confidence": 0.0, "why": "groq_bad_or_empty_json", "tags": []}

            return normalize_result(obj)

        except Exception as e:
            return {"relevant": False, "confidence": 0.0, "why": f"groq_failed:{type(e).__name__}", "tags": []}
