#!/usr/bin/env python3
"""Bilingual parity check (issue #35): the two editions of each document ship together.

- SKILL.zh.md is the full Chinese edition. SKILL.md is already written in Chinese, so
  everything after the marker line in SKILL.zh.md must equal SKILL.md after its YAML
  frontmatter, byte for byte. A change to one file without the other fails.
- README.zh.md is the full Chinese translation of README.md. Its structure must match:
  the same sequence of heading levels, the same number of table rows and the same number
  of fenced code blocks, so a section added to one edition but not the other fails.

Usage: python3 scripts/check_parity.py [repo-root]. Exit status 1 on any mismatch.
"""

import re
import sys
from pathlib import Path

MARKER = "<!-- 正文开始：以下与 SKILL.md 正文（frontmatter 之后）逐字相同，由 scripts/check_parity.py 校验 -->"
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


def skill_body(text: str) -> str | None:
    """SKILL.md text after the closing '---' of its frontmatter, or None if there is none."""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return "\n".join(lines[i + 1:])
    return None


def structure(text: str) -> tuple[list[int], int, int]:
    """Heading levels in order, table rows and fenced code blocks, outside fenced code."""
    levels: list[int] = []
    rows = 0
    blocks = 0
    fence = ""
    for line in text.split("\n"):
        m = FENCE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line[m.end():].strip():
                fence = ""
            continue
        if m:
            fence = m.group(1)
            blocks += 1
            continue
        h = re.match(r"^(#{1,6}) +\S", line)
        if h:
            levels.append(len(h.group(1)))
        elif line.lstrip().startswith("|"):
            rows += 1
    return levels, rows, blocks


def check(root: Path) -> list[str]:
    problems: list[str] = []
    try:
        skill = (root / "SKILL.md").read_text(encoding="utf-8")
        skill_zh = (root / "SKILL.zh.md").read_text(encoding="utf-8")
        readme = (root / "README.md").read_text(encoding="utf-8")
        readme_zh = (root / "README.zh.md").read_text(encoding="utf-8")
    except OSError as e:
        return [f"无法读取：{e}"]
    body = skill_body(skill)
    if body is None:
        problems.append("SKILL.md 没有 YAML frontmatter")
    elif skill_zh.count(MARKER) != 1:
        problems.append("SKILL.zh.md 须恰有一行正文开始标记")
    else:
        zh_body = skill_zh.split(MARKER, 1)[1]
        zh_body = zh_body[1:] if zh_body.startswith("\n") else zh_body
        if zh_body != body:
            a, b = body.split("\n"), zh_body.split("\n")
            n = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
            problems.append(f"SKILL.zh.md 正文与 SKILL.md 不一致（正文第 {n + 1} 行起）")
    en, zh = structure(readme), structure(readme_zh)
    names = ("标题层级序列", "表格行数", "代码块数")
    for name, x, y in zip(names, en, zh):
        if x != y:
            problems.append(f"README.zh.md 与 README.md 的{name}不一致：{y} ≠ {x}")
    return problems


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    problems = check(root)
    for p in problems:
        print(f"ERROR {p}")
    print("双语对等：通过" if not problems else f"双语对等：{len(problems)} 处不一致")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
