import fixer.s3_fix as s3_fix
from fixer.s3_fix import fix_public_bucket


class FakeS3:
    def __init__(self):
        self.calls = []

    def put_public_access_block(self, **kwargs):
        self.calls.append(kwargs)

    def get_caller_identity(self):
        return {"Arn": "arn:aws:sts::123456789012:assumed-role/agent-fixer-s3/test"}


class FakeSession:
    def __init__(self):
        self.s3 = FakeS3()

    def client(self, name, **kwargs):
        return self.s3


def _setup(monkeypatch):
    monkeypatch.setattr(s3_fix, "record", lambda *args, **kwargs: None)
    monkeypatch.setattr(s3_fix, "find_public_s3", lambda session: [{"bucket": "bad-bucket"}])
    return FakeSession(), FakeSession()  # (read-only session, fixer session)


def test_dry_run_changes_nothing(monkeypatch):
    scan, fixer = _setup(monkeypatch)
    result = fix_public_bucket("bad-bucket", apply=False, session=scan, fixer_session=fixer)
    assert "Nothing was changed" in result
    assert fixer.s3.calls == []


def test_bucket_not_flagged_is_refused(monkeypatch):
    scan, fixer = _setup(monkeypatch)
    result = fix_public_bucket(
        "other-bucket", apply=True, session=scan, fixer_session=fixer,
        ask=lambda _: "other-bucket",
    )
    assert result.startswith("refused")
    assert fixer.s3.calls == []


def test_wrong_confirmation_is_rejected(monkeypatch):
    scan, fixer = _setup(monkeypatch)
    result = fix_public_bucket(
        "bad-bucket", apply=True, session=scan, fixer_session=fixer,
        ask=lambda _: "yes",
    )
    assert result.startswith("rejected")
    assert fixer.s3.calls == []


def test_change_is_made_by_fixer_session_not_read_only_session(monkeypatch):
    scan, fixer = _setup(monkeypatch)
    result = fix_public_bucket(
        "bad-bucket", apply=True, session=scan, fixer_session=fixer,
        ask=lambda _: "bad-bucket",
    )
    assert result.startswith("applied")
    assert len(fixer.s3.calls) == 1
    assert fixer.s3.calls[0]["Bucket"] == "bad-bucket"
    assert scan.s3.calls == []  # the read-only session never changed anything