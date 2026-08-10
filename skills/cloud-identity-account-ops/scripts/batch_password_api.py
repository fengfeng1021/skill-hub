"""Dry-run-first password updates for accounts from a validated tenant plan."""

from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from plan_accounts import PlanError, load_and_validate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path, help="Validated non-secret tenant plan JSON")
    parser.add_argument("--apply", action="store_true", help="Perform password writes")
    parser.add_argument(
        "--shared-password-approved",
        action="store_true",
        help="Confirm the user explicitly approved the shared-password risk",
    )
    parser.add_argument(
        "--confirm-domain",
        help="Must exactly match primary_domain when --apply is used",
    )
    parser.add_argument(
        "--no-change-at-next-login",
        action="store_true",
        help="Do not require a password change at next login (higher risk)",
    )
    return parser.parse_args()


async def main() -> int:
    args = parse_args()
    try:
        plan, accounts = load_and_validate(args.plan)
    except PlanError as exc:
        print(f"PLAN INVALID: {exc}", file=sys.stderr)
        return 2

    domain = plan["primary_domain"]
    users = [row["primary_email"] for row in accounts]
    print(f"Targets ({len(users)}): {users[0]} .. {users[-1]}")
    print(f"Pilot: {plan['pilot']}")

    if not args.apply:
        print("Dry run only. No passwords or accounts were changed.")
        return 0
    if not args.shared_password_approved:
        print("Refusing write: --shared-password-approved is required.", file=sys.stderr)
        return 2
    if args.confirm_domain != domain:
        print("Refusing write: --confirm-domain must exactly match the plan.", file=sys.stderr)
        return 2

    token = os.environ.get("GOOGLE_DIRECTORY_ACCESS_TOKEN")
    if not token:
        print(
            "GOOGLE_DIRECTORY_ACCESS_TOKEN is not set. Use a short-lived token with "
            "admin.directory.user scope; never put it in the command line.",
            file=sys.stderr,
        )
        return 2

    password = getpass.getpass("Shared initial password: ")
    confirmation = getpass.getpass("Confirm shared initial password: ")
    if not password or password != confirmation:
        print("Password confirmation failed.", file=sys.stderr)
        return 2

    change_at_next_login = not args.no_change_at_next_login
    success = 0
    failed: list[str] = []
    for email in users:
        url = (
            "https://admin.googleapis.com/admin/directory/v1/users/"
            + urllib.parse.quote(email, safe="")
        )
        body = json.dumps(
            {
                "password": password,
                "changePasswordAtNextLogin": change_at_next_login,
            }
        ).encode("utf-8")
        request = urllib.request.Request(url, data=body, method="PATCH")
        request.add_header("Authorization", f"Bearer {token}")
        request.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status == 200:
                    success += 1
                    print(f"OK   {email}")
                else:
                    failed.append(email)
                    print(f"FAIL {email}: HTTP {response.status}")
        except urllib.error.HTTPError as exc:
            failed.append(email)
            print(f"FAIL {email}: HTTP {exc.code}")
        except Exception as exc:
            failed.append(email)
            print(f"FAIL {email}: {type(exc).__name__}")
        await asyncio.sleep(0.3)

    password = None
    confirmation = None
    print(f"Completed: {success}/{len(users)} succeeded")
    if failed:
        print("Failed accounts:", ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
