#!/usr/bin/env python3
"""List decision records that are due for review (references/decision-record-template.md, rules 6-7).

Reads every *.md file under the given archive directory. An ATX heading ("#" to "######"
followed by a space, outside fenced code) opens a block that runs to the next heading of
the same or a higher level, so sub-headings stay inside it. Each "- Verdict：" line belongs
to the deepest heading block that contains it; that block is the record, and its fields
are read only from that block, never from sibling sections, a document title above it, or
fenced code. Field names may be bold; the list marker may be "-" or "*".
A record is due when its "- 复评日期：" date is on or before today, its "- 实际结果：" is still
empty or starts with "待复评", and its "- 状态：" is not 已取代 / 已撤销.
Reported as errors: a 复评日期 that is missing or not exactly one YYYY-MM-DD date; a Verdict
line outside every heading, or sharing its deepest heading with another Verdict line (a record
nested under another record's heading is read on its own and left out of the outer one); a
Verdict line in an unsupported form ("+ ", "1. ", indented, lower-case); a file that mentions
Verdict but yields no record; and a file that cannot be read as UTF-8.

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
HEADING = re.compile(r"(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*")
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")
VERDICT = re.compile(FIELD.format(name="Verdict"))
# A Verdict line the field pattern does not accept: other list markers, indentation, lower case.
LOOSE_VERDICT = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+\**verdict\**[ \t]*[：:]", re.I)
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
CLOSED = ("已取代", "已撤销")


def field(section: str, name: str) -> str | None:
    m = re.search(FIELD.format(name=name), section, re.M)
    return m.group(1).strip("*` \t") if m else None


def code_mask(lines: list[str]) -> list[bool]:
    """True for each line inside a fenced code block (CommonMark: the closing fence uses the
    same character, is at least as long as the opening one, and carries no info string)."""
    mask: list[bool] = []
    fence = ""
    for line in lines:
        m = FENCE.match(line)
        if fence:
            mask.append(True)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip():
                fence = ""
        elif m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            mask.append(True)
            fence = m.group(1)
        else:
            mask.append(False)
    return mask


def records(text: str) -> tuple[list[tuple[str, str]], int]:
    """(title, block) for each record, and the number of Verdict lines that belong to none.

    The block keeps only lines outside fenced code, so fields are never read from code."""
    lines = text.split("\n")
    code = code_mask(lines)
    heads: list[tuple[int, int, str]] = []  # (line index, level, title)
    for i, line in enumerate(lines):
        if not code[i] and (m := HEADING.fullmatch(line)):
            heads.append((i, len(m.group(1)), m.group(2).strip()))
    # end of each heading's block: the next heading of the same or a higher level
    ends = [len(lines)] * len(heads)
    open_heads: list[int] = []
    for n, (start, level, _) in enumerate(heads):
        while open_heads and heads[open_heads[-1]][1] >= level:
            ends[open_heads.pop()] = start
        open_heads.append(n)
    verdicts = [i for i, line in enumerate(lines) if not code[i] and VERDICT.match(line)]
    loose = sum(1 for i, line in enumerate(lines)
                if not code[i] and LOOSE_VERDICT.match(line) and not VERDICT.match(line))
    owner: dict[int, list[int]] = {}  # deepest enclosing heading -> its Verdict lines
    stray = loose
    h = -1
    for v in verdicts:
        while h + 1 < len(heads) and heads[h + 1][0] < v:
            h += 1
        # the last heading before v always encloses it: any heading closing its block comes after v
        if h < 0:
            stray += 1
        else:
            owner.setdefault(h, []).append(v)
    owners = [n for n in sorted(owner) if len(owner[n]) == 1]
    stray += sum(len(v) for v in owner.values() if len(v) > 1)
    # each line goes to the innermost record around it, so a nested record keeps its own fields
    body: dict[int, list[str]] = {n: [] for n in owners}
    starts = {heads[n][0]: n for n in owners}
    stack: list[int] = []
    for i, line in enumerate(lines):
        while stack and ends[stack[-1]] <= i:
            stack.pop()
        if i in starts:
            stack.append(starts[i])
        if stack and not code[i]:
            body[stack[-1]].append(line)
    found = [(heads[n][2], "\n".join(body[n])) for n in owners]
    return found, stray


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
