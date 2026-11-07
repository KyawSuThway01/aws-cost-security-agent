"""Read-only S3 scanner: finds buckets that may be open to the public.

This module only READS data. It never changes any bucket.
"""
import json

import boto3
from botocore.exceptions import ClientError

PUBLIC_GROUPS = {
    "http://acs.amazonaws.com/groups/global/AllUsers": "everyone on the internet",
    "http://acs.amazonaws.com/groups/global/AuthenticatedUsers": "any AWS account holder",
}


def _bucket_region(s3, name):
    """Buckets live in one region. Find it so we call the right endpoint."""
    location = s3.get_bucket_location(Bucket=name)["LocationConstraint"]
    if location is None:
        return "us-east-1"
    if location == "EU":
        return "eu-west-1"
    return location


def _check_bucket(session, s3, name):
    result = {"bucket": name, "status": "not_public", "reasons": []}
    try:
        client = session.client("s3", region_name=_bucket_region(s3, name))

        # 1. Does the bucket policy make it public?
        try:
            policy = client.get_bucket_policy_status(Bucket=name)
            if policy["PolicyStatus"]["IsPublic"]:
                result["reasons"].append("Bucket policy allows public access")
        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchBucketPolicy":
                raise

        # 2. Does the ACL give access to everyone?
        acl = client.get_bucket_acl(Bucket=name)
        for grant in acl["Grants"]:
            uri = grant["Grantee"].get("URI")
            if uri in PUBLIC_GROUPS:
                result["reasons"].append(
                    f"ACL gives {grant['Permission']} to {PUBLIC_GROUPS[uri]}"
                )

        # 3. Is "Block Public Access" fully on? If yes, the bucket is protected.
        try:
            config = client.get_public_access_block(Bucket=name)
            fully_blocked = all(config["PublicAccessBlockConfiguration"].values())
        except ClientError as e:
            if e.response["Error"]["Code"] != "NoSuchPublicAccessBlockConfiguration":
                raise
            fully_blocked = False
        result["block_public_access_fully_on"] = fully_blocked

        if result["reasons"] and not fully_blocked:
            result["status"] = "public"
            result["risk"] = "HIGH"

    except ClientError as e:
        result["status"] = "unknown"
        result["reasons"].append(f"Could not check: {e.response['Error']['Code']}")
    return result


def find_public_s3(session=None):
    """Return buckets that are public (or could not be checked)."""
    session = session or boto3.Session()
    s3 = session.client("s3")
    buckets = s3.list_buckets()["Buckets"]
    results = [_check_bucket(session, s3, b["Name"]) for b in buckets]
    return [r for r in results if r["status"] != "not_public"]


if __name__ == "__main__":
    print(json.dumps(find_public_s3(), indent=2))