#!/usr/bin/env python3
"""Validate SKILL.md against the Agent Skills spec (https://agentskills.io/specification).

Checks: frontmatter keys, name format, description length, metadata is a string map,
body under 500 lines, and that referenced in-repo files exist. Exit 1 on any error.
Requires PyYAML.
"""

import re
import sys
from pathlib import Path

import yaml

ALLOWED = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def main(root: Path) -> int:
    errors: list[str] = []
    skill = root / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        print("ERROR: no YAML frontmatter")
        return 1
    fm = yaml.safe_load(m.group(1))
    body = m.group(2)
    if not isinstance(fm, dict):
        print("ERROR: frontmatter is not a mapping")
        return 1

    extra = sorted(set(fm) - ALLOWED)
    if extra:
        errors.append(
            f"unexpected frontmatter key(s): {', '.join(extra)}; allowed: {sorted(ALLOWED)}"
        )
    name = fm.get("name", "")
    if not (isinstance(name, str) and 1 <= len(name) <= 64 and NAME_RE.match(name)):
        errors.append(
            f"name {name!r} must be 1-64 chars, lowercase a-z, 0-9 and single hyphens"
        )
    desc = fm.get("description", "")
    if not (isinstance(desc, str) and 1 <= len(desc) <= 1024):
        errors.append(
            f"description must be 1-1024 chars (got {len(desc) if isinstance(desc, str) else 'non-string'})"
        )
    meta = fm.get("metadata", {})
    if meta is not None and not (
        isinstance(meta, dict)
        and all(isinstance(k, str) and isinstance(v, str) for k, v in meta.items())
    ):
        errors.append("metadata must be a map of string -> string")

    lines = body.count("\n") + 1
    if lines > 500:
        errors.append(f"SKILL.md body is {lines} lines; keep it under 500")

    for ref in sorted(
        set(re.findall(r"`((?:references|demo|evals|docs)/[^`\s]+)`", body))
    ):
        if not (root / ref).exists():
            errors.append(f"referenced file missing: {ref}")

    for e in errors:
        print("ERROR:", e)
    if not errors:
        print(
            f"OK: SKILL.md valid (name={name}, description {len(desc)} chars, body {lines} lines)"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(
        main(
            Path(sys.argv[1])
            if len(sys.argv) > 1
            else Path(__file__).resolve().parent.parent
        )
    )
