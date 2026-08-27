"""
Audit trail and change history tracker for all tweaks executed by INFINITY Tweaker.
"""
import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any

HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "change_history.json")

def record_change(feature: str, setting: str, prev_val: Any, new_val: Any, result: str, details: str = ""):
    """Record an optimization action into local persistent change history."""
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "feature": feature,
        "setting": setting,
        "previous_value": str(prev_val),
        "new_value": str(new_val),
        "result": result,  # SUCCESS, FAILED, PARTIAL SUCCESS, NOT SUPPORTED
        "details": details
    }
    history = get_change_history()
    history.insert(0, entry)
    # Keep last 200 entries
    history = history[:200]
    
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2)
    except Exception:
        pass

def get_change_history() -> List[Dict[str, Any]]:
    if not os.path.exists(HISTORY_FILE):
        return []
    try:
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []
