#!/usr/bin/env python3
"""Fixtures for scripts/review_due.py (SOTA VER-2).

Each case writes a small archive to a temporary directory, runs the script with a fixed
--today, and checks the exit status and which records are listed as DUE or ERROR. A last
check keeps the script's field names in step with references/decision-record-template.md.
Exit status is non-zero if any expectation fails.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "review_due.py"
TEMPLATE = ROOT / "references" / "decision-record-template.md"
TODAY = "2026-11-30"
# ERROR messages about a whole file rather than one record
FILE_LEVEL = ("无法读取", "含 Verdict", "第 ", "代码块或 HTML 注释")


def record(rid: str, review: str | None = "2026-11-30", result: str = "待复评", status: str = "已采纳") -> str:
    lines = [f"## {rid}（终裁·改，2026-10-30；示例议题）", "", "- Verdict：改——示例。"]
    if review is not None:
        lines.append(f"- 复评日期：{review}")
    lines += [f"- 实际结果：{result}", f"- 状态：{status}", ""]
    return "\n".join(lines)


# name -> (files, extra args, expected exit, expected DUE ids, expected ERROR ids)
CASES: dict[str, tuple[dict[str, str], list[str], int, set[str], set[str]]] = {
    "due today": ({"a.md": record("TT-1")}, [], 0, {"TT-1"}, set()),
    "due earlier": ({"a.md": record("TT-1", review="2026-11-01")}, [], 0, {"TT-1"}, set()),
    "not yet due": ({"a.md": record("TT-1", review="2026-12-01")}, [], 0, set(), set()),
    "already reviewed": ({"a.md": record("TT-1", result="达到——周报更正 0 次")}, [], 0, set(), set()),
    "pending with note": ({"a.md": record("TT-1", result="待复评（数据 12-02 到）")}, [], 0, {"TT-1"}, set()),
    "empty result": ({"a.md": record("TT-1", result="")}, [], 0, {"TT-1"}, set()),
    "superseded": ({"a.md": record("TT-1", status="已取代（→ TT-9）")}, [], 0, set(), set()),
    "withdrawn": ({"a.md": record("TT-1", status="已撤销")}, [], 0, set(), set()),
    "missing date": ({"a.md": record("TT-1", review=None)}, [], 0, set(), {"TT-1"}),
    "date with text": ({"a.md": record("TT-1", review="2026-11-30（4 期后）")}, [], 0, set(), {"TT-1"}),
    "placeholder date": ({"a.md": record("TT-1", review="<YYYY-MM-DD>")}, [], 0, set(), {"TT-1"}),
    "not a record": ({"a.md": "## 笔记\n\n- 复评日期：2026-01-01\n"}, [], 0, set(), set()),
    "two records one file": (
        {"a.md": record("TT-1", review="2027-01-01") + "\n" + record("TT-2")}, [], 0, {"TT-2"}, set()
    ),
    "subdirectory and CRLF": ({"2026/b.md": record("TT-3").replace("\n", "\r\n")}, [], 0, {"TT-3"}, set()),
    "bold names": (
        {"a.md": record("TT-1").replace("- Verdict：", "- **Verdict：**").replace("- 复评日期：", "- **复评日期**：")},
        [], 0, {"TT-1"}, set(),
    ),
    "bold value": ({"a.md": record("TT-1", review="**2026-11-30**", status="**已取代（→ TT-9）**")}, [], 0, set(), set()),
    "code value": ({"a.md": record("TT-1", review="`2026-11-30`")}, [], 0, {"TT-1"}, set()),
    "level-1 heading": ({"a.md": record("TT-1").replace("## ", "# ", 1)}, [], 0, {"TT-1"}, set()),
    "level-3 heading": ({"a.md": record("TT-1").replace("## ", "### ", 1)}, [], 0, {"TT-1"}, set()),
    "two level-3 records": (
        {"a.md": "# 归档\n\n" + (record("TT-1", review="2027-01-01") + "\n" + record("TT-2")).replace("## ", "### ")},
        [], 0, {"TT-2"}, set(),
    ),
    "leading BOM": ({"a.md": "\ufeff" + record("TT-1")}, [], 0, {"TT-1"}, set()),
    "star list marker": ({"a.md": record("TT-1").replace("- ", "* ")}, [], 0, {"TT-1"}, set()),
    "space before colon": ({"a.md": record("TT-1").replace("- Verdict：", "- Verdict ：")}, [], 0, {"TT-1"}, set()),
    "basic-format date": ({"a.md": record("TT-1", review="20261130")}, [], 0, set(), {"TT-1"}),
    "ISO week date": ({"a.md": record("TT-1", review="2026-W48-1")}, [], 0, set(), {"TT-1"}),
    "invalid month": ({"a.md": record("TT-1", review="2026-13-01")}, [], 0, set(), {"TT-1"}),
    "no heading": ({"a.md": "- Verdict：改。\n- 复评日期：2026-11-30\n"}, [], 0, set(), {"a.md"}),
    "not UTF-8 then a good file": (
        {"a.md": "## TT-0\n- Verdict：\xff", "b.md": record("TT-1")}, [], 0, {"TT-1"}, {"a.md"}
    ),
    "sub-heading after Verdict": (
        {"a.md": record("TT-1").replace("- 复评日期：", "### 三队观点\n\n- 红队：示例。\n- 复评日期：")}, [], 0, {"TT-1"}, set()
    ),
    # the record is the deepest heading holding the Verdict, so it is listed under that heading's name
    "sub-heading before Verdict": ({"a.md": record("TT-1").replace("- Verdict：", "### 背景\n\n- Verdict：")}, [], 0, {"背景"}, set()),
    "status after sub-heading": (
        {"a.md": record("TT-1", status="已取代（→ TT-9）").replace("- 实际结果：", "### 结果\n\n- 实际结果：")}, [], 0, set(), set()
    ),
    "heading in code fence": (
        {"a.md": record("TT-1").replace("- 复评日期：", "```\n# 注释\n```\n- 复评日期：")}, [], 0, {"TT-1"}, set()
    ),
    # TT-2 nests under TT-1: each is read on its own, and TT-1 does not borrow TT-2's fields
    "level-1 then level-2 record": ({"a.md": record("TT-1", review="2027-01-01").replace("## ", "# ", 1) + "\n" + record("TT-2")}, [], 0, {"TT-2"}, set()),
    "outer record borrows nothing": (
        {"a.md": "# TT-1（示例）\n- Verdict：改。\n- 实际结果：待复评\n\n" + record("TT-2", review="2026-11-01")}, [], 0, {"TT-2"}, {"TT-1"}
    ),
    "document title, earlier sibling has fields": (
        {"a.md": "# 决策记录 TT-2\n\n## 关联记录\n\n- TT-1：周报改周一\n- 状态：已取代（→ TT-2）\n"
                 "- 实际结果：达到——TT-0\n- 复评日期：2099-01-01\n\n" + record("TT-2")},
        [], 0, {"TT-2"}, set(),
    ),
    "fields in a code block are not read": (
        {"a.md": record("TT-1", review=None).replace("- Verdict：改——示例。", "- Verdict：改——示例。\n```\n- 复评日期：2026-11-30\n```")},
        [], 0, set(), {"TT-1"},
    ),
    "tilde fence hides a heading": (
        {"a.md": record("TT-1").replace("- 复评日期：", "~~~\n## 注释\n~~~\n- 复评日期：")}, [], 0, {"TT-1"}, set()
    ),
    "longer fence holds a shorter one": (
        {"a.md": record("TT-1").replace("- 复评日期：", "````\n```\n## 注释\n```\n````\n- 复评日期：")}, [], 0, {"TT-1"}, set()
    ),
    "inline code at line start is not a fence": (
        {"a.md": record("TT-1").replace("- 复评日期：", "```x``` 是行内代码\n- 复评日期：")}, [], 0, {"TT-1"}, set()
    ),
    "tilde does not close a backtick fence": (
        {"a.md": record("TT-1").replace("- 复评日期：", "```\n~~~\n## 注释\n```\n- 复评日期：")}, [], 0, {"TT-1"}, set()
    ),
    "fence with info string does not close": (
        {"a.md": record("TT-1").replace("- 复评日期：", "```\n```py\n## 注释\n```\n- 复评日期：")}, [], 0, {"TT-1"}, set()
    ),
    "two Verdicts under one heading": (
        {"a.md": record("TT-1").replace("- Verdict：改——示例。", "- Verdict：改——示例。\n- Verdict：驳。")}, [], 0, set(), {"a.md"}
    ),
    "two Verdicts beside a good record": (
        {"a.md": record("TT-0", review="2027-01-01") + "\n" + record("TT-1").replace("- Verdict：改——示例。", "- Verdict：改——示例。\n- Verdict：驳。")},
        [], 0, set(), {"a.md"},
    ),
    "later sibling section lends nothing": (
        {"a.md": record("TT-1", review=None) + "\n## 附录\n\n- 复评日期：2026-11-30\n"}, [], 0, set(), {"TT-1"}
    ),
    "B2: sibling sub-section inside the record": (
        {"a.md": "## TT-2\n- Verdict：改\n### 关联记录\n- 状态：已取代（→ TT-2）\n### 复评\n"
                 "- 复评日期：2026-11-01\n- 实际结果：待复评\n- 状态：已采纳\n"},
        [], 0, set(), {"TT-2"},
    ),
    "B2: status twice": ({"a.md": record("TT-1", status="已取代（→ TT-9）") + "- 状态：已采纳\n"}, [], 0, set(), {"TT-1"}),
    "B2: review date twice": ({"a.md": record("TT-1", review="2027-06-01") + "- 复评日期：2026-11-01\n"}, [], 0, set(), {"TT-1"}),
    "B2: result twice": ({"a.md": record("TT-1", result="达到——草") + "- 实际结果：待复评\n"}, [], 0, set(), {"TT-1"}),
    "B2: unrecognised record heading": (
        {"a.md": "# 决策记录 TT-2\n\n## 关联记录\n\n- 状态：已取代（→ TT-2）\n- 实际结果：达到——TT-0\n\n"
                 + record("TT-2").replace("## TT-2", "  ## TT-2")},
        [], 0, set(), {"关联记录", "a.md"},
    ),
    "full-width hash heading": ({"a.md": record("TT-1") + "\n＃＃ TT-2\n"}, [], 0, {"TT-1"}, {"a.md"}),
    "unclosed fence swallows a record": (
        {"a.md": record("TT-1", review="2027-01-01") + "```\n" + record("TT-2")}, [], 0, set(), {"a.md"}
    ),
    "HTML comment hides heading and fields": (
        {"a.md": record("TT-1").replace("- 复评日期：", "<!--\n## 旧稿\n- 状态：已撤销\n-->\n- 复评日期：")}, [], 0, {"TT-1"}, set()
    ),
    "fence indented four spaces is not a fence": (
        {"a.md": record("TT-1").replace("- 复评日期：", "    ```\n- 复评日期：")}, [], 0, {"TT-1"}, set()
    ),
    "Verdict in a code block is ignored": (
        {"a.md": record("TT-1").replace("- 复评日期：", "```\n- Verdict：驳。\n+ Verdict：驳。\n```\n- 复评日期：")}, [], 0, {"TT-1"}, set()
    ),
    "numbered Verdict beside a good record": (
        {"a.md": record("TT-1", review="2027-01-01") + "\n" + record("TT-2").replace("- Verdict：", "1. Verdict：")}, [], 0, set(), {"a.md"}
    ),
    "bare Verdict beside a good record": (
        {"a.md": record("TT-1", review="2027-01-01") + "\n## TT-2\n**Verdict**：改\n"}, [], 0, set(), {"a.md"}
    ),
    "annotated Verdict beside a good record": (
        {"a.md": record("TT-1", review="2027-01-01") + "\n## TT-3\n- Verdict（终裁）：改\n"}, [], 0, set(), {"a.md"}
    ),
    "status in full-width parentheses": ({"a.md": record("TT-1", status="（已取代 → TT-9）")}, [], 0, set(), set()),
    "empty heading gets a placeholder name": ({"a.md": record("TT-1").replace("## TT-1（终裁·改，2026-10-30；示例议题）", "## ")}, [], 0, {"（无标题）"}, set()),
    "Verdict only in prose": ({"a.md": "## 说明\n\n本文件说明 Verdict 的写法。\n"}, [], 0, set(), {"a.md"}),
    "hash without space is not a heading": ({"a.md": "#TT-1\n- Verdict：改。\n- 复评日期：2026-11-30\n"}, [], 0, set(), {"a.md"}),
    "closing hashes dropped from name": ({"a.md": record("TT-1").replace("## TT-1（终裁·改，2026-10-30；示例议题）", "## TT-1 ##")}, [], 0, {"TT-1"}, set()),
    "second record with loose marker": (
        {"a.md": record("TT-1", review="2027-01-01") + "\n" + record("TT-2").replace("- Verdict：", "+ Verdict：")}, [], 0, set(), {"a.md"}
    ),
    "lower-case verdict": ({"a.md": record("TT-1").replace("- Verdict：", "- verdict：")}, [], 0, set(), {"a.md"}),
    "level-3 then level-2 record": (
        {"a.md": record("TT-1").replace("## ", "### ", 1) + "\n" + record("TT-2", review="2027-01-01")}, [], 0, {"TT-1"}, set()
    ),
    "unsupported list marker": ({"a.md": record("TT-1").replace("- ", "+ ")}, [], 0, set(), {"a.md"}),
    "Verdict before first heading": ({"a.md": "- Verdict：改。\n\n" + record("TT-1")}, [], 0, {"TT-1"}, {"a.md"}),
    "directory named .md": ({"x.md/b.md": record("TT-1")}, [], 0, {"TT-1"}, set()),
    "strict with due": ({"a.md": record("TT-1")}, ["--strict"], 1, {"TT-1"}, set()),
    "strict with error": ({"a.md": record("TT-1", review=None)}, ["--strict"], 1, set(), {"TT-1"}),
    "strict clean": ({"a.md": record("TT-1", review="2027-01-01")}, ["--strict"], 0, set(), set()),
}


def run(archive: Path, extra: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(archive), "--today", TODAY, *extra],
        capture_output=True, text=True, encoding="utf-8",
    )


def ids(out: str, tag: str) -> set[str]:
    found = set()
    for line in out.splitlines():
        if line.startswith(tag):
            rest = line.split(None, 1)[1]
            # "ERROR a.md: 无法读取…" names a file; "DUE   a.md: TT-1（…）" names a record
            file, _, title = rest.partition(": ")
            if not title or title.startswith(FILE_LEVEL):
                found.add(file)
                continue
            name = re.split(r"（复评日期 |: ", title, maxsplit=1)[0]  # drop the DUE / ERROR suffix
            found.add(name.split("（", 1)[0] or name)
    return found


def main() -> int:
    failures = 0
    for name, (files, extra, code, due, errors) in CASES.items():
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in files.items():
                p = Path(tmp) / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                raw = text.encode("utf-8")
                p.write_bytes(raw.replace("\xff".encode("utf-8"), b"\xff"))  # "\xff" stands for a non-UTF-8 byte
            r = run(Path(tmp), extra)
        got = (r.returncode, ids(r.stdout, "DUE"), ids(r.stdout, "ERROR"))
        ok = got == (code, due, errors)
        failures += not ok
        print(f"{'ok ' if ok else 'BAD'} {name} -> {got}")
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "gone.md").symlink_to(Path(tmp) / "nowhere.md")
        (Path(tmp) / "b.md").write_text(record("TT-1"), encoding="utf-8")
        r = run(Path(tmp), [])
    got = (r.returncode, ids(r.stdout, "DUE"), ids(r.stdout, "ERROR"))
    ok = got == (0, {"TT-1"}, {"gone.md"})
    failures += not ok
    print(f"{'ok ' if ok else 'BAD'} broken symlink then a good file -> {got}")
    with tempfile.TemporaryDirectory() as tmp:
        r = run(Path(tmp), [])
        bad = subprocess.run([sys.executable, str(SCRIPT), tmp, "--today", "20261130"], capture_output=True, text=True)
    ok = r.returncode == 0 and bad.returncode == 2
    failures += not ok
    print(f"{'ok ' if ok else 'BAD'} --today accepts only YYYY-MM-DD -> {bad.returncode}")
    with tempfile.TemporaryDirectory() as tmp:
        r = run(Path(tmp) / "missing", [])
    ok = r.returncode == 2
    failures += not ok
    print(f"{'ok ' if ok else 'BAD'} missing directory -> {r.returncode}")
    template = TEMPLATE.read_text(encoding="utf-8")
    for needle in ("- Verdict：", "- 复评日期：", "- 实际结果：待复评", "- 状态："):
        ok = needle in template
        failures += not ok
        print(f"{'ok ' if ok else 'BAD'} template has {needle!r}")
    total = len(CASES) + 7
    print(f"{total - failures}/{total} review_due fixtures behaved as expected")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
