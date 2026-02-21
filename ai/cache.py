import json
import os
import time
from typing import Any, Dict

CACHE_PATH = os.path.join(os.path.dirname(__file__), "ai_cache.json")

def load_cache() -> Dict[str, Any]:
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_cache(cache: Dict[str, Any]) -> None:
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)

def cache_get(cache: Dict[str, Any], key: str):
    item = cache.get(key)
    if not item:
        return None
    return item.get("value")

def cache_set(cache: Dict[str, Any], key: str, value: Any, provider: str):
    cache[key] = {
        "value": value,
        "provider": provider,
        "ts": int(time.time()),
    }
