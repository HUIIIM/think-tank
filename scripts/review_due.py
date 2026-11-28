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
A record is due when its 复评日期 is on or before today, unless its 状态 is exactly one of
已复评（YYYY-MM-DD）, 已取代（→ <record ID>） or 已撤销（YYYY-MM-DD）, with a valid date not
after today (half-width brackets also accepted). 实际结果 never closes a record on its own:
free text cannot be told apart from a hedge, so anything but an exact closing 状态 keeps the
reminder.
Reported as errors:
- a 复评日期 that is not exactly one YYYY-MM-DD date;
- a 状态 that starts like a closing value but is not one exactly, or carries an invalid or
  future date; a 状态 of 已复评 whose 实际结果 does not start with 达到 / 未达到 / 部分达到;
- one of the three fields missing from the record's own lines (a copy under a sub-heading
  does not count), written twice there, or written there in a form the field pattern does
  not accept (a quote, a table, a note before the colon, a non-breaking or full-width space);
- a Verdict line outside every heading, sharing its section with another Verdict line, or
  in an unsupported form ("+ ", "1. ", no list marker, indented, lower case, "Verdict（…）：");
- a heading-like line that is not a heading (indented, no space after "#", seven or more
  "#", full-width "＃", a setext underline);
- a fenced code block or HTML comment left open at the end of the file;
- a file with Verdict or 复评日期 that yields no record, or that cannot be read as UTF-8;
- a 复评日期 line outside every record in a file where another record was read;
- a directory that cannot be listed, a symlinked directory (not followed), a broken
  symlink, a *.md that is not a regular file, or an archive with no record files at all.
  An unreadable archive root exits 2.

Usage: review_due.py <archive-dir> [--today YYYY-MM-DD] [--strict]
--strict exits 1 when anything is due or in error; otherwise the exit status is 0.
Exit 2 if the directory does not exist. Uses only the standard library.
"""

import argparse
import io
import os
import re
import stat
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
    r"^[ \t]*(?:(?:[-*+]|\d+[.)])[ \t]+)?\**verdict\**[ \t]*(?:[（(][^）)\n]*[）)])?[ \t]*\**[：:]", re.IGNORECASE
)
# Looks like a heading to a reader but is not one here.
HEADING_LIKE = re.compile(r" {1,3}#{1,6}[ \t]|#{1,6}[^# \t]|#{1,6}$|#{7,}|[ \t]*＃|[ \t]*<h[1-6][ \t>]", re.IGNORECASE)
SETEXT = re.compile(r" {0,3}(=+|-+)[ \t]*")
CHECKED = ("复评日期", "实际结果", "状态")
# A line a reader would take for one of CHECKED that FIELD does not accept: a quote, table or
# other list marker, a non-breaking or full-width space, a parenthesised note before the colon.
# Indented lines are sub-items (e.g. a follow-up's own 状态) and are left alone.
LOOSE_FIELD = re.compile(
    r"^(?![ \t])[\s>|+\-*\d.)\u3000\xa0]*\**(" + "|".join(CHECKED) + r")\**[\s\u3000\xa0]*(?:[（(][^）)\n]*[）)])?[\s\u3000\xa0]*\**[：:]"
)
NOISE = " \t\u3000\xa0*`_\"'“”‘’「」『』（）()【】"
# Only an exact 状态 value closes a record; free text in 实际结果 never does, because no pattern
# can tell every hedge ("证据待补", "等待验证", "N/A") from an outcome.
RECORD_ID = r"[A-Za-z]+-[A-Za-z0-9-]*\d[A-Za-z0-9-]*"
STATUS_REVIEWED = re.compile(r"已复评[（(](\d{4}-\d{2}-\d{2})[）)]")
STATUS_REPLACED = re.compile(rf"已取代[（(]\s*→\s*{RECORD_ID}\s*[）)]")
STATUS_WITHDRAWN = re.compile(r"已撤销[（(](\d{4}-\d{2}-\d{2})[）)]")
STATUS_FINAL = ("已复评", "已取代", "已撤销")
OUTCOME = re.compile(r"(?:部分达到|未达到|达到)(?:$|[\s—\-（(：:，,。；;])")
# 复评日期 followed, within a few characters, by a year: a field line, a table cell or prose
DATE_LIKE = re.compile(r"复评日期[^\n\d]{0,8}?[\s：:|*`]\s*[*`]*\s*\d{4}")
DATE_FIELD = re.compile(FIELD.format(name="复评日期"))
ISO_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
SUFFIXES = (".md", ".markdown")


def status_value(section: str) -> str:
    """The 状态 value with emphasis and code marks removed and outer spaces trimmed; its
    brackets are kept, they are part of the closed forms."""
    m = re.search(FIELD.format(name="状态"), section, re.MULTILINE)
    return re.sub(r"[*`]", "", m.group(1)).strip(" \t\u3000\xa0") if m else ""


def closing(status: str, today: date) -> tuple[bool, str | None]:
    """(closed, problem): closed only for an exact 已复评（date）, 已取代（→ ID） or 已撤销（date）
    with a valid date not after today; a value that starts like one but is not is a problem."""
    if STATUS_REPLACED.fullmatch(status):
        return True, None
    m = STATUS_REVIEWED.fullmatch(status) or STATUS_WITHDRAWN.fullmatch(status)
    if m:
        try:
            when = date.fromisoformat(m.group(1))
        except ValueError:
            return False, f"状态里的日期不合法（{status}）"
        if when > today:
            return False, f"状态里的日期晚于今天（{status}）"
        return True, None
    if status.startswith(STATUS_FINAL):
        return False, f"状态写法无法识别（{status[:30]}），须为 已复评（YYYY-MM-DD）/ 已取代（→ 记录编号）/ 已撤销（YYYY-MM-DD）"
    return False, None


def field(section: str, name: str) -> str | None:
    """The value of a field line: emphasis and code marks removed, quotes, brackets and spaces
    trimmed from both ends."""
    m = re.search(FIELD.format(name=name), section, re.MULTILINE)
    return re.sub(r"[*`]", "", m.group(1)).strip(NOISE) if m else None


def count(section: str, name: str) -> int:
    return len(re.findall(FIELD.format(name=name), section, re.MULTILINE))


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
    levels: list[int] = []
    for i, line in enumerate(lines):
        if not code[i] and (m := HEADING.fullmatch(line)):
            heads.append((i, m.group(2).strip()))
            levels.append(len(m.group(1)))
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
    own_lines: set[int] = set()
    subtree: set[int] = set()
    for n in sorted(owner):
        if len(owner[n]) > 1:
            stray += len(owner[n])
            continue
        start = heads[n][0]
        end = heads[n + 1][0] if n + 1 < len(heads) else len(lines)
        own = "\n".join(line for i, line in enumerate(lines[start:end], start) if not code[i])
        found.append((heads[n][1] or "（无标题）", own))
        own_lines.update(range(start, end))
        # the record's sub-sections: up to the next heading of the same or a higher level
        tree_end = next((heads[k][0] for k in range(n + 1, len(heads)) if levels[k] <= levels[n]), len(lines))
        subtree.update(range(start, tree_end))
    # A record that was not recognised (its Verdict missing or malformed) shows up as a 复评日期
    # nobody owns, even when another record in the file was read: any dated mention outside
    # every record's sub-sections, or a "- 复评日期：" field line outside a record's own lines
    # (a record nested under another one still has its own field line).
    orphan = sorted({i + 1 for i, line in enumerate(lines) if not code[i] and (
        (i not in subtree and DATE_LIKE.search(line)) or (i not in own_lines and DATE_FIELD.match(line)))})
    if orphan and found:
        problems.append(f"第 {', '.join(map(str, orphan[:5]))} 行的复评日期不属于任何记录（Verdict 缺失或写法无法识别）")
    return found, stray, problems


def walk(root: Path) -> tuple[list[Path], list[str]]:
    """Record files under root, and the directories that could not be listed or followed.

    os.walk is used for its onerror hook: Path.rglob skips an unreadable directory silently."""
    files: list[Path] = []
    errors: list[str] = []

    def unreadable(err: OSError) -> None:
        where = Path(err.filename).relative_to(root) if err.filename else root
        errors.append(f"ERROR {where}: 目录无法读取（{type(err).__name__}），其中的记录未检查")

    for current, dirs, names in os.walk(root, onerror=unreadable):
        here = Path(current)
        for d in sorted(dirs):
            if (here / d).is_symlink():
                errors.append(f"ERROR {(here / d).relative_to(root)}: 符号链接目录不跟随，其中的记录未检查")
        for n in sorted(names):
            path = here / n
            if path.suffix.lower() in SUFFIXES:
                files.append(path)
            elif path.is_symlink() and not path.exists():
                errors.append(f"ERROR {path.relative_to(root)}: 断开的符号链接（可能是未挂载的目录），其中的记录未检查")
    return sorted(files), errors


def scan(root: Path, today: date) -> tuple[list[str], list[str], int]:
    due: list[str] = []
    paths, errors = walk(root)
    if not paths and not errors:
        errors.append("ERROR .: 归档目录中没有 .md / .markdown 记录文件")
    for path in paths:
        rel = path.relative_to(root)
        try:
            # a FIFO or device named *.md would block or read as empty
            if not stat.S_ISREG(path.stat().st_mode):
                errors.append(f"ERROR {rel}: 不是普通文件，未读取")
                continue
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
            # only an exact closing 状态 ends the reminders; anything else keeps them
            status = status_value(own)
            closed, problem = closing(status, today)
            if problem:
                errors.append(f"ERROR {where}: {problem}")
                continue
            if status.startswith("已复评") and not OUTCOME.match(field(own, "实际结果") or ""):
                errors.append(f"ERROR {where}: 状态为已复评，但实际结果不是以 达到 / 未达到 / 部分达到 开头")
                continue
            if when <= today and not closed:
                due.append(f"DUE   {where}（复评日期 {when.isoformat()}）")
        if stray:
            errors.append(f"ERROR {rel}: 含 Verdict 但未解析出记录（{stray} 个 Verdict 字段行不在任何记录内）")
        elif not found and "Verdict" in text:
            errors.append(f"ERROR {rel}: 含 Verdict 但未解析出记录（需要标题行与 \"- Verdict：\" 字段行）")
        elif not found and re.search(r"复评日期[^\n]{0,8}[：:]", text):
            errors.append(f"ERROR {rel}: 有复评日期但没有 \"- Verdict：\" 字段行，未解析出记录")
    return due, errors, len(paths)


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
    # a file name that is not valid UTF-8 must not crash the run and drop the lines after it
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(errors="backslashreplace")
    if not a.archive.is_dir():
        print(f"不是目录：{a.archive}", file=sys.stderr)
        return 2
    try:
        os.scandir(a.archive).close()
    except OSError as err:
        print(f"无法读取归档目录：{a.archive}（{type(err).__name__}）", file=sys.stderr)
        return 2
    due, errors, scanned = scan(a.archive, a.today)
    for line in errors + due:
        print(line)
    print(f"扫描 {scanned} 个文件：{len(due)} 条到期待复评，{len(errors)} 条错误（截至 {a.today.isoformat()}）")
    return 1 if a.strict and (due or errors) else 0


if __name__ == "__main__":
    sys.exit(main())
