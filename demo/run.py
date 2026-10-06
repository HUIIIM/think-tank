#!/usr/bin/env python3
"""think-tank demo: 输入议题 -> D 编号决策记录草稿骨架（最小可运行切片）。"""
import argparse, os, sys
from datetime import datetime, timezone

DEMO = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(DEMO, "output")
os.makedirs(OUT, exist_ok=True)

ap = argparse.ArgumentParser()
ap.add_argument("--topic", required=True, help="待决策议题（一句话）")
a = ap.parse_args()

draft = f"""# 决策记录草稿 [DEMO DRAFT·不进正式决策日志]

- 议题：{a.topic}
- 时间：{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
- 流程：think-tank v1.1（demo 级：单轮骨架）

## 开场定义（前置关）
- 命题是否真实待决策：[过/不过＋一句话证据]
- 决策权边界：本议题终裁权在 [谁]，硬保留事项 [有/无]

## 张力网络
- 红队：[激进立场一句话]
- 蓝队：[稳健立场一句话]
- 白队：[综合视角一句话]

## 辩证过程（第 1 轮）
- 红队 [陈述]：…
- 蓝队 [质疑/反驳]：…
- 白队 [综合]：…
- 主持人争议点：…
- ASCII 框架图：（按争议选光谱/矩阵/环路/树）

## 总协调建议
- 建议：[接/改/驳＋一句话依据]

## 终裁（待 CEO）
- [未终裁]
"""
p = os.path.join(OUT, "decision-draft.md")
open(p, "w", encoding="utf-8").write(draft)
print("draft 已生成：", p)
