"""Append-only audit log. Every proposal, approval, refusal and result is recorded."""
import getpass
import json
from datetime import datetime, timezone
from pathlib import Path

LOG_FILE = Path("audit") / "audit.jsonl"


def record(event, **details):
    LOG_FILE.parent.mkdir(exist_ok=True)
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "user": getpass.getuser(),
        **details,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, default=str) + "\n")
    return entry