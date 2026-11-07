"""Run all read-only scanners and return one combined report.

Each scanner runs on its own. If one fails (for example, a missing
permission), the others still finish and the error is recorded.
"""
import json
from datetime import datetime, timezone

import boto3

from tools.cost_scanner import get_cost_summary
from tools.ec2_scanner import find_idle_ec2
from tools.s3_scanner import find_public_s3
from tools.sg_scanner import find_open_security_groups


def _safe(func, *args, **kwargs):
    try:
        return {"status": "ok", "data": func(*args, **kwargs)}
    except Exception as e:
        return {"status": "error", "error": f"{type(e).__name__}: {e}"}


def scan_all(session=None):
    session = session or boto3.Session()
    return {
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "region": session.region_name,
        "public_s3": _safe(find_public_s3, session),
        "open_security_groups": _safe(find_open_security_groups, session),
        "idle_ec2": _safe(find_idle_ec2, session),
        "cost_summary": _safe(get_cost_summary, session, period="month_to_date"),
    }


if __name__ == "__main__":
    print(json.dumps(scan_all(), indent=2, default=str))