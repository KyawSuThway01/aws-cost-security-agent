from tests.fakes import FakePaginator
from tools.sg_scanner import _rate_rule, find_open_security_groups


def test_ssh_is_high():
    risk, description = _rate_rule({"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22})
    assert risk == "HIGH"
    assert "SSH" in description


def test_http_is_low():
    risk, _ = _rate_rule({"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80})
    assert risk == "LOW"


def test_all_traffic_is_high():
    risk, _ = _rate_rule({"IpProtocol": "-1"})
    assert risk == "HIGH"


def test_wide_port_range_is_high():
    risk, _ = _rate_rule({"IpProtocol": "tcp", "FromPort": 0, "ToPort": 65535})
    assert risk == "HIGH"


def test_unknown_port_is_medium():
    risk, _ = _rate_rule({"IpProtocol": "tcp", "FromPort": 8080, "ToPort": 8080})
    assert risk == "MEDIUM"


class FakeEC2:
    def __init__(self, groups):
        self.groups = groups

    def get_paginator(self, name):
        assert name == "describe_security_groups"
        return FakePaginator([{"SecurityGroups": self.groups}])


class FakeSession:
    def __init__(self, groups):
        self.ec2 = FakeEC2(groups)

    def client(self, name, **kwargs):
        return self.ec2


def _group(group_id, port, cidr="0.0.0.0/0", ipv6=None):
    return {
        "GroupId": group_id,
        "GroupName": f"group-{group_id}",
        "VpcId": "vpc-1",
        "IpPermissions": [
            {
                "IpProtocol": "tcp",
                "FromPort": port,
                "ToPort": port,
                "IpRanges": [{"CidrIp": cidr}],
                "Ipv6Ranges": [{"CidrIpv6": ipv6}] if ipv6 else [],
            }
        ],
    }


def test_finds_open_rules_and_sorts_high_first():
    groups = [_group("sg-web", 80), _group("sg-ssh", 22)]
    findings = find_open_security_groups(FakeSession(groups))
    assert [f["security_group_id"] for f in findings] == ["sg-ssh", "sg-web"]
    assert findings[0]["risk"] == "HIGH"


def test_private_ranges_are_ignored():
    groups = [_group("sg-private", 22, cidr="10.0.0.0/8")]
    assert find_open_security_groups(FakeSession(groups)) == []


def test_ipv6_open_to_world_is_found():
    groups = [_group("sg-v6", 22, cidr="10.0.0.0/8", ipv6="::/0")]
    findings = find_open_security_groups(FakeSession(groups))
    assert len(findings) == 1
    assert findings[0]["open_to"] == ["::/0"]