"""Wrap the read-only scanners as tools the agent can call.

The agent gets ONLY these four read tools. It has no tool that can
change, stop, or delete anything.
"""
import json

from strands import tool

from tools.cost_scanner import get_cost_summary as _get_cost_summary
from tools.ec2_scanner import find_idle_ec2 as _find_idle_ec2
from tools.s3_scanner import find_public_s3 as _find_public_s3
from tools.sg_scanner import find_open_security_groups as _find_open_security_groups


@tool
def find_public_s3() -> str:
    """Find S3 buckets that are open to the public. Read-only.

    Returns a JSON list. An empty list means no public buckets were found.
    """
    return json.dumps(_find_public_s3(), default=str)


@tool
def find_open_security_groups() -> str:
    """Find security group rules that allow traffic from the whole internet
    (0.0.0.0/0 or ::/0). Read-only. Each finding has a risk of HIGH, MEDIUM or LOW.

    Returns a JSON list. An empty list means no open rules were found.
    """
    return json.dumps(_find_open_security_groups(), default=str)


@tool
def find_idle_ec2() -> str:
    """Find running EC2 servers whose CPU stayed very low over the last 7 days.
    Read-only. Servers with CPU spikes or without enough data are not listed.

    Returns a JSON list. An empty list means no idle servers were found.
    """
    return json.dumps(_find_idle_ec2(), default=str)


@tool
def get_cost_summary(period: str = "month_to_date") -> str:
    """Read AWS spending from Cost Explorer. Read-only. Each call costs about $0.01,
    so call it at most once.

    Args:
        period: "month_to_date" or "last_month".

    Returns a JSON object with total cost and the most expensive services.
    """
    return json.dumps(_get_cost_summary(period=period), default=str)


ALL_TOOLS = [find_public_s3, find_open_security_groups, find_idle_ec2, get_cost_summary]