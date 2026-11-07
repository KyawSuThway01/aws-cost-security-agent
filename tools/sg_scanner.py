"""Read-only security group scanner: finds ports open to the whole internet.

This module only READS data. It never changes any security group.
"""
import json

import boto3

SENSITIVE_PORTS = {
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    1433: "SQL Server",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    6379: "Redis",
    9200: "Elasticsearch",
    27017: "MongoDB",
}
WEB_PORTS = {80, 443}
RISK_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def _open_cidrs(rule):
    """Return the 'whole internet' ranges used by this rule (IPv4 and IPv6)."""
    cidrs = [r["CidrIp"] for r in rule.get("IpRanges", []) if r["CidrIp"] == "0.0.0.0/0"]
    cidrs += [r["CidrIpv6"] for r in rule.get("Ipv6Ranges", []) if r["CidrIpv6"] == "::/0"]
    return cidrs


def _rate_rule(rule):
    """Return (risk, description) for one inbound rule."""
    protocol = rule["IpProtocol"]
    if protocol == "-1":
        return "HIGH", "all protocols and all ports"

    first = rule.get("FromPort", -1)
    last = rule.get("ToPort", -1)
    label = f"{protocol} {first}" if first == last else f"{protocol} {first}-{last}"

    exposed = [name for port, name in SENSITIVE_PORTS.items() if first <= port <= last]
    if exposed:
        return "HIGH", f"{label} ({', '.join(exposed)})"
    if first == last and first in WEB_PORTS:
        return "LOW", f"{label} (web traffic, usually intended)"
    return "MEDIUM", label


def find_open_security_groups(session=None):
    """Return inbound rules that allow traffic from 0.0.0.0/0 or ::/0."""
    session = session or boto3.Session()
    ec2 = session.client("ec2")
    findings = []

    for page in ec2.get_paginator("describe_security_groups").paginate():
        for group in page["SecurityGroups"]:
            for rule in group.get("IpPermissions", []):
                cidrs = _open_cidrs(rule)
                if not cidrs:
                    continue
                risk, description = _rate_rule(rule)
                findings.append(
                    {
                        "security_group_id": group["GroupId"],
                        "name": group["GroupName"],
                        "vpc_id": group.get("VpcId"),
                        "rule": description,
                        "open_to": cidrs,
                        "risk": risk,
                    }
                )

    return sorted(findings, key=lambda f: RISK_ORDER[f["risk"]])


if __name__ == "__main__":
    print(json.dumps(find_open_security_groups(), indent=2))