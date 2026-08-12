#!/usr/bin/env python3
"""Read-only reference bridge for self-hosted Agent Skills clients."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


class BridgeError(RuntimeError):
    pass


def unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def metadata(path: Path) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise BridgeError(f"Cannot read {path}: {exc}") from exc
    match = re.match(r"^---\s*\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)", text)
    if not match:
        raise BridgeError(f"Missing YAML frontmatter: {path}")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        item = re.match(r"^(name|description):\s*(.+)$", line)
        if item:
            fields[item.group(1)] = unquote(item.group(2))
    if not fields.get("name") or not fields.get("description"):
        raise BridgeError(f"name and description are required: {path}")
    fields["body"] = text[match.end():]
    return fields


def discover(roots: list[Path]) -> dict[str, dict[str, Any]]:
    skills: dict[str, dict[str, Any]] = {}
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("SKILL.md")):
            try:
                fields = metadata(path)
            except BridgeError:
                continue
            name = fields["name"]
            if name in skills:
                continue
            skills[name] = {
                "name": name,
                "description": fields["description"],
                "directory": str(path.parent.resolve()),
                "skillFile": str(path.resolve()),
                "body": fields["body"],
            }
    return skills


def safe_resource(directory: Path, relative: str) -> Path:
    raw = relative.strip().replace("\\", "/")
    if not raw or raw.startswith("/") or ".." in Path(raw).parts:
        raise BridgeError("Resource path must stay inside the skill directory")
    target = (directory / raw).resolve()
    try:
        target.relative_to(directory.resolve())
    except ValueError as exc:
        raise BridgeError("Resource path escapes the skill directory") from exc
    if not target.is_file():
        raise BridgeError(f"Resource does not exist: {relative}")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-root", action="append", required=True, help="A directory containing skill folders")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list")
    load = commands.add_parser("load")
    load.add_argument("name")
    read = commands.add_parser("read")
    read.add_argument("name")
    read.add_argument("resource")
    args = parser.parse_args()

    try:
        skills = discover([Path(item).expanduser().resolve() for item in args.skills_root])
        if args.command == "list":
            payload = [
                {key: item[key] for key in ("name", "description", "directory")}
                for item in sorted(skills.values(), key=lambda value: value["name"])
            ]
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        item = skills.get(args.name)
        if not item:
            raise BridgeError(f"Unknown skill: {args.name}")
        if args.command == "load":
            print(json.dumps({key: item[key] for key in ("name", "description", "directory", "body")}, ensure_ascii=False, indent=2))
            return 0
        path = safe_resource(Path(item["directory"]), args.resource)
        try:
            print(path.read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            print(json.dumps({"path": str(path), "encoding": "binary", "size": path.stat().st_size}))
        return 0
    except BridgeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
