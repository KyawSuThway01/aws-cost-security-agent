"""Tests for secret redaction. All keys below are fake examples."""
from agent.redact import REDACTED, redact


def test_aws_access_key_id_is_hidden():
    text = "found key AKIAABCDEFGHIJKLMNOP in a tag"
    result = redact(text)
    assert "AKIAABCDEFGHIJKLMNOP" not in result
    assert REDACTED in result


def test_secret_value_after_name_is_hidden():
    result = redact('{"password": "hunter2-not-real"}')
    assert "hunter2-not-real" not in result
    assert "password" in result


def test_private_key_block_is_hidden():
    text = "-----BEGIN RSA PRIVATE KEY-----\nabc123\n-----END RSA PRIVATE KEY-----"
    result = redact(text)
    assert "abc123" not in result


def test_normal_text_is_unchanged():
    text = '[{"bucket": "test-bucket", "risk": "HIGH"}]'
    assert redact(text) == text