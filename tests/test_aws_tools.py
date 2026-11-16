"""Check that every agent tool hides secrets. Real AWS is never called.

The key below is a fake example.
"""
import pytest

from agent import aws_tools

FAKE_KEY = "AKIAABCDEFGHIJKLMNOP"
LEAKY = [{"note": f"tag value {FAKE_KEY}"}]


@pytest.mark.parametrize(
    "tool_name, scanner_name",
    [
        ("find_public_s3", "_find_public_s3"),
        ("find_open_security_groups", "_find_open_security_groups"),
        ("find_idle_ec2", "_find_idle_ec2"),
        ("get_cost_summary", "_get_cost_summary"),
    ],
)
def test_tool_output_hides_secrets(monkeypatch, tool_name, scanner_name):
    monkeypatch.setattr(aws_tools, scanner_name, lambda *a, **k: LEAKY)
    result = getattr(aws_tools, tool_name)()
    assert FAKE_KEY not in result
    assert "[REDACTED]" in result