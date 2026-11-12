#!/usr/bin/env python3
"""List decision records that are due for review (references/decision-record-template.md, rules 6-7).

Reads every .md / .markdown file under the given archive directory. An ATX heading ("#" to
"######" followed by a space, outside fenced code and HTML comments) starts a section that
runs to the next heading of any level. A section holding exactly one "- Verdict：" line is
a record; its fields are read from that section only.
复评日期, 实际结果 and 状态 must each appear exactly once, directly under the record heading
(before any sub-heading); they are never read from sub-sections, sibling sections, a
document title above, fenced code or HTML comments. Field names may be bold; the list
marker may be "-" or "*".
A record is due when its 复评日期 is on or before today, unless its 实际结果 starts with
达到 / 未达到 / 部分达到 or its 状态 starts with 已取代 / 已撤销 (after spaces, emphasis,
quotes and brackets are trimmed): anything unclear keeps the reminder.
Reported as errors:
- a 复评日期 that is not exactly one YYYY-MM-DD date;
- one of the three fields missing from the record's own lines (a copy under a sub-heading
  does not count), written twice there, or written there in a form the field pattern does
  not accept (a quote, a table, a note before the colon, a non-breaking or full-width space);
- a Verdict line outside every heading, sharing its section with another Verdict line, or
  in an unsupported form ("+ ", "1. ", no list marker, indented, lower case, "Verdict（…）：");
- a heading-like line that is not a heading (indented, no space after "#", seven or more
  "#", full-width "＃", a setext underline);
- a fenced code block or HTML comment left open at the end of the file;
- a file with Verdict or 复评日期 that yields no record, or that cannot be read as UTF-8.

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
FIELD = r"^[-*][ \t]+\**{name}\**[ \t]*[：:]\**[ \t]*(.*)$"
HEADING = re.compile(r"(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*")
FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)")
VERDICT = re.compile(FIELD.format(name="Verdict"))
# A Verdict line the field pattern does not accept: other or no list marker, indentation,
# lower case, a parenthesised note before the colon.
LOOSE_VERDICT = re.compile(
    r"^[ \t]*(?:(?:[-*+]|\d+[.)])[ \t]+)?\**verdict\**[ \t]*(?:[（(][^）)\n]*[）)])?[ \t]*\**[：:]", re.I
)
# Looks like a heading to a reader but is not one here.
HEADING_LIKE = re.compile(r" {1,3}#{1,6}[ \t]|#{1,6}[^# \t]|#{7,}|[ \t]*＃")
SETEXT = re.compile(r" {0,3}(=+|-+)[ \t]*")
CHECKED = ("复评日期", "实际结果", "状态")
# A line a reader would take for one of CHECKED that FIELD does not accept: a quote, table or
# other list marker, a non-breaking or full-width space, a parenthesised note before the colon.
LOOSE_FIELD = re.compile(
    r"^[\s>|+\-*\d.)\u3000\xa0]*\**(" + "|".join(CHECKED) + r")\**[\s\u3000\xa0]*(?:[（(][^）)\n]*[）)])?[\s\u3000\xa0]*\**[：:]"
)
NOISE = " \t\u3000\xa0*`_\"'“”‘’「」『』（）()<>[]【】"
REVIEWED = ("达到", "未达到", "部分达到")
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
CLOSED = ("已取代", "已撤销")


def field(section: str, name: str) -> str | None:
    """The value of a field line, with emphasis, quotes, brackets and spaces trimmed."""
    m = re.search(FIELD.format(name=name), section, re.M)
    return m.group(1).strip(NOISE) if m else None


def count(section: str, name: str) -> int:
    return len(re.findall(FIELD.format(name=name), section, re.M))


def code_mask(lines: list[str]) -> tuple[list[bool], bool]:
    """True for each line inside a fenced code block or an HTML comment, and whether one is
    still open at the end. Fences follow CommonMark: the closing fence uses the same
    character, is at least as long as the opening one, and carries no info string."""
    mask: list[bool] = []
    fence = ""
    comment = False
    for line in lines:
        m = FENCE.match(line)
        if fence:
            mask.append(True)
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not m.group(2).strip():
                fence = ""
        elif comment:
            mask.append(True)
            comment = "-->" not in line
        elif m and not (m.group(1)[0] == "`" and "`" in m.group(2)):
            mask.append(True)
            fence = m.group(1)
        elif line.lstrip().startswith("<!--"):
            mask.append(True)
            comment = "-->" not in line.split("<!--", 1)[1]
        else:
            mask.append(False)
    return mask, bool(fence) or comment


def records(text: str) -> tuple[list[tuple[str, str]], int, list[str]]:
    """(title, own lines) for each record, the number of Verdict lines that belong to none,
    and file-level problems. A record's own lines run from its heading to the next heading
    of any level and leave out code and comments."""
    lines = text.split("\n")
    code, unclosed = code_mask(lines)
    problems = ["代码块或 HTML 注释到文件末尾仍未闭合"] if unclosed else []
    odd = [i + 1 for i, line in enumerate(lines) if not code[i] and HEADING_LIKE.match(line)]
    # a setext underline turns the paragraph line above it into a heading this script ignores
    odd += [i + 1 for i, line in enumerate(lines)
            if i and not code[i] and SETEXT.fullmatch(line) and lines[i - 1].strip()
            and not code[i - 1] and not re.match(r"[ \t]*([-*+>|#]|\d+[.)])", lines[i - 1])
            and (line.strip()[0] == "=" or not SETEXT.fullmatch(lines[i - 1]))]
    odd.sort()
    if odd:
        problems.append(f"第 {', '.join(map(str, odd[:5]))} 行像标题但不是（标题须为行首 # 加空格，1–6 个 #）")
    heads: list[tuple[int, str]] = []  # (line index, title)
    for i, line in enumerate(lines):
        if not code[i] and (m := HEADING.fullmatch(line)):
            heads.append((i, m.group(2).strip()))
    stray = sum(1 for i, line in enumerate(lines)
                if not code[i] and LOOSE_VERDICT.match(line) and not VERDICT.match(line))
    owner: dict[int, list[int]] = {}  # nearest heading above -> its Verdict lines
    h = -1
    for v in (i for i, line in enumerate(lines) if not code[i] and VERDICT.match(line)):
        while h + 1 < len(heads) and heads[h + 1][0] < v:
            h += 1
        if h < 0:
            stray += 1
        else:
            owner.setdefault(h, []).append(v)
    found: list[tuple[str, str]] = []
    for n in sorted(owner):
        if len(owner[n]) > 1:
            stray += len(owner[n])
            continue
        start = heads[n][0]
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        own = "\n".join(line for i, line in enumerate(lines[start:end], start) if not code[i])
        found.append((heads[n][1] or "（无标题）", own))
    return found, stray, problems


def scan(root: Path, today: date) -> tuple[list[str], list[str]]:
    due: list[str] = []
    errors: list[str] = []
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if path.is_dir() or path.suffix.lower() not in (".md", ".markdown"):
            continue
        try:
            # universal newlines: CRLF reads as LF; utf-8-sig drops a leading BOM
            text = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeDecodeError) as err:
            errors.append(f"ERROR {rel}: 无法读取（{type(err).__name__}）")
            continue
        found, stray, problems = records(text)
        errors += [f"ERROR {rel}: {p}" for p in problems]
        for title, own in found:
            where = f"{rel}: {title}"
            loose = [line.strip() for line in own.split("\n")
                     if LOOSE_FIELD.match(line) and not any(re.match(FIELD.format(name=n), line) for n in CHECKED)]
            if loose:
                errors.append(f"ERROR {where}: 字段写法无法识别（{loose[0][:30]}），须为行首 \"- 字段名：值\"")
                continue
            # only the record's own lines count: a sub-section may describe another record
            counts = {name: count(own, name) for name in CHECKED}
            twice = [name for name, k in counts.items() if k > 1]
            if twice:
                errors.append(f"ERROR {where}: 字段重复（{'、'.join(twice)}），无法判断哪一个属于本记录")
                continue
            missing = [name for name, k in counts.items() if k == 0]
            if missing:
                errors.append(f"ERROR {where}: 缺少字段（{'、'.join(missing)}），须在记录标题下、子标题之前各写一次")
                continue
            raw = field(own, "复评日期")
            try:
                if not ISO_DATE.fullmatch(raw or ""):
                    raise ValueError
                when = date.fromisoformat(raw or "")
            except ValueError:
                errors.append(f"ERROR {where}: 复评日期缺失或不是 YYYY-MM-DD（{raw!r}）")
                continue
            # only an explicit outcome counts as reviewed and only an explicit status closes a
            # record: anything unclear keeps the reminder
            reviewed = (field(own, "实际结果") or "").startswith(REVIEWED)
            closed = (field(own, "状态") or "").startswith(CLOSED)
            if when <= today and not reviewed and not closed:
                due.append(f"DUE   {where}（复评日期 {when.isoformat()}）")
        if stray:
            errors.append(f"ERROR {rel}: 含 Verdict 但未解析出记录（{stray} 个 Verdict 字段行不在任何记录内）")
        elif not found and ("Verdict" in text or re.search(r"复评日期[^\n]{0,8}[：:]", text)):
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
