#!/usr/bin/env python3
"""think-tank demo: 输入议题 -> 编号决策记录草稿骨架（最小可运行切片）。"""

import argparse
import os
import re
import sys
from datetime import datetime, timezone

DEMO = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DEMO)


def skill_version() -> str:
    """metadata.version from SKILL.md frontmatter; 'unknown' if absent."""
    try:
        with open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8") as f:
            head = f.read(4000)
    except OSError:
        return "unknown"
    m = re.search(r'^\s*version:\s*"?([0-9][^"\n]*)"?\s*$', head, re.MULTILINE)
    return m.group(1) if m else "unknown"


ap = argparse.ArgumentParser()
ap.add_argument("--topic", required=True, help="待决策议题（一句话）")
ap.add_argument(
    "--out", default=os.path.join(DEMO, "output"), help="输出目录（默认 demo/output）"
)
a = ap.parse_args()

# 议题压成一行：换行会让用户输入伪造出 "## 终裁" 之类的节标题
# 非法 UTF-8 字节（argv 中的代理字符）替换为 U+FFFD，避免写文件时崩溃
topic = " ".join(
    a.topic.encode("utf-8", "surrogateescape").decode("utf-8", "replace").split()
)
if not topic:
    sys.exit("--topic 不能为空")

draft = f"""# 决策记录草稿 [DEMO DRAFT·不进正式决策日志]

- 议题：{topic}
- 时间：{datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")}
- 流程：think-tank v{skill_version()}（demo 级：单轮骨架）

## 开场定义
- 命题是否真实待决策：[过/不过＋一句话证据]
- 不得代裁四条：[未命中 / 命中第 N 条→不进辩论，走原通道]
- 决策权边界：本议题终裁权在 [谁]，硬保留事项 [有/无]

## 张力网络
- 红队（质疑/风险视角）：[一句话立场]
- 蓝队（价值/用户视角）：[一句话立场]
- 白队（工程/执行视角）：[一句话立场]
- 意外视角（[角色，领域之外]）：[一句话立场]

## 辩证过程
### 第 1 轮
- 红队 [陈述]：…　一句话：…
- 蓝队 [质疑/反驳]：…　一句话：…
- 白队 [修正]：…　一句话：…
- 意外视角 [补充]：…　一句话：…
- 主持人争议点：…
- ASCII 框架图：（按争议选光谱/矩阵/环路/树）

## 总协调裁决书
- 建议：[接/改/驳＋一句话依据]

## CEO 终裁与决策记录
- [未终裁]
"""
os.makedirs(a.out, exist_ok=True)
p = os.path.join(a.out, "decision-draft.md")
with open(p, "w", encoding="utf-8") as f:
    f.write(draft)
print("draft 已生成：", p)
