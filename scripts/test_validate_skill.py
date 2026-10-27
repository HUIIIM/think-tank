#!/usr/bin/env python3
"""Negative fixtures for scripts/validate_skill.py (SOTA VER-2).

Each case mutates a copy of this repository's SKILL.md (or plugin.json) in a temporary
directory named like the real skill directory, runs the validator, and expects exit 1 with that rule's own error message,
so every rule is tested on its own rather than through another rule.
The unmutated copy must exit 0. Exit status is non-zero if any expectation fails.
"""

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
        sub_skill(r'^  version: "([^"]+)"$', r"  version: 1.5"),
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
        "description over 1024 chars",
        sub_skill(r'^description: "', 'description: "' + "x" * 1100),
        "description must be 1-1024",
    ),
    (
        "missing scripts/ reference",
        sub_skill(r"^## 输出契约$", "## 输出契约\n\n见 `scripts/missing.py`。"),
        "referenced file missing: scripts/missing.py",
    ),
    (
        "plugin.json version drift",
        sub_plugin('"version": "', '"version": "9.9.9-'),
        "plugin.json version",
    ),
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
    root = base / ROOT.name
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
    print(
        f"{len(CASES) + 1 - failures}/{len(CASES) + 1} validator fixtures behaved as expected"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
