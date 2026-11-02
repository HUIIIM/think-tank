#!/usr/bin/env python3
"""Fixtures for scripts/review_due.py (SOTA VER-2).

Each case writes a small archive to a temporary directory, runs the script with a fixed
--today, and checks the exit status and which records are listed as DUE or ERROR. A last
check keeps the script's field names in step with references/decision-record-template.md.
Exit status is non-zero if any expectation fails.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "review_due.py"
TEMPLATE = ROOT / "references" / "decision-record-template.md"
TODAY = "2026-11-30"


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
            title = line.split(": ", 1)[1]
            found.add(title.split("（", 1)[0])
    return found


def main() -> int:
    failures = 0
    for name, (files, extra, code, due, errors) in CASES.items():
        with tempfile.TemporaryDirectory() as tmp:
            for rel, text in files.items():
                p = Path(tmp) / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(text.encode("utf-8"))
            r = run(Path(tmp), extra)
        got = (r.returncode, ids(r.stdout, "DUE"), ids(r.stdout, "ERROR"))
        ok = got == (code, due, errors)
        failures += not ok
        print(f"{'ok ' if ok else 'BAD'} {name} -> {got}")
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
    total = len(CASES) + 5
    print(f"{total - failures}/{total} review_due fixtures behaved as expected")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
