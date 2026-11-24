#!/usr/bin/env python3
"""Bilingual parity check (issue #35): the two editions of each document ship together.

- SKILL.zh.md is the full Chinese edition. SKILL.md is already written in Chinese, so
  everything after the marker line in SKILL.zh.md must equal SKILL.md after its YAML
  frontmatter, byte for byte. A change to one file without the other fails.
- README.zh.md is the full Chinese translation of README.md. Its structure must match:
  the same sequence of heading levels, the same number of table rows, fenced code blocks and
  list items, and the same inline code spans and link targets (as multisets; in-page "#"
  anchors and the README.md <-> README.zh.md cross-links are ignored), so a section, row,
  bullet, path or link added to or dropped from one edition fails.

Limits: a changed sentence in prose is not detected, so the README translation is kept in
step by hand. Headings are ATX headings at column 0 ("#" to "######"); indented and setext
headings are not counted. Any line whose first non-space character is "|" counts as a
table row. Line endings are normalised by text-mode reading, so CRLF and LF compare equal.

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


CROSS = {"README.md", "README.zh.md"}


def structure(text: str) -> tuple[list[int], int, int, int, list[str], list[str]]:
    """Heading levels in order, table rows, fenced code blocks, list items, inline code spans
    and link targets, all outside fenced code."""
    levels: list[int] = []
    rows = 0
    blocks = 0
    items = 0
    code: list[str] = []
    links: list[str] = []
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
        code += re.findall(r"`([^`]+)`", line)
        links += [t for t in re.findall(r"\]\(([^)\s]+)\)", line) if not t.startswith("#") and t not in CROSS]
        h = re.match(r"^(#{1,6}) +\S", line)
        if h:
            levels.append(len(h.group(1)))
        elif line.lstrip().startswith("|"):
            rows += 1
        elif re.match(r"^\s*(?:[-*+]|\d+[.)]) +\S", line):
            items += 1
    return levels, rows, blocks, items, sorted(code), sorted(links)


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
    names = ("标题层级序列", "表格行数", "代码块数", "列表项数")
    for name, x, y in zip(names, en[:4], zh[:4]):
        if x != y:
            problems.append(f"README.zh.md 与 README.md 的{name}不一致：{y} ≠ {x}")
    for name, x, y in (("行内代码", en[4], zh[4]), ("链接目标", en[5], zh[5])):
        only_en = sorted(set(x) - set(y)) + [v for v in set(x) & set(y) if x.count(v) > y.count(v)]
        only_zh = sorted(set(y) - set(x)) + [v for v in set(x) & set(y) if y.count(v) > x.count(v)]
        if only_en or only_zh:
            problems.append(f"README.zh.md 与 README.md 的{name}不一致：仅英文版或英文版更多 {only_en}，仅中文版或中文版更多 {only_zh}")
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
