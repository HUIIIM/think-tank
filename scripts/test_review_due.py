#!/usr/bin/env python3
"""Fixtures for scripts/review_due.py (SOTA VER-2).

Each case writes a small archive to a temporary directory, runs the script with a fixed
--today, and checks the exit status and which records are listed as DUE or ERROR. A last
check keeps the script's field names in step with references/decision-record-template.md.
Exit status is non-zero if any expectation fails.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "review_due.py"
TEMPLATE = ROOT / "references" / "decision-record-template.md"
TODAY = "2026-11-30"
# ERROR messages about a whole file rather than one record
FILE_LEVEL = ("无法读取", "含 Verdict", "有复评日期", "第 ", "代码块或 HTML 注释", "目录无法读取", "符号链接目录", "归档目录中没有", "断开的符号链接", "不是普通文件")


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
    # the archive holds only records, so record fields without a Verdict mean a broken record
    "fields without Verdict": ({"a.md": "## 笔记\n\n- 复评日期：2026-01-01\n"}, [], 0, set(), {"a.md"}),
    "no record fields at all": ({"a.md": "## 笔记\n\n随手记。\n"}, [], 0, set(), set()),
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
    # the three fields must sit directly under the record heading; under a sub-heading they are missing
    "sub-heading after Verdict": (
        {"a.md": record("TT-1").replace("- 复评日期：", "### 三队观点\n\n- 红队：示例。\n- 复评日期：")}, [], 0, set(), {"TT-1", "a.md"}
    ),
    "sub-heading after the fields is fine": ({"a.md": record("TT-1") + "### 三队观点\n\n- 红队：示例。\n"}, [], 0, {"TT-1"}, set()),
    # the record is the deepest heading holding the Verdict, so it is listed under that heading's name
    "sub-heading before Verdict": ({"a.md": record("TT-1").replace("- Verdict：", "### 背景\n\n- Verdict：")}, [], 0, {"背景"}, set()),
    "status after sub-heading": (
        {"a.md": record("TT-1", status="已取代（→ TT-9）").replace("- 实际结果：", "### 结果\n\n- 实际结果：")}, [], 0, set(), {"TT-1"}
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
        [], 0, {"TT-2"}, {"a.md"},
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
        {"a.md": record("TT-1", review=None) + "\n## 附录\n\n- 复评日期：2026-11-30\n"}, [], 0, set(), {"TT-1", "a.md"}
    ),
    "B2: sibling sub-section inside the record": (
        {"a.md": "## TT-2\n- Verdict：改\n### 关联记录\n- 状态：已取代（→ TT-2）\n### 复评\n"
                 "- 复评日期：2026-11-01\n- 实际结果：待复评\n- 状态：已采纳\n"},
        [], 0, set(), {"TT-2", "a.md"},
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
    "B3: result in full-width parentheses": ({"a.md": record("TT-1", result="（待复评）")}, [], 0, {"TT-1"}, set()),
    "B3: result in quotes": ({"a.md": record("TT-1", result="“待复评”")}, [], 0, {"TT-1"}, set()),
    "B3: result after a full-width space": ({"a.md": record("TT-1", result="\u3000待复评")}, [], 0, {"TT-1"}, set()),
    "B3: result 暂无": ({"a.md": record("TT-1", result="暂无")}, [], 0, {"TT-1"}, set()),
    "B3: result TBD": ({"a.md": record("TT-1", result="TBD")}, [], 0, {"TT-1"}, set()),
    "B3: result 未达到 is reviewed": ({"a.md": record("TT-1", result="未达到——更正仍有 1 次")}, [], 0, set(), set()),
    "B3: result 部分达到 is reviewed": ({"a.md": record("TT-1", result="部分达到——TT-3")}, [], 0, set(), set()),
    "B3: bold reviewed result": ({"a.md": record("TT-1", result="**达到**——0 次更正")}, [], 0, set(), set()),
    "B4: status only in a sub-section": (
        {"a.md": record("TT-2").replace("- 状态：已采纳\n", "### 关联记录\n- TT-1：周报周五发\n- 状态：已取代（→ TT-2）\n")},
        [], 0, set(), {"TT-2"},
    ),
    "B4: result only in a sub-section": (
        {"a.md": record("TT-2").replace("- 实际结果：待复评\n", "").replace("- 状态：已采纳\n", "- 状态：已采纳\n### 关联\n- 实际结果：达到——TT-1\n")},
        [], 0, set(), {"TT-2"},
    ),
    "B4: missing status": ({"a.md": record("TT-1").replace("- 状态：已采纳\n", "")}, [], 0, set(), {"TT-1"}),
    "B4: status with a note": ({"a.md": record("TT-1").replace("- 状态：", "- 状态（当前）：")}, [], 0, set(), {"TT-1"}),
    "B4: status in a quote": ({"a.md": record("TT-1").replace("- 状态：", "> - 状态：")}, [], 0, set(), {"TT-1"}),
    "B4: status in a table": ({"a.md": record("TT-1").replace("- 状态：已采纳", "| 状态：已采纳 |")}, [], 0, set(), {"TT-1"}),
    "B4: no-break space after marker": ({"a.md": record("TT-1").replace("- 状态：", "-\xa0状态：")}, [], 0, set(), {"TT-1"}),
    "B4: full-width space before colon": ({"a.md": record("TT-1").replace("- 状态：", "- 状态\u3000：")}, [], 0, set(), {"TT-1"}),
    "setext heading is reported": ({"a.md": record("TT-1") + "\n附录\n===\n"}, [], 0, {"TT-1"}, {"a.md"}),
    "setext dash heading is reported": ({"a.md": record("TT-1") + "\n附录\n---\n"}, [], 0, {"TT-1"}, {"a.md"}),
    "rule after a blank line is fine": ({"a.md": record("TT-1") + "\n---\n"}, [], 0, {"TT-1"}, set()),
    "unclosed HTML comment": ({"a.md": record("TT-1") + "<!--\n注释\n"}, [], 0, {"TT-1"}, {"a.md"}),
    "seven hashes": ({"a.md": record("TT-1") + "####### 太深\n"}, [], 0, {"TT-1"}, {"a.md"}),
    "hash without space inside a record": ({"a.md": record("TT-1") + "#注释\n"}, [], 0, {"TT-1"}, {"a.md"}),
    "upper-case and long extensions": ({"a.MD": record("TT-1"), "b.markdown": record("TT-2")}, [], 0, {"TT-1", "TT-2"}, set()),
    "related-record sub-section is ignored": (
        {"a.md": record("TT-2") + "### 关联记录\n- TT-1：周报周五发\n- 状态：已取代（→ TT-2）\n- 实际结果：达到——TT-0\n"},
        [], 0, {"TT-2"}, set(),
    ),
    "loose status beside a proper one": ({"a.md": record("TT-1") + "> - 状态：已取代（→ TT-9）\n"}, [], 0, set(), {"TT-1"}),
    "table status beside a proper one": ({"a.md": record("TT-1") + "| 状态：已取代 |\n"}, [], 0, set(), {"TT-1"}),
    "boundary: 达到 as a verb": ({"a.md": record("TT-1", result="达到复评日期后再填")}, [], 0, {"TT-1"}, set()),
    "boundary: 未达到 as a verb": ({"a.md": record("TT-1", result="未达到复评日期，暂不填")}, [], 0, {"TT-1"}, set()),
    "boundary: question mark": ({"a.md": record("TT-1", result="达到？待核实")}, [], 0, {"TT-1"}, set()),
    "boundary: checkbox menu": ({"a.md": record("TT-1", result="[ ] 达到 [ ] 未达到 [ ] 部分达到")}, [], 0, {"TT-1"}, set()),
    "boundary: template placeholder": ({"a.md": record("TT-1", result="<达到 / 未达到 / 部分达到——证据>")}, [], 0, {"TT-1"}, set()),
    "boundary: result 达到 alone": ({"a.md": record("TT-1", result="达到")}, [], 0, set(), set()),
    "boundary: 已取代旧流程 is not closed": ({"a.md": record("TT-1", status="已取代旧流程")}, [], 0, {"TT-1"}, set()),
    "boundary: 已撤销旧方案 is not closed": ({"a.md": record("TT-1", status="已撤销旧方案，改为本方案")}, [], 0, {"TT-1"}, set()),
    "boundary: 已取代 with arrow": ({"a.md": record("TT-1", status="已取代 → TT-9")}, [], 0, set(), set()),
    "boundary: 已撤销 alone": ({"a.md": record("TT-1", status="已撤销")}, [], 0, set(), set()),
    "bare ## is reported": ({"a.md": record("TT-1") + "##\n"}, [], 0, {"TT-1"}, {"a.md"}),
    "HTML heading is reported": ({"a.md": record("TT-1") + "<h3>附录</h3>\n"}, [], 0, {"TT-1"}, {"a.md"}),
    "indented sub-item status is left alone": (
        {"a.md": record("TT-1") + "- 执行跟进项：\n  - 状态：已完成\n"}, [], 0, {"TT-1"}, set()
    ),
    "empty archive": ({"notes.txt": "随手记"}, [], 0, set(), {"."}),
    "second record with a bad Verdict": (
        {"a.md": record("TT-2", review="2099-01-01") + "\n" + record("TT-3").replace("- Verdict：", "- 结论：")}, [], 0, set(), {"a.md"}
    ),
    "second record in a quote": (
        {"a.md": record("TT-2", review="2099-01-01") + "\n## TT-3\n" + "".join("> " + ln + "\n" for ln in record("TT-3").splitlines()[1:])},
        [], 0, set(), {"a.md"},
    ),
    "hedged: 达到（待确认）": ({"a.md": record("TT-1", result="达到（待确认）")}, [], 0, {"TT-1"}, set()),
    "hedged: 达到 TBD": ({"a.md": record("TT-1", result="达到 TBD")}, [], 0, {"TT-1"}, set()),
    "hedged: 部分达到（尚未复评）": ({"a.md": record("TT-1", result="部分达到（尚未复评）")}, [], 0, {"TT-1"}, set()),
    "hedged: spaced template menu": ({"a.md": record("TT-1", result="达到 / 未达到 / 部分达到——<证据或记录编号>")}, [], 0, {"TT-1"}, set()),
    "hedged: 已撤销 待确认": ({"a.md": record("TT-1", status="已撤销 待确认")}, [], 0, {"TT-1"}, set()),
    "hedged: 已取代（→ 待定）": ({"a.md": record("TT-1", status="已取代（→ 待定）")}, [], 0, {"TT-1"}, set()),
    "hedged: 已取代 with no target": ({"a.md": record("TT-1", status="已取代 →")}, [], 0, {"TT-1"}, set()),
    "hedged: template status menu": ({"a.md": record("TT-1", status="已取代（→ 新记录编号）/ 已撤销")}, [], 0, {"TT-1"}, set()),
    "hedged: 达到——尚未核实": ({"a.md": record("TT-1", result="达到——尚未核实")}, [], 0, {"TT-1"}, set()),
    "hedged: 已取代（→ 新记录编号）": ({"a.md": record("TT-1", status="已取代（→ 新记录编号）")}, [], 0, {"TT-1"}, set()),
    "hedged: 达到 / 未达到": ({"a.md": record("TT-1", result="达到 / 未达到")}, [], 0, {"TT-1"}, set()),
    "hedged: 达到——未复评": ({"a.md": record("TT-1", result="达到——未复评")}, [], 0, {"TT-1"}, set()),
    "hedged: 达到——<证据>": ({"a.md": record("TT-1", result="达到——<证据>")}, [], 0, {"TT-1"}, set()),
    "hedged: truncated menu 达到 /": ({"a.md": record("TT-1", result="达到 /")}, [], 0, {"TT-1"}, set()),
    "hedged: 达到（或 /部分达到）": ({"a.md": record("TT-1", result="达到（或 /部分达到）")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——证据待补": ({"a.md": record("TT-1", result="达到——证据待补")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——数据待确认": ({"a.md": record("TT-1", result="达到——数据待确认")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——指标待核": ({"a.md": record("TT-1", result="达到——指标待核")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——看起来达到了，待数据确认": ({"a.md": record("TT-1", result="达到——看起来达到了，待数据确认")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——待验证": ({"a.md": record("TT-1", result="达到——待验证")}, [], 0, {"TT-1"}, set()),
    "hedge: 部分达到——待评估": ({"a.md": record("TT-1", result="部分达到——待评估")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——尚待确认": ({"a.md": record("TT-1", result="达到——尚待确认")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——[待补]": ({"a.md": record("TT-1", result="达到——[待补]")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——“待复评”": ({"a.md": record("TT-1", result="达到——“待复评”")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——暂定": ({"a.md": record("TT-1", result="达到——暂定")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——未核实": ({"a.md": record("TT-1", result="达到——未核实")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——尚无数据，尚未": ({"a.md": record("TT-1", result="达到——尚无数据，尚未")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——TBC": ({"a.md": record("TT-1", result="达到——TBC")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——pending": ({"a.md": record("TT-1", result="达到——pending")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——WIP": ({"a.md": record("TT-1", result="达到——WIP")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——占位": ({"a.md": record("TT-1", result="达到——占位")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——xxx": ({"a.md": record("TT-1", result="达到——xxx")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——…": ({"a.md": record("TT-1", result="达到——…")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——？": ({"a.md": record("TT-1", result="达到——？")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到?": ({"a.md": record("TT-1", result="达到?")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——<链接>": ({"a.md": record("TT-1", result="达到——<链接>")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到 或 未达到": ({"a.md": record("TT-1", result="达到 或 未达到")}, [], 0, {"TT-1"}, set()),
    "hedge: 达到——等待确认": ({"a.md": record("TT-1", result="达到——等待确认")}, [], 0, {"TT-1"}, set()),
    "hedge: 已撤销——暂定": ({"a.md": record("TT-1", status="已撤销——暂定")}, [], 0, {"TT-1"}, set()),
    "hedge: 已取代（→ ?）": ({"a.md": record("TT-1", status="已取代（→ ?）")}, [], 0, {"TT-1"}, set()),
    "hedge: 已取代（→ xxx）": ({"a.md": record("TT-1", status="已取代（→ xxx）")}, [], 0, {"TT-1"}, set()),
    "evidence with a query string": ({"a.md": record("TT-1", result="达到——https://bi.example/r?id=7")}, [], 0, set(), set()),
    "evidence with 期待 and 对待": ({"a.md": record("TT-1", result="达到——符合期待，对待客户方式不变")}, [], 0, set(), set()),
    # a whole record quoted under another one is a citation, not an archive entry: not read
    "quoted record under a good one is a citation": (
        {"a.md": record("TT-1", review="2099-01-01") + "### 引用\n> - Verdict：改\n> - 复评日期：2026-11-01\n"}, [], 0, set(), set()
    ),
    "hedge: 达到——数据未确认": ({"a.md": record("TT-1", result="达到——数据未确认")}, [], 0, {"TT-1"}, set()),
    "hedge: truncated 达到 或": ({"a.md": record("TT-1", result="达到 或")}, [], 0, {"TT-1"}, set()),
    "evidence naming a Spending report": ({"a.md": record("TT-1", result="达到——见 Spending 报表")}, [], 0, set(), set()),
    "evidence naming TBDashboard": ({"a.md": record("TT-1", result="达到——见 TBDashboard 看板")}, [], 0, set(), set()),
    "evidence with a URL": ({"a.md": record("TT-1", result="达到——https://bi.example/r/1")}, [], 0, set(), set()),
    "evidence with a path": ({"a.md": record("TT-1", result="达到——打开率 41%，见 ops/weekly 看板")}, [], 0, set(), set()),
    "evidence with a rate": ({"a.md": record("TT-1", result="部分达到——周活 3 次/周")}, [], 0, set(), set()),
    "evidence with 等待": ({"a.md": record("TT-1", result="达到——客户等待时长下降 30%")}, [], 0, set(), set()),
    "evidence with 接待": ({"a.md": record("TT-1", result="未达到——接待量未变")}, [], 0, set(), set()),
    "withdrawn with a slash in the note": ({"a.md": record("TT-1", status="已撤销——见 TT-5 / 会议纪要")}, [], 0, set(), set()),
    "hedged: 达到TBD without a space": ({"a.md": record("TT-1", result="达到——TBD")}, [], 0, {"TT-1"}, set()),
    "hedged: 已取代（→待定） without a space": ({"a.md": record("TT-1", status="已取代（→待定）")}, [], 0, {"TT-1"}, set()),
    "hedged: 达到，待补数据": ({"a.md": record("TT-1", result="达到，待补数据")}, [], 0, {"TT-1"}, set()),
    "review note in the record's own sub-section": (
        {"a.md": record("TT-1", result="达到——0 次更正") + "### 复评记录\n\n- 原复评日期：2026-11-01，已按期复评。\n"}, [], 0, set(), set()
    ),
    "intro under the document title": ({"a.md": "# 决策记录\n\n> 复评日期：以下方字段为准。\n\n" + record("TT-1")}, [], 0, {"TT-1"}, set()),
    "nested broken record under a good one": (
        {"a.md": record("TT-1", review="2099-01-01") + "### TT-3\n- 结论：改\n- 复评日期：2026-01-01\n- 实际结果：待复评\n- 状态：已采纳\n"},
        [], 0, set(), {"a.md"},
    ),
    "second record dated in a table": (
        {"a.md": record("TT-2", review="2099-01-01") + "\n## TT-3\n| 结论 | 改 |\n| 复评日期 | 2026-01-01 |\n"}, [], 0, set(), {"a.md"}
    ),
    "second record dated without a colon": (
        {"a.md": record("TT-2", review="2099-01-01") + "\n## TT-3\n- 结论：改\n- 复评日期 2026-01-01\n"}, [], 0, set(), {"a.md"}
    ),
    "outcome with evidence": ({"a.md": record("TT-1", result="部分达到——见 TT-3 附件")}, [], 0, set(), set()),
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


def run_unprivileged(archive: Path, extra: list[str]) -> subprocess.CompletedProcess[str] | None:
    """Run the script as a user that file permissions apply to: as is when not root, else
    through setpriv as nobody. None when root cannot drop privileges here."""
    prefix: list[str] = []
    if os.geteuid() == 0:
        setpriv = shutil.which("setpriv")
        if not setpriv:
            return None
        prefix = [setpriv, "--reuid=65534", "--regid=65534", "--clear-groups"]
    return subprocess.run(
        [*prefix, sys.executable, str(SCRIPT), str(archive), "--today", TODAY, *extra],
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
        (Path(tmp) / "2025").symlink_to(Path(tmp) / "unmounted")
        os.mkfifo(Path(tmp) / "pipe.md")
        (Path(tmp) / "b.md").write_text(record("TT-1"), encoding="utf-8")
        try:
            r = subprocess.run([sys.executable, str(SCRIPT), tmp, "--today", TODAY], capture_output=True, text=True, timeout=20)
            got = (r.returncode, ids(r.stdout, "DUE"), ids(r.stdout, "ERROR"))
        except subprocess.TimeoutExpired:
            got = (-1, set(), {"hung"})
    ok = got == (0, {"TT-1"}, {"2025", "pipe.md"})
    failures += not ok
    print(f"{'ok ' if ok else 'BAD'} broken directory link and FIFO are errors, not skipped or hung -> {got}")
    with tempfile.TemporaryDirectory() as tmp:
        bad_name = os.fsencode(tmp) + b"/x\xff.md"
        with open(bad_name, "wb") as f:
            f.write(record("TT-1").encode("utf-8"))
        (Path(tmp) / "y.md").write_text(record("TT-2"), encoding="utf-8")
        strict_env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        byte_run = subprocess.run([sys.executable, str(SCRIPT), tmp, "--today", TODAY], capture_output=True, env=strict_env)
    out = byte_run.stdout.decode("utf-8", "replace")
    ok = byte_run.returncode == 0 and out.count("DUE") == 2
    failures += not ok
    print(f"{'ok ' if ok else 'BAD'} non-UTF-8 file name under a strict stdout -> rc {byte_run.returncode}, {out.count('DUE')} DUE")
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "real").mkdir()
        (Path(tmp) / "real" / "a.md").write_text(record("TT-1"), encoding="utf-8")
        (Path(tmp) / "link").symlink_to(Path(tmp) / "real", target_is_directory=True)
        r = run(Path(tmp), [])
    got = (r.returncode, ids(r.stdout, "DUE"), ids(r.stdout, "ERROR"))
    ok = got == (0, {"TT-1"}, {"link"})
    failures += not ok
    print(f"{'ok ' if ok else 'BAD'} symlinked directory is reported, not followed -> {got}")
    # an unreadable directory must be an ERROR, never a silent "nothing due"
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        base.chmod(0o755)
        (base / "ok").mkdir()
        (base / "ok" / "a.md").write_text(record("TT-1", review="2027-01-01"), encoding="utf-8")
        (base / "locked").mkdir()
        (base / "locked" / "b.md").write_text(record("TT-2"), encoding="utf-8")
        for path in (base / "ok", base / "ok" / "a.md", base / "locked" / "b.md"):
            path.chmod(0o755)
        (base / "locked").chmod(0o000)
        sub = run_unprivileged(base, ["--strict"])
        (base / "locked").chmod(0o755)
        (base / "shut").mkdir(mode=0o700)
        (base / "shut" / "c.md").write_text(record("TT-3"), encoding="utf-8")
        (base / "shut").chmod(0o000)
        top = run_unprivileged(base / "shut", ["--strict"])
        (base / "shut").chmod(0o755)
    if sub is None or top is None:
        failures += 1
        print("BAD unreadable directories: running as root and cannot drop privileges (no setpriv)")
    else:
        got = (sub.returncode, ids(sub.stdout, "DUE"), ids(sub.stdout, "ERROR"))
        ok = got == (1, set(), {"locked"})
        failures += not ok
        print(f"{'ok ' if ok else 'BAD'} unreadable sub-directory is an error -> {got}")
        ok = top.returncode == 2
        failures += not ok
        print(f"{'ok ' if ok else 'BAD'} unreadable archive root exits 2 -> {top.returncode}")
    with tempfile.TemporaryDirectory() as tmp:
        r = run(Path(tmp), [])
        bad = subprocess.run([sys.executable, str(SCRIPT), tmp, "--today", "20261130"], capture_output=True, text=True)
    ok = r.returncode == 0 and bad.returncode == 2  # r: an empty archive is an error, but not --strict
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
    total = len(CASES) + 12
    print(f"{total - failures}/{total} review_due fixtures behaved as expected")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
