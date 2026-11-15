import fixer.s3_fix as s3_fix
from fixer.s3_fix import fix_public_bucket


class FakeS3:
    def __init__(self):
        self.calls = []

    def put_public_access_block(self, **kwargs):
        self.calls.append(kwargs)


class FakeSession:
    def __init__(self):
        self.s3 = FakeS3()

    def client(self, name, **kwargs):
        return self.s3


def _setup(monkeypatch):
    monkeypatch.setattr(s3_fix, "record", lambda *args, **kwargs: None)
    monkeypatch.setattr(s3_fix, "find_public_s3", lambda session: [{"bucket": "bad-bucket"}])
    return FakeSession()


def test_dry_run_changes_nothing(monkeypatch):
    session = _setup(monkeypatch)
    result = fix_public_bucket("bad-bucket", apply=False, session=session)
    assert "Nothing was changed" in result
    assert session.s3.calls == []


def test_bucket_not_flagged_is_refused(monkeypatch):
    session = _setup(monkeypatch)
    result = fix_public_bucket("other-bucket", apply=True, session=session, ask=lambda _: "other-bucket")
    assert result.startswith("refused")
    assert session.s3.calls == []


def test_wrong_confirmation_is_rejected(monkeypatch):
    session = _setup(monkeypatch)
    result = fix_public_bucket("bad-bucket", apply=True, session=session, ask=lambda _: "yes")
    assert result.startswith("rejected")
    assert session.s3.calls == []


def test_correct_confirmation_applies_one_change(monkeypatch):
    session = _setup(monkeypatch)
    result = fix_public_bucket("bad-bucket", apply=True, session=session, ask=lambda _: "bad-bucket")
    assert result.startswith("applied")
    assert len(session.s3.calls) == 1
    assert session.s3.calls[0]["Bucket"] == "bad-bucket"