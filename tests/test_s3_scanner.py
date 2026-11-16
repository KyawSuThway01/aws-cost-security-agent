"""Tests for the S3 scanner. A fake bucket is used, so real AWS is never called."""
from botocore.exceptions import ClientError

from tools.s3_scanner import find_public_s3

ALL_USERS = "http://acs.amazonaws.com/groups/global/AllUsers"


def _err(code, operation):
    return ClientError({"Error": {"Code": code}}, operation)


class FakeS3:
    """One fake bucket. Works as both the main client and the regional client."""

    def __init__(self, policy=None, acl_uris=(), block=None, deny=False):
        self.policy = policy        # None = no policy, True = public, False = private policy
        self.acl_uris = acl_uris    # public group URIs in the ACL
        self.block = block          # None = no config, True = all four on, False = not all on
        self.deny = deny            # True = AccessDenied on the first call

    def list_buckets(self):
        return {"Buckets": [{"Name": "test-bucket"}]}

    def get_bucket_location(self, Bucket):
        if self.deny:
            raise _err("AccessDenied", "GetBucketLocation")
        return {"LocationConstraint": "ap-southeast-2"}

    def get_bucket_policy_status(self, Bucket):
        if self.policy is None:
            raise _err("NoSuchBucketPolicy", "GetBucketPolicyStatus")
        return {"PolicyStatus": {"IsPublic": self.policy}}

    def get_bucket_acl(self, Bucket):
        grants = [
            {"Grantee": {"Type": "Group", "URI": uri}, "Permission": "READ"}
            for uri in self.acl_uris
        ]
        grants.append(
            {"Grantee": {"Type": "CanonicalUser", "ID": "owner"}, "Permission": "FULL_CONTROL"}
        )
        return {"Grants": grants}

    def get_public_access_block(self, Bucket):
        if self.block is None:
            raise _err("NoSuchPublicAccessBlockConfiguration", "GetPublicAccessBlock")
        return {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": self.block,
            }
        }


class FakeSession:
    def __init__(self, s3):
        self.s3 = s3

    def client(self, service, region_name=None):
        return self.s3


def test_public_policy_without_block_is_high():
    results = find_public_s3(FakeSession(FakeS3(policy=True)))
    assert len(results) == 1
    assert results[0]["status"] == "public"
    assert results[0]["risk"] == "HIGH"


def test_public_acl_is_found():
    results = find_public_s3(FakeSession(FakeS3(acl_uris=[ALL_USERS])))
    assert results[0]["status"] == "public"
    assert "everyone on the internet" in results[0]["reasons"][0]


def test_full_block_public_access_protects_bucket():
    results = find_public_s3(FakeSession(FakeS3(policy=True, block=True)))
    assert results == []


def test_private_bucket_is_not_reported():
    results = find_public_s3(FakeSession(FakeS3(policy=False, block=True)))
    assert results == []


def test_access_denied_is_unknown_not_guessed():
    results = find_public_s3(FakeSession(FakeS3(deny=True)))
    assert results[0]["status"] == "unknown"
    assert "AccessDenied" in results[0]["reasons"][0]