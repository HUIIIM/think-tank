#!/usr/bin/env python3
"""Validate SKILL.md against the Agent Skills spec (https://agentskills.io/specification).

The spec requires `name` to equal the skill directory name, so run it on a checkout
whose directory is named after the skill (CI checks out into `think-tank`).

Checks: frontmatter keys, name format, description length, metadata is a string map,
body under 500 lines, and that referenced in-repo files exist. Exit 1 on any error.
Requires PyYAML.
"""

import json
import re
import sys
from pathlib import Path

import yaml


class _UniqueKeyLoader(yaml.SafeLoader):
    """SafeLoader that rejects duplicate mapping keys instead of keeping the last."""


def _construct_mapping(
    loader: yaml.SafeLoader, node: yaml.MappingNode
) -> dict[object, object]:
    keys = [k.value for k, _ in node.value if isinstance(k, yaml.ScalarNode)]
    dupes = sorted({str(k) for k in keys if keys.count(k) > 1})
    if dupes:
        raise yaml.constructor.ConstructorError(
            None, None, f"duplicate key(s): {', '.join(dupes)}", node.start_mark
        )
    return loader.construct_mapping(node)


_UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)

ALLOWED = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
NAME_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")


def main(root: Path) -> int:
    errors: list[str] = []
    skill = root / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not m:
        print("ERROR: no YAML frontmatter")
        return 1
    try:
        fm = yaml.load(m.group(1), Loader=_UniqueKeyLoader)
    except yaml.YAMLError as e:
        print(f"ERROR: frontmatter YAML: {e}")
        return 1
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
    if not (isinstance(name, str) and 1 <= len(name) <= 64 and NAME_RE.fullmatch(name)):
        errors.append(
            f"name {name!r} must be 1-64 chars, lowercase a-z, 0-9 and single hyphens"
        )
    if isinstance(name, str) and name != root.resolve().name:
        errors.append(
            f"name {name!r} must match the skill directory name {root.resolve().name!r}"
        )
    desc = fm.get("description", "")
    if not (isinstance(desc, str) and 1 <= len(desc) <= 1024):
        errors.append(
            f"description must be 1-1024 chars (got {len(desc) if isinstance(desc, str) else 'non-string'})"
        )
    if "compatibility" in fm and not (
        isinstance(fm["compatibility"], str) and 1 <= len(fm["compatibility"]) <= 500
    ):
        errors.append("compatibility must be a 1-500 char string")
    if "license" in fm and not isinstance(fm["license"], str):
        errors.append("license must be a string")
    if "allowed-tools" in fm and not isinstance(fm["allowed-tools"], str):
        errors.append("allowed-tools must be a space-separated string")
    meta = fm.get("metadata", {})
    if meta is not None and not (
        isinstance(meta, dict)
        and all(isinstance(k, str) and isinstance(v, str) for k, v in meta.items())
    ):
        errors.append("metadata must be a map of string -> string")

    plugin = root / ".claude-plugin" / "plugin.json"
    if plugin.exists():
        pdata = json.loads(plugin.read_text(encoding="utf-8"))
        if pdata.get("name") != name:
            errors.append(
                f".claude-plugin/plugin.json name {pdata.get('name')!r} != SKILL.md name {name!r}"
            )
        pv = pdata.get("version")
        mv = meta.get("version") if isinstance(meta, dict) else None
        if pv != mv:
            errors.append(
                f".claude-plugin/plugin.json version {pv!r} != SKILL.md metadata.version {mv!r}"
            )
    lines = body.count("\n") + 1
    if lines > 500:
        errors.append(f"SKILL.md body is {lines} lines; keep it under 500")

    for ref in sorted(
        set(
            re.findall(
                r"`((?:references|demo|evals|docs|scripts|assets)/[^`\s]+)`", body
            )
        )
    ):
        if not (root / ref).exists():
            errors.append(f"referenced file missing: {ref}")

    for err in errors:
        print("ERROR:", err)
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
