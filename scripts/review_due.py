#!/usr/bin/env python3
"""List decision records that are due for review (references/decision-record-template.md, rules 6-7).

Reads every *.md file under the given archive directory. A record is a "## " section
that has a "- Verdict：" line (field names may be bold). It is due when its "- 复评日期：" date is on or before today,
its "- 实际结果：" is still empty or starts with "待复评", and its "- 状态：" is not 已取代 / 已撤销.
A record whose 复评日期 is missing or not a single YYYY-MM-DD date is reported as an error.

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
FIELD = r"^- \**{name}\**[：:]\**[ \t]*(.*?)[ \t]*$"
CLOSED = ("已取代", "已撤销")


def field(section: str, name: str) -> str | None:
    m = re.search(FIELD.format(name=name), section, re.M)
    return m.group(1).strip("*` \t") if m else None


def scan(root: Path, today: date) -> tuple[list[str], list[str]]:
    due: list[str] = []
    errors: list[str] = []
    for path in sorted(root.rglob("*.md")):
        text = path.read_text(encoding="utf-8")  # universal newlines: CRLF reads as LF
        for section in re.split(r"^(?=## )", text, flags=re.M):
            if not section.startswith("## ") or field(section, "Verdict") is None:
                continue
            title = section.splitlines()[0][3:].strip()
            where = f"{path.relative_to(root)}: {title}"
            raw = field(section, "复评日期")
            try:
                when = date.fromisoformat(raw or "")
            except ValueError:
                errors.append(f"ERROR {where}: 复评日期缺失或不是 YYYY-MM-DD（{raw!r}）")
                continue
            result = field(section, "实际结果") or ""
            status = field(section, "状态") or ""
            if when <= today and (not result or result.startswith("待复评")) and not status.startswith(CLOSED):
                due.append(f"DUE   {where}（复评日期 {when.isoformat()}）")
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
