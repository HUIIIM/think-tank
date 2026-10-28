#!/usr/bin/env python3
"""Negative fixtures for scripts/validate_skill.py (SOTA VER-2).

Each case mutates a copy of this repository's SKILL.md (or plugin.json) in a temporary
directory named like the real skill directory, runs the validator, and expects exit 1 with that rule's own error message,
so every rule is tested on its own rather than through another rule.
The unmutated copy must exit 0. Exit status is non-zero if any expectation fails.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "scripts" / "validate_skill.py"
COPY = ["SKILL.md", ".claude-plugin", "references", "evals", "demo", "docs", "scripts"]

Mutation = Callable[[Path], None]
# Fixture copies live in a directory named after the skill (the spec requires name == directory),
# so the suite also runs from a clone or worktree with a different directory name.
_m = re.search(
    r"^name: *\"?([^\"\n]+)\"?$", (ROOT / "SKILL.md").read_text(encoding="utf-8"), re.M
)
SKILL_NAME = _m.group(1) if _m else ROOT.name


def sub_skill(pattern: str, repl: str) -> Mutation:
    def apply(root: Path) -> None:
        p = root / "SKILL.md"
        text, n = re.subn(
            pattern, lambda _m: repl, p.read_text(encoding="utf-8"), count=1, flags=re.M
        )
        if n != 1:
            raise RuntimeError(f"fixture pattern did not match: {pattern!r}")
        p.write_text(text, encoding="utf-8")

    return apply


def sub_plugin(old: str, new: str) -> Mutation:
    def apply(root: Path) -> None:
        p = root / ".claude-plugin" / "plugin.json"
        text = p.read_text(encoding="utf-8")
        if old not in text:
            raise RuntimeError(f"fixture text not found in plugin.json: {old!r}")
        p.write_text(text.replace(old, new, 1), encoding="utf-8")

    return apply


def body_exactly(n_lines: int) -> Mutation:
    """Pad the SKILL.md body so it has exactly n_lines lines (as the validator counts)."""

    def apply(root: Path) -> None:
        p = root / "SKILL.md"
        text = p.read_text(encoding="utf-8")
        head, body = text.split("\n---\n", 1)
        have = body.count("\n") + 1
        if have > n_lines:
            raise RuntimeError(f"body already has {have} lines")
        p.write_text(
            head + "\n---\n" + body + "x\n" * (n_lines - have), encoding="utf-8"
        )

    return apply


def plugin_without_version(root: Path) -> None:
    p = root / ".claude-plugin" / "plugin.json"
    data = json.loads(p.read_text(encoding="utf-8"))
    del data["version"]
    p.write_text(json.dumps(data), encoding="utf-8")


def strip_frontmatter(root: Path) -> None:
    p = root / "SKILL.md"
    p.write_text(p.read_text(encoding="utf-8").split("\n---\n", 1)[1], encoding="utf-8")


CASES: list[tuple[str, Mutation, str]] = [
    (
        "unknown top-level key",
        sub_skill(r"^license: MIT$", "license: MIT\nversion: x"),
        "unexpected frontmatter key",
    ),
    (
        "legacy user_invocable key",
        sub_skill(r"^license: MIT$", "license: MIT\nuser_invocable: true"),
        "unexpected frontmatter key",
    ),
    (
        "uppercase name",
        sub_skill(r"^name: think-tank$", "name: Think-Tank"),
        "must be 1-64 chars",
    ),
    (
        "name with trailing newline",
        sub_skill(r"^name: think-tank$", 'name: "think-tank\\n"'),
        "must be 1-64 chars",
    ),
    (
        "name differs from directory",
        sub_skill(r"^name: think-tank$", "name: think-tanks"),
        "must match the skill directory name",
    ),
    (
        "duplicate top-level key",
        sub_skill(r"^license: MIT$", "license: MIT\nlicense: Apache-2.0"),
        "duplicate key",
    ),
    (
        "non-string metadata value",
        sub_skill(r'^  version: "?([^"\n]+)"?$', r"  version: 1.5"),
        "metadata must be a map of string",
    ),
    (
        "license not a string",
        sub_skill(r"^license: MIT$", "license: [MIT]"),
        "license must be a string",
    ),
    (
        "compatibility over 500 chars",
        sub_skill(r"^license: MIT$", "license: MIT\ncompatibility: " + "x" * 501),
        "compatibility must be",
    ),
    (
        "allowed-tools not a string",
        sub_skill(r"^license: MIT$", "license: MIT\nallowed-tools: [Read]"),
        "allowed-tools must be",
    ),
    (
        "description of 1025 chars",
        sub_skill(r'^description: ".*"$', 'description: "' + "x" * 1025 + '"'),
        "description must be 1-1024",
    ),
    (
        "missing scripts/ reference",
        sub_skill(r"^## 输出契约$", "## 输出契约\n\n见 `scripts/missing.py`。"),
        "referenced file missing: scripts/missing.py",
    ),
    (
        "missing assets/ reference",
        sub_skill(r"^## 输出契约$", "## 输出契约\n\n见 `assets/missing.png`。"),
        "referenced file missing: assets/missing.png",
    ),
    (
        "compatibility not a string",
        sub_skill(r"^license: MIT$", "license: MIT\ncompatibility: [claude-code]"),
        "compatibility must be",
    ),
    ("body of exactly 501 lines", body_exactly(501), "SKILL.md body is 501 lines"),
    (
        "name with leading hyphen",
        sub_skill(r"^name: think-tank$", "name: -think-tank"),
        "must be 1-64 chars",
    ),
    (
        "name with trailing hyphen",
        sub_skill(r"^name: think-tank$", "name: think-tank-"),
        "must be 1-64 chars",
    ),
    (
        "name with double hyphen",
        sub_skill(r"^name: think-tank$", "name: think--tank"),
        "must be 1-64 chars",
    ),
    (
        "missing description key",
        sub_skill(r'^description: ".*"\n', ""),
        "description must be 1-1024",
    ),
    (
        "plugin.json name drift",
        sub_plugin('"name": "think-tank"', '"name": "think-tank-x"'),
        "plugin.json name",
    ),
    (
        "name of 65 chars",
        sub_skill(r"^name: think-tank$", "name: " + "a" * 65),
        "must be 1-64 chars",
    ),
    (
        "empty description",
        sub_skill(r'^description: ".*"$', 'description: ""'),
        "description must be 1-1024",
    ),
    (
        "empty compatibility",
        sub_skill(r"^license: MIT$", 'license: MIT\ncompatibility: ""'),
        "compatibility must be",
    ),
    (
        "nested duplicate key",
        sub_skill(r'^  version: "?([^"\n]+)"?$', '  version: "1"\n  version: "2"'),
        "duplicate key",
    ),
    (
        "missing references/ reference",
        sub_skill(r"^## 输出契约$", "## 输出契约\n\n见 `references/missing.md`。"),
        "referenced file missing: references/missing.md",
    ),
    ("plugin.json without version", plugin_without_version, "plugin.json version"),
    ("no frontmatter", strip_frontmatter, "no YAML frontmatter"),
    (
        "plugin.json version drift",
        sub_plugin('"version": "', '"version": "9.9.9-'),
        "plugin.json version",
    ),
]


def unquote_version(root: Path) -> None:
    """`version: 1.0.4` (unquoted) is still a YAML string, so it must validate.

    A no-op when SKILL.md already has it unquoted, so the suite keeps working after that edit.
    """
    p = root / "SKILL.md"
    text = p.read_text(encoding="utf-8")
    if re.search(r"""^  version: [^"'\n]+$""", text, flags=re.M):
        return
    text, n = re.subn(r'^(  version: )"([^"\n]+)"$', r"\1\2", text, count=1, flags=re.M)
    if n != 1:
        raise RuntimeError("metadata.version not found")
    p.write_text(text, encoding="utf-8")


def assert_unquoted(root: Path) -> None:
    line = re.search(
        r"^  version: (.+)$", (root / "SKILL.md").read_text(encoding="utf-8"), re.M
    )
    if not line or line.group(1)[0] in "\"'":
        raise RuntimeError("unquote_version left metadata.version quoted")


# Edge values the spec allows: these must still validate (exit 0).
PASSING: list[tuple[str, Mutation]] = [
    (
        "description of exactly 1024 chars",
        sub_skill(r'^description: ".*"$', 'description: "' + "x" * 1024 + '"'),
    ),
    ("body of exactly 500 lines", body_exactly(500)),
    ("unquoted metadata.version", unquote_version),
]


def run(root: Path) -> tuple[int, str]:
    r = subprocess.run(
        [sys.executable, str(VALIDATOR), str(root)],
        capture_output=True,
        text=True,
        check=False,
    )
    return r.returncode, r.stdout + r.stderr


def fresh(base: Path) -> Path:
    root = base / SKILL_NAME
    if root.exists():
        shutil.rmtree(root)
    root.mkdir()
    for item in COPY:
        src = ROOT / item
        if src.is_dir():
            shutil.copytree(src, root / item)
        elif src.exists():
            shutil.copy2(src, root / item)
    return root


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        rc, _ = run(fresh(base))
        print(f"{'ok ' if rc == 0 else 'BAD'} unmutated copy -> {rc} (want 0)")
        failures += rc != 0
        for label, mutate, expected in CASES:
            root = fresh(base)
            mutate(root)
            rc, out = run(root)
            good = rc == 1 and expected in out
            print(
                f"{'ok ' if good else 'BAD'} {label} -> {rc}, want 1 with {expected!r}"
            )
            failures += not good
        for label, mutate in PASSING:
            root = fresh(base)
            mutate(root)
            if mutate is unquote_version:
                assert_unquoted(root)
            rc, _ = run(root)
            print(f"{'ok ' if rc == 0 else 'BAD'} {label} -> {rc} (want 0)")
            failures += rc != 0
    total = len(CASES) + len(PASSING) + 1
    print(f"{total - failures}/{total} validator fixtures behaved as expected")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
