#!/usr/bin/env python3
"""Fixtures for scripts/check_parity.py (issue #35).

Each case builds a small repo in a temporary directory from the real SKILL.md / SKILL.zh.md /
README.md / README.zh.md, applies one edit, runs the checker and compares its exit status with
the expected one; the output must also contain the expected reason, so a case cannot pass
because of some other mismatch. A last case runs it on the repository itself. Exit status is non-zero if any
expectation fails.
"""

import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "check_parity.py"
FILES = ("SKILL.md", "SKILL.zh.md", "README.md", "README.zh.md")

Edit = Callable[[Path], None]


def append(name: str, text: str) -> Edit:
    def run(d: Path) -> None:
        p = d / name
        p.write_text(p.read_text(encoding="utf-8") + text, encoding="utf-8")
    return run


def replace(name: str, old: str, new: str) -> Edit:
    def run(d: Path) -> None:
        p = d / name
        s = p.read_text(encoding="utf-8")
        assert old in s, (name, old)
        p.write_text(s.replace(old, new, 1), encoding="utf-8")
    return run


def remove(name: str) -> Edit:
    def run(d: Path) -> None:
        (d / name).unlink()
    return run


def both(*edits: Edit) -> Edit:
    def run(d: Path) -> None:
        for e in edits:
            e(d)
    return run


def noop(d: Path) -> None:
    pass


M = "<!-- 正文开始：以下与 SKILL.md 正文（frontmatter 之后）逐字相同，由 scripts/check_parity.py 校验 -->"


def crlf(name: str) -> Edit:
    def run(d: Path) -> None:
        p = d / name
        p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
    return run


# name -> (edit, expected exit status, text the output must contain)
CASES: dict[str, tuple[Edit, int, str]] = {
    "unchanged": (noop, 0, "通过"),
    "SKILL.md body changed alone": (replace("SKILL.md", "## 工作流", "## 工作流程"), 1, "SKILL.zh.md 正文与 SKILL.md 不一致"),
    "SKILL.zh.md body changed alone": (replace("SKILL.zh.md", "## 工作流", "## 工作流程"), 1, "SKILL.zh.md 正文与 SKILL.md 不一致"),
    "SKILL body changed in both": (both(replace("SKILL.md", "## 工作流", "## 工作流程"), replace("SKILL.zh.md", "## 工作流", "## 工作流程")), 0, "通过"),
    "SKILL.md frontmatter changed only": (replace("SKILL.md", 'version: "', 'version: "9'), 0, "通过"),
    "SKILL.zh.md note changed only": (replace("SKILL.zh.md", "English readers", "Readers"), 0, "通过"),
    "SKILL.zh.md trailing line added": (append("SKILL.zh.md", "多一行\n"), 1, "SKILL.zh.md 正文与 SKILL.md 不一致"),
    "SKILL.zh.md marker missing": (replace("SKILL.zh.md", "<!-- 正文开始", "<!-- 开始"), 1, "正文开始标记"),
    "SKILL.zh.md marker twice, next to the first": (replace("SKILL.zh.md", M, M + "\n" + M), 1, "正文开始标记"),
    "SKILL.md without frontmatter": (replace("SKILL.md", "---\nname:", "name:"), 1, "没有 YAML frontmatter"),
    "SKILL.zh.md with CRLF line endings": (crlf("SKILL.zh.md"), 0, "通过"),
    "README.zh.md with CRLF line endings": (crlf("README.zh.md"), 0, "通过"),
    "README section added in English only": (append("README.md", "\n## Extra\n\ntext\n"), 1, "标题层级序列"),
    "README section added in both": (both(append("README.md", "\n## Extra\n\ntext\n"), append("README.zh.md", "\n## 附加\n\n文字\n")), 0, "通过"),
    "README heading level differs": (replace("README.zh.md", "## 致谢", "### 致谢"), 1, "标题层级序列"),
    "README heading with closing hashes still counts": (replace("README.zh.md", "## 致谢", "## 致谢 ##"), 0, "通过"),
    "README table row added in Chinese only": (replace("README.zh.md", "| 类型 |", "| 多一行 | x |\n| 类型 |"), 1, "表格行数"),
    "README code block added in English only": (append("README.md", "\n```\nx\n```\n"), 1, "代码块数"),
    "README tilde code block added in English only": (append("README.md", "\n~~~\nx\n~~~\n"), 1, "代码块数"),
    "heading inside a code block is ignored": (both(append("README.md", "\n```\n## not a heading\n```\n"), append("README.zh.md", "\n```\n代码\n```\n")), 0, "通过"),
    "README list item dropped in Chinese": (replace("README.zh.md", "- demo 输出是骨架，不是完整辩论。\n", ""), 1, "列表项数"),
    "README inline code changed in Chinese": (replace("README.zh.md", "`demo/eval_selftest.py`", "`demo/eval_self.py`"), 1, "行内代码"),
    "README link target changed in Chinese": (replace("README.zh.md", "[LICENSE](LICENSE)", "[LICENSE](LICENCE)"), 1, "链接目标"),
    "README in-page anchor differs (ignored)": (replace("README.zh.md", "(#安全)", "(#安全与报告)"), 0, "通过"),
    "README.zh.md missing": (remove("README.zh.md"), 1, "无法读取"),
    "SKILL.zh.md missing": (remove("SKILL.zh.md"), 1, "无法读取"),
}


def run(root: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(SCRIPT), str(root)], capture_output=True, text=True)
    return r.returncode, r.stdout


def main() -> int:
    failed = 0
    for name, (edit, expected, text) in CASES.items():
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            for f in FILES:
                shutil.copy(ROOT / f, d / f)
            edit(d)
            got, out = run(d)
        ok = got == expected and text in out
        failed += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {name}: exit {got}, expected {expected}" + ("" if text in out else f"; output lacks {text!r}: {out.strip()}"))
    got, out = run(ROOT)
    failed += got != 0
    print(f"{'ok  ' if got == 0 else 'FAIL'} repository itself: exit {got}, expected 0")
    total = len(CASES) + 1
    print(f"check_parity 夹具：{total - failed}/{total} 符合预期")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
