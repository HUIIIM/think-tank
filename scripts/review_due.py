#!/usr/bin/env python3
"""List decision records that are due for review (references/decision-record-template.md, rules 6-7).

Reads every *.md file under the given archive directory. A heading ("#" to "######", outside
fenced code) opens a block that runs to the next heading of the same or a higher level, so
sub-headings stay inside it. A record is the outermost block holding exactly one "- Verdict："
line; field names may be bold, the list marker may be "-" or "*". It is due when its
"- 复评日期：" date is on or before today, its "- 实际结果：" is still empty or starts with
"待复评", and its "- 状态：" is not 已取代 / 已撤销.
Reported as errors: a 复评日期 that is missing or not exactly one YYYY-MM-DD date, a Verdict
line that belongs to no record, a file that mentions Verdict but yields no record, and a
file that cannot be read as UTF-8.

Usage: review_due.py <archive-dir> [--today YYYY-MM-DD] [--strict]
--strict exits 1 when anything is due or in error; otherwise the exit status is 0.
Exit 2 if the directory does not exist. Uses only the standard library.
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

# Field names may be bold ("- **复评日期**：" or "- **复评日期：**"); the value may be in ` or **.
FIELD = r"^[-*][ \t]+\**{name}\**[ \t]*[：:]\**[ \t]*(.*?)[ \t]*$"
HEADING = re.compile(r"(#{1,6})[ \t]+(.*)")
FENCE = re.compile(r"[ \t]*(```|~~~)")
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
CLOSED = ("已取代", "已撤销")


def field(section: str, name: str) -> str | None:
    m = re.search(FIELD.format(name=name), section, re.M)
    return m.group(1).strip("*` \t") if m else None


def records(text: str) -> tuple[list[tuple[str, str]], int]:
    """(title, block) for each record, and the number of Verdict lines outside any record."""
    lines = text.split("\n")
    heads: list[tuple[int, int, str]] = []  # (line index, level, title)
    fenced = False
    for i, line in enumerate(lines):
        if FENCE.match(line):
            fenced = not fenced
        elif not fenced and (m := HEADING.fullmatch(line)):
            heads.append((i, len(m.group(1)), m.group(2).strip()))
    verdict = re.compile(FIELD.format(name="Verdict"))
    found: list[tuple[str, str]] = []
    covered = 0
    used = 0
    for n, (start, level, title) in enumerate(heads):
        if start < covered:
            continue
        end = next((h[0] for h in heads[n + 1:] if h[1] <= level), len(lines))
        block = "\n".join(lines[start:end])
        if sum(1 for line in lines[start:end] if verdict.match(line)) == 1:
            found.append((title, block))
            covered = end
            used += 1
    total = sum(1 for line in lines if verdict.match(line))
    return found, total - used


def scan(root: Path, today: date) -> tuple[list[str], list[str]]:
    due: list[str] = []
    errors: list[str] = []
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        if path.is_dir():
            continue
        try:
            # universal newlines: CRLF reads as LF; utf-8-sig drops a leading BOM
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as err:
            errors.append(f"ERROR {rel}: 无法读取（{type(err).__name__}）")
            continue
        found, stray = records(text)
        for title, section in found:
            where = f"{rel}: {title}"
            raw = field(section, "复评日期")
            try:
                if not ISO_DATE.fullmatch(raw or ""):
                    raise ValueError
                when = date.fromisoformat(raw or "")
            except ValueError:
                errors.append(f"ERROR {where}: 复评日期缺失或不是 YYYY-MM-DD（{raw!r}）")
                continue
            result = field(section, "实际结果") or ""
            status = field(section, "状态") or ""
            if when <= today and (not result or result.startswith("待复评")) and not status.startswith(CLOSED):
                due.append(f"DUE   {where}（复评日期 {when.isoformat()}）")
        if stray:
            errors.append(f"ERROR {rel}: 含 Verdict 但未解析出记录（{stray} 个 Verdict 字段行不在任何记录内）")
        elif not found and "Verdict" in text:
            errors.append(f"ERROR {rel}: 含 Verdict 但未解析出记录（需要标题行与 \"- Verdict：\" 字段行）")
    return due, errors


def iso_date(value: str) -> date:
    if not ISO_DATE.fullmatch(value):
        raise argparse.ArgumentTypeError(f"不是 YYYY-MM-DD：{value}")
    return date.fromisoformat(value)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("archive", type=Path, help="决策记录归档目录")
    ap.add_argument("--today", type=iso_date, default=date.today())
    ap.add_argument("--strict", action="store_true", help="有到期或错误时退出码为 1")
    a = ap.parse_args()
    if not a.archive.is_dir():
        print(f"不是目录：{a.archive}", file=sys.stderr)
        return 2
    due, errors = scan(a.archive, a.today)
    for line in errors + due:
        print(line)
    print(f"{len(due)} 条到期待复评，{len(errors)} 条错误（截至 {a.today.isoformat()}）")
    return 1 if a.strict and (due or errors) else 0


if __name__ == "__main__":
    sys.exit(main())
