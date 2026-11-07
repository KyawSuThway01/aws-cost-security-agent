from datetime import datetime, timezone

from tests.fakes import FakePaginator
from tools.ec2_scanner import find_idle_ec2


class FakeEC2:
    def __init__(self, instances):
        self.instances = instances

    def get_paginator(self, name):
        assert name == "describe_instances"
        return FakePaginator([{"Reservations": [{"Instances": self.instances}]}])


class FakeCloudWatch:
    def __init__(self, data):
        self.data = data  # instance id -> list of data points

    def get_metric_statistics(self, **kwargs):
        instance_id = kwargs["Dimensions"][0]["Value"]
        return {"Datapoints": self.data.get(instance_id, [])}


class FakeSession:
    def __init__(self, instances, data):
        self.clients = {
            "ec2": FakeEC2(instances),
            "cloudwatch": FakeCloudWatch(data),
        }

    def client(self, name, **kwargs):
        return self.clients[name]


def _instance(instance_id, name):
    return {
        "InstanceId": instance_id,
        "InstanceType": "t3.micro",
        "LaunchTime": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "Tags": [{"Key": "Name", "Value": name}],
    }


def _points(average, maximum, count=3):
    return [{"Average": average, "Maximum": maximum}] * count


def test_idle_server_is_found():
    session = FakeSession([_instance("i-idle", "idle")], {"i-idle": _points(1.0, 2.0)})
    findings = find_idle_ec2(session)
    assert len(findings) == 1
    assert findings[0]["instance_id"] == "i-idle"
    assert findings[0]["name"] == "idle"


def test_server_with_cpu_spike_is_not_idle():
    session = FakeSession([_instance("i-spiky", "spiky")], {"i-spiky": _points(1.0, 80.0)})
    assert find_idle_ec2(session) == []


def test_busy_server_is_not_idle():
    session = FakeSession([_instance("i-busy", "busy")], {"i-busy": _points(50.0, 60.0)})
    assert find_idle_ec2(session) == []


def test_server_without_data_is_skipped_not_guessed():
    session = FakeSession([_instance("i-new", "new")], {})
    assert find_idle_ec2(session) == []