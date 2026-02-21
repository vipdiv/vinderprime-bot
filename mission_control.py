import requests
from typing import List, Dict
from config import MISSION_CONTROL_BASE_URL

def push_tasks(tasks: List[Dict[str, str]]) -> bool:
    url = f"{MISSION_CONTROL_BASE_URL}/api/tasks/bulk"
    try:
        r = requests.post(url, json={"tasks": tasks}, timeout=10)
        return r.status_code in (200, 201)
    except Exception:
        return False
