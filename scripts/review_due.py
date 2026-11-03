#!/usr/bin/env python3
"""List decision records that are due for review (references/decision-record-template.md, rules 6-7).

Reads every *.md file under the given archive directory. A record is a heading section
(any level, "#" to "######") that has a "- Verdict：" line; field names may be bold, the
list marker may be "-" or "*". It is due when its "- 复评日期：" date is on or before today,
its "- 实际结果：" is still empty or starts with "待复评", and its "- 状态：" is not 已取代 / 已撤销.
Reported as errors: a 复评日期 that is missing or not exactly one YYYY-MM-DD date, a file that
mentions Verdict but yields no record, and a file that cannot be read as UTF-8.

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
HEADING = r"^(?=#{1,6}[ \t])"
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
CLOSED = ("已取代", "已撤销")


def field(section: str, name: str) -> str | None:
    m = re.search(FIELD.format(name=name), section, re.M)
    return m.group(1).strip("*` \t") if m else None


def scan(root: Path, today: date) -> tuple[list[str], list[str]]:
    due: list[str] = []
    errors: list[str] = []
    for path in sorted(root.rglob("*.md")):
        rel = path.relative_to(root)
        try:
            # universal newlines: CRLF reads as LF; utf-8-sig drops a leading BOM
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as err:
            errors.append(f"ERROR {rel}: 无法读取（{type(err).__name__}）")
            continue
        found = 0
        for section in re.split(HEADING, text, flags=re.M):
            if not section.startswith("#") or field(section, "Verdict") is None:
                continue
            found += 1
            title = section.splitlines()[0].lstrip("#").strip()
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
        if not found and "Verdict" in text:
            errors.append(f"ERROR {rel}: 含 Verdict 但未解析出记录（需要标题行与 \"- Verdict：\" 字段行）")
    return due, errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("archive", type=Path, help="决策记录归档目录")
    ap.add_argument("--today", type=date.fromisoformat, default=date.today())
    ap.add_argument("--strict", action="store_true", help="有到期或错误时退出码为 1")
    a = ap.parse_args()
    if not a.archive.is_dir():
        print(f"不是目录：{a.archive}", file=sys.stderr)
        return 2
    due, errors = scan(a.archive, a.today)
    for line in errors + due:
        print(line)
    print(f"{len(due)} 条到期待复评，{len(errors)} 条复评日期有误（截至 {a.today.isoformat()}）")
    return 1 if a.strict and (due or errors) else 0


if __name__ == "__main__":
    sys.exit(main())
