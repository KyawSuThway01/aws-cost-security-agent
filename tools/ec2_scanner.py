"""Read-only EC2 scanner: finds running servers with very low CPU.

This module only READS data. It never stops or changes any instance.
"""
import json
from datetime import datetime, timedelta, timezone

import boto3


def _name_tag(instance):
    for tag in instance.get("Tags", []):
        if tag["Key"] == "Name":
            return tag["Value"]
    return None


def find_idle_ec2(session=None, cpu_threshold=5.0, spike_limit=20.0, lookback_hours=168):
    """Return running instances whose CPU stayed very low.

    cpu_threshold: average CPU % below this counts as idle.
    spike_limit:   if CPU ever went above this %, the server is NOT idle.
    lookback_hours: how far back to look (168 hours = 7 days).
    """
    session = session or boto3.Session()
    ec2 = session.client("ec2")
    cloudwatch = session.client("cloudwatch")

    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=lookback_hours)
    # Short windows use 5-minute data points, long windows use 1-hour points.
    period = 300 if lookback_hours <= 24 else 3600

    findings = []
    paginator = ec2.get_paginator("describe_instances")
    filters = [{"Name": "instance-state-name", "Values": ["running"]}]

    for page in paginator.paginate(Filters=filters):
        for reservation in page["Reservations"]:
            for instance in reservation["Instances"]:
                instance_id = instance["InstanceId"]
                stats = cloudwatch.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName="CPUUtilization",
                    Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                    StartTime=start,
                    EndTime=end,
                    Period=period,
                    Statistics=["Average", "Maximum"],
                )
                points = stats["Datapoints"]
                if not points:
                    # A brand-new instance has no data yet. Do not guess.
                    continue

                avg_cpu = sum(p["Average"] for p in points) / len(points)
                max_cpu = max(p["Maximum"] for p in points)

                if avg_cpu < cpu_threshold and max_cpu < spike_limit:
                    findings.append(
                        {
                            "instance_id": instance_id,
                            "name": _name_tag(instance),
                            "instance_type": instance["InstanceType"],
                            "launch_time": instance["LaunchTime"].isoformat(),
                            "avg_cpu_percent": round(avg_cpu, 2),
                            "max_cpu_percent": round(max_cpu, 2),
                            "data_points": len(points),
                            "lookback_hours": lookback_hours,
                            "risk": "MEDIUM",
                        }
                    )
    return findings


if __name__ == "__main__":
    print(json.dumps(find_idle_ec2(), indent=2))