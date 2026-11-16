"""Hide secrets in text before the agent sees it or a report shows it.

This is a safety net in code. We do not only trust the model to stay quiet.
It is a simple pattern match, so it can miss unusual secrets.
"""
import re

REDACTED = "[REDACTED]"

PATTERNS = [
    # AWS access key IDs, for example AKIA + 16 letters or digits
    re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
    # Values after names like aws_secret_access_key, secret, password, token
    re.compile(
        r"""(?ix)
        (?P<name>aws_secret_access_key|secret[_-]?key|password|token)
        (?P<sep>["']?\s*[:=]\s*["']?)
        (?P<value>[^\s"',}]+)
        """
    ),
    # Private key blocks
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        re.DOTALL,
    ),
]


def redact(text):
    """Return the text with likely secrets replaced by [REDACTED]."""
    text = PATTERNS[0].sub(REDACTED, text)
    text = PATTERNS[1].sub(
        lambda m: f"{m.group('name')}{m.group('sep')}{REDACTED}", text
    )
    text = PATTERNS[2].sub(REDACTED, text)
    return text