#!/bin/bash
# think-tank eval: 一键 PASS/FAIL，零外部依赖
set -u
DEMO="$(cd "$(dirname "$0")" && pwd)"
python3 "$DEMO/run.py" --topic "demo 议题：是否把 Skill Pack demo 纳入 skill 上架门禁" || { echo "FAIL: run.py 执行失败"; exit 1; }
F="$DEMO/output/decision-draft.md"
ok=1
[ -f "$F" ] || ok=0
for s in "开场定义" "张力网络" "辩证过程" "总协调建议" "终裁"; do
  grep -q "$s" "$F" || ok=0
done
grep -q "DEMO DRAFT" "$F" || ok=0
if [ "$ok" = 1 ]; then echo "PASS: 决策记录草稿五节齐全"; exit 0
else echo "FAIL: 草稿缺节"; exit 1; fi
