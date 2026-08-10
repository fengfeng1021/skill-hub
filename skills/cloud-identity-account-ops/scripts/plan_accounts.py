"""Validate a non-secret Cloud Identity tenant plan and emit an account manifest."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse


DOMAIN_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)
PREFIX_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,62})$")
SENSITIVE_KEY_PARTS = {
    "password",
    "passwd",
    "token",
    "secret",
    "privatekey",
    "private_key",
    "cookie",
    "certificate",
    "credential",
}
LOGIN_STRATEGIES = {"native", "permanent-sso", "temporary-sso"}
EMPLOYEE_ID_STRATEGIES = {"local-part", "none"}


class PlanError(ValueError):
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path, help="Path to a non-secret tenant plan JSON")
    parser.add_argument("--manifest", type=Path, help="Write the validated CSV manifest")
    parser.add_argument("--force", action="store_true", help="Replace an existing manifest")
    return parser.parse_args()


def reject_sensitive_keys(value, path="root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = re.sub(r"[^a-z0-9_]", "", str(key).lower())
            if any(part in normalized for part in SENSITIVE_KEY_PARTS):
                raise PlanError(f"secret-like field is forbidden: {path}.{key}")
            reject_sensitive_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_sensitive_keys(child, f"{path}[{index}]")


def require_mapping(parent: dict, key: str) -> dict:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise PlanError(f"{key} must be an object")
    return value


def require_text(parent: dict, key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value.strip():
        raise PlanError(f"{key} must be a non-empty string")
    return value.strip()


def validate_email(email: str, label: str) -> str:
    if email.count("@") != 1:
        raise PlanError(f"{label} must be an email address")
    local, domain = email.lower().split("@", 1)
    if not local or not PREFIX_RE.fullmatch(local) or not DOMAIN_RE.fullmatch(domain):
        raise PlanError(f"{label} is invalid: {email}")
    return f"{local}@{domain}"


def load_and_validate(path: Path) -> tuple[dict, list[dict]]:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PlanError(f"plan not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise PlanError(f"invalid JSON: {exc}") from exc
    if not isinstance(plan, dict):
        raise PlanError("plan root must be an object")
    reject_sensitive_keys(plan)

    if plan.get("schema_version") != 1:
        raise PlanError("schema_version must be 1")

    domain = require_text(plan, "primary_domain").lower()
    if not DOMAIN_RE.fullmatch(domain):
        raise PlanError(f"invalid primary_domain: {domain}")

    target_ou = require_text(plan, "target_ou")
    if not target_ou.startswith("/") or target_ou == "/":
        raise PlanError("target_ou must be a dedicated non-root OU path")

    pattern = require_mapping(plan, "account_pattern")
    prefix = require_text(pattern, "prefix").lower()
    if not PREFIX_RE.fullmatch(prefix):
        raise PlanError("account_pattern.prefix is not a safe email local-part prefix")
    start = pattern.get("start")
    count = pattern.get("count")
    digits = pattern.get("digits")
    if not isinstance(start, int) or start < 0:
        raise PlanError("account_pattern.start must be a non-negative integer")
    if not isinstance(count, int) or not 1 <= count <= 10000:
        raise PlanError("account_pattern.count must be between 1 and 10000")
    if not isinstance(digits, int) or not 1 <= digits <= 8:
        raise PlanError("account_pattern.digits must be between 1 and 8")
    if start + count - 1 >= 10**digits:
        raise PlanError("account range does not fit account_pattern.digits")

    profile = require_mapping(plan, "profile")
    given_prefix = require_text(profile, "given_name_prefix")
    family_name = require_text(profile, "family_name")

    employee_strategy = require_text(plan, "employee_id_strategy")
    if employee_strategy not in EMPLOYEE_ID_STRATEGIES:
        raise PlanError("employee_id_strategy must be local-part or none")

    login_strategy = require_text(plan, "login_strategy")
    if login_strategy not in LOGIN_STRATEGIES:
        raise PlanError("login_strategy must be native, permanent-sso, or temporary-sso")

    exclusions = plan.get("admin_exclusions")
    if not isinstance(exclusions, list) or len(exclusions) < 2:
        raise PlanError("admin_exclusions must contain at least two confirmed admins")
    admin_exclusions = {
        validate_email(str(email), f"admin_exclusions[{index}]")
        for index, email in enumerate(exclusions)
    }
    if len(admin_exclusions) != len(exclusions):
        raise PlanError("admin_exclusions contains duplicate addresses")

    services = plan.get("target_services")
    if not isinstance(services, list) or not services:
        raise PlanError("target_services must be a non-empty list")
    for index, service in enumerate(services):
        parsed = urlparse(str(service))
        if parsed.scheme != "https" or not parsed.netloc:
            raise PlanError(f"target_services[{index}] must be an HTTPS URL")

    accounts = []
    for number in range(start, start + count):
        suffix = f"{number:0{digits}d}"
        local = f"{prefix}{suffix}"
        email = f"{local}@{domain}"
        if email in admin_exclusions:
            raise PlanError(f"generated account overlaps admin_exclusions: {email}")
        accounts.append(
            {
                "primary_email": email,
                "local_part": local,
                "given_name": f"{given_prefix}{suffix}",
                "family_name": family_name,
                "employee_id": local if employee_strategy == "local-part" else "",
                "target_ou": target_ou,
            }
        )

    pilot = validate_email(require_text(plan, "pilot"), "pilot")
    account_emails = {row["primary_email"] for row in accounts}
    if pilot not in account_emails:
        raise PlanError("pilot must be one of the generated accounts")
    if pilot in admin_exclusions:
        raise PlanError("pilot must not be an administrator")

    normalized = dict(plan)
    normalized["primary_domain"] = domain
    normalized["target_ou"] = target_ou
    normalized["pilot"] = pilot
    normalized["admin_exclusions"] = sorted(admin_exclusions)
    normalized["login_strategy"] = login_strategy
    return normalized, accounts


def write_manifest(path: Path, accounts: list[dict], force: bool) -> None:
    if path.exists() and not force:
        raise PlanError(f"manifest already exists: {path}; use --force to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(accounts[0]))
        writer.writeheader()
        writer.writerows(accounts)


def main() -> int:
    args = parse_args()
    try:
        plan, accounts = load_and_validate(args.plan)
        if args.manifest:
            write_manifest(args.manifest, accounts, args.force)
    except PlanError as exc:
        print(f"PLAN INVALID: {exc}", file=sys.stderr)
        return 2

    print(f"PLAN VALID: {plan['primary_domain']}")
    print(f"Target OU: {plan['target_ou']}")
    print(f"Strategy: {plan['login_strategy']}")
    print(f"Accounts: {len(accounts)}")
    print(f"First: {accounts[0]['primary_email']}")
    print(f"Pilot: {plan['pilot']}")
    print(f"Last: {accounts[-1]['primary_email']}")
    print(f"Admin exclusions: {len(plan['admin_exclusions'])} verified in plan")
    if args.manifest:
        print(f"Manifest: {args.manifest.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
