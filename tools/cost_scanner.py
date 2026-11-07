"""Read-only cost reader: summarizes AWS spend from Cost Explorer.

This module only READS data. It never changes anything.
Note: each Cost Explorer API call costs about $0.01.
"""
import json
from datetime import datetime, timedelta, timezone

import boto3


def _period(period):
    """Return (start, end) dates. 'end' is exclusive, as Cost Explorer expects."""
    today = datetime.now(timezone.utc).date()
    first_of_this_month = today.replace(day=1)
    if period == "last_month":
        start = (first_of_this_month - timedelta(days=1)).replace(day=1)
        return start, first_of_this_month
    if period == "month_to_date":
        return first_of_this_month, today + timedelta(days=1)
    raise ValueError("period must be 'last_month' or 'month_to_date'")


def get_cost_summary(session=None, period="last_month", top_n=10):
    """Return total cost and the most expensive services for a period."""
    session = session or boto3.Session()
    # Cost Explorer only has one endpoint, in us-east-1.
    ce = session.client("ce", region_name="us-east-1")
    start, end = _period(period)

    response = ce.get_cost_and_usage(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        # Show real usage cost, not cost after credits are applied.
        Filter={
            "Not": {
                "Dimensions": {"Key": "RECORD_TYPE", "Values": ["Credit", "Refund"]}
            }
        },
    )

    totals = {}
    for result in response["ResultsByTime"]:
        for group in result["Groups"]:
            service = group["Keys"][0]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            totals[service] = totals.get(service, 0.0) + amount

    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    return {
        "period": period,
        "start": start.isoformat(),
        "end_exclusive": end.isoformat(),
        "currency": "USD",
        "total_cost": round(sum(totals.values()), 4),
        "top_services": [
            {"service": name, "cost": round(cost, 4)} for name, cost in ranked[:top_n]
        ],
    }


if __name__ == "__main__":
    print(json.dumps(get_cost_summary(period="month_to_date"), indent=2))