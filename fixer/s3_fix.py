"""Human-approved fix: turn ON S3 Block Public Access for one bucket.

This is the ONLY place that can change anything. The AI agent never calls it.
"""
import boto3
from botocore.exceptions import ClientError

from fixer.audit import record
from tools.s3_scanner import find_public_s3

BLOCK_ALL = {
    "BlockPublicAcls": True,
    "IgnorePublicAcls": True,
    "BlockPublicPolicy": True,
    "RestrictPublicBuckets": True,
}


def fix_public_bucket(bucket, apply=False, session=None, ask=input):
    session = session or boto3.Session()
    record("proposed", action="s3_block_public_access", bucket=bucket, apply=apply)

    # 1. Check live. Never act on an old report.
    flagged = {finding["bucket"] for finding in find_public_s3(session)}
    if bucket not in flagged:
        record("refused", bucket=bucket, reason="not currently flagged as public")
        return "refused: this bucket is not currently flagged as public."

    # 2. Dry-run is the default. Nothing changes.
    if not apply:
        record("dry_run", bucket=bucket)
        return (
            "dry run: would turn on all four S3 Block Public Access settings "
            f"for '{bucket}'. Nothing was changed."
        )

    # 3. Human approval: type the exact bucket name.
    answer = ask(
        f"Turn ON Block Public Access for '{bucket}'?\n"
        "Type the bucket name to approve, or anything else to cancel: "
    ).strip()
    if answer != bucket:
        record("rejected", bucket=bucket)
        return "rejected by human. Nothing was changed."
    record("approved", bucket=bucket)

    # 4. One small change.
    try:
        session.client("s3").put_public_access_block(
            Bucket=bucket, PublicAccessBlockConfiguration=BLOCK_ALL
        )
    except ClientError as e:
        record("failed", bucket=bucket, error=e.response["Error"]["Code"])
        return f"failed: {e.response['Error']['Code']}"

    record("applied", bucket=bucket)
    return f"applied: Block Public Access is now ON for '{bucket}'."