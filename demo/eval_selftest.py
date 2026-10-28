#!/usr/bin/env python3
"""demo/eval.sh 的自测：在临时副本上改坏受保护文本，eval 必须 FAIL；未改动与 CRLF 副本必须 PASS。"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COPY = ["SKILL.md", "references", "evals", "demo"]
CRLF_FILES = ["SKILL.md", "references/three-teams.md", "evals/smoke-02.md"]

# (名称, 文件, 原文, 替换文本)：每条都必须让 eval FAIL
MUTATIONS = [
    ("闸门正文包进 HTML 注释", "SKILL.md",
     "主持人先判命题是否命中", "<!--\n主持人先判命题是否命中"),
    ("治理铁律去向对调", "SKILL.md",
     "去向：②④ 走法务通道，①③ 走 CEO/董事长通道。", "去向：①③ 走法务通道，②④ 走 CEO/董事长通道。"),
    ("闸门命中改为照常辩论", "SKILL.md",
     '命中 → 直接输出"不进辩论＋', '命中 → 照常进入辩论；仍可参考"不进辩论＋'),
    ("闸门标题改为可选", "SKILL.md",
     "不得代裁闸门（强制，先于一切步骤）", "不得代裁闸门（可选，主持人酌情跳过）"),
    ("第①条删去以 Miao 名义发送消息", "references/three-teams.md",
     "身份验证/签名、以 Miao 名义发送消息、DNS 修改", "身份验证/签名、DNS 修改"),
    ("three-teams 加更正行", "references/three-teams.md",
     "第 1、3 条走 CEO/董事长通道。", "第 1、3 条走 CEO/董事长通道。\n**更正**：现行为第 1、3 条走法务通道。"),
    ("smoke-02 拦下项改为 ✗", "evals/smoke-02.md",
     "在第 -2 步被拦下：✓", "在第 -2 步被拦下：✗"),
    ("smoke-02 执行方式改为手写", "evals/smoke-02.md",
     "由一个全新的 Claude 会话执行", "由作者会话手写预期输出（未真实执行）"),
    ("闸门行内插入孤立回车", "SKILL.md",
     '命中 → 直接输出"不进辩论', '命中 \r→ 直接输出"不进辩论'),
    ("run.py 契约节名改动", "demo/run.py",
     "## 总协调裁决书", "## 总协调建议"),
    ("run.py 去掉换行处理", "demo/run.py",
     '.decode("utf-8", "replace").split()\n)', '.decode("utf-8", "replace").split(" ")\n)'),
]


def run_eval(tree: Path) -> int:
    r = subprocess.run(["bash", str(tree / "demo" / "eval.sh")], capture_output=True, text=True, cwd="/")
    return r.returncode


def fresh_copy(base: Path) -> Path:
    tree = base / "tree"
    if tree.exists():
        shutil.rmtree(tree)
    tree.mkdir()
    for name in COPY:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, tree / name, ignore=shutil.ignore_patterns("__pycache__", "output"))
        else:
            shutil.copy2(src, tree / name)
    return tree


def main() -> int:
    failures = 0
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)

        tree = fresh_copy(base)
        if run_eval(tree) != 0:
            print("FAIL: 未改动副本没有通过 eval")
            failures += 1

        tree = fresh_copy(base)
        for f in CRLF_FILES:
            p = tree / f
            p.write_bytes(p.read_bytes().replace(b"\n", b"\r\n"))
        if run_eval(tree) != 0:
            print("FAIL: CRLF 副本被误判为 FAIL")
            failures += 1

        for name, f, old, new in MUTATIONS:
            tree = fresh_copy(base)
            p = tree / f
            text = p.read_text(encoding="utf-8")
            if text.count(old) != 1:
                print(f"FAIL: 变异「{name}」的原文在 {f} 中不是恰好一处，自测需要更新")
                failures += 1
                continue
            p.write_text(text.replace(old, new), encoding="utf-8")
            if run_eval(tree) == 0:
                print(f"FAIL: 变异「{name}」没有被 eval 抓到")
                failures += 1

    total = 2 + len(MUTATIONS)
    if failures:
        print(f"eval 自测 FAIL：{failures}/{total} 项不符合预期")
        return 1
    print(f"eval 自测 PASS：{total} 项全部符合预期（未改动与 CRLF 判 PASS，{len(MUTATIONS)} 种变异判 FAIL）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
