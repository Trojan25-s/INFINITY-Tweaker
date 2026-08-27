"""
Backup & Restore Manager: Creates reversible snapshots prior to system tweaks.
"""
import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List
from Restore.change_history import record_change
from Core.Logging.logger import get_logger

logger = get_logger()

BACKUPS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Snapshots")
os.makedirs(BACKUPS_DIR, exist_ok=True)

def create_backup_snapshot(name: str, state_data: Dict[str, Any]) -> str:
    """Create a new named configuration restore point."""
    snapshot_id = f"SNAP-{uuid.uuid4().hex[:8].upper()}"
    filepath = os.path.join(BACKUPS_DIR, f"{snapshot_id}.json")
    
    payload = {
        "id": snapshot_id,
        "name": name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "state_data": state_data
    }
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(payload, f, indent=2)
        logger.info(f"Created system snapshot {snapshot_id}: {name}")
        return snapshot_id
    except Exception as e:
        logger.error(f"Failed to create backup snapshot: {e}")
        return ""

def list_backup_snapshots() -> List[Dict[str, Any]]:
    """List all available restore points."""
    snapshots = []
    for f in os.listdir(BACKUPS_DIR):
        if f.endswith('.json'):
            path = os.path.join(BACKUPS_DIR, f)
            try:
                with open(path, 'r', encoding='utf-8') as handle:
                    data = json.load(handle)
                    snapshots.append({
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "created_at": data.get("created_at"),
                        "item_count": len(data.get("state_data", {}))
                    })
            except Exception:
                continue
    snapshots.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return snapshots

def get_snapshot(snapshot_id: str) -> Dict[str, Any]:
    path = os.path.join(BACKUPS_DIR, f"{snapshot_id}.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}
