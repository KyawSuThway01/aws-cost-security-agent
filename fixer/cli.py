import argparse

from fixer.s3_fix import fix_public_bucket


def main():
    parser = argparse.ArgumentParser(description="Human-approved fixer")
    parser.add_argument("bucket", help="name of the public bucket to protect")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="really make the change (you will be asked to confirm)",
    )
    args = parser.parse_args()
    print(fix_public_bucket(args.bucket, apply=args.apply))


if __name__ == "__main__":
    main()