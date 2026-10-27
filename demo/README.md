# think-tank demo

最小可运行切片：输入一个议题，输出 编号决策记录草稿骨架。

## 运行
```bash
python3 demo/run.py --topic "你的议题一句话"
bash demo/eval.sh  # 输出 PASS/FAIL；写临时目录，不改仓库文件
```

## 输出
`demo/output/decision-draft.md`（可用 `--out` 改目录）：按 `SKILL.md` 输出契约，开场定义/张力网络/辩证过程/总协调裁决书/CEO 终裁与决策记录五节齐全，
头部标注 `[DEMO DRAFT·不进正式决策日志]`。

## 诚实边界
本 demo 只验证"议题→草稿骨架"链路可运行；真实辩论质量不在 30 秒 demo 范围内，
以 `evals/smoke-01.md` 的完整 dry-run 为准。
