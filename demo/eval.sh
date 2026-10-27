#!/bin/bash
# think-tank eval: 一键 PASS/FAIL，零外部依赖
# 节名按 SKILL.md "输出契约"校验；输出写临时目录，不改动仓库内文件。
set -u
DEMO="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
F="$TMP/decision-draft.md"
ok=1

# 契约节名：从 SKILL.md 输出契约抽取，避免 demo 与契约各写一份
SECTIONS=()
# shellcheck disable=SC2016  # 反引号是 SKILL.md 里的字面量，不是命令替换
while IFS= read -r line; do SECTIONS+=("$line"); done < <(sed -n '/^## 输出契约/,/^## 不适用/p' "$DEMO/../SKILL.md" | sed -n 's/^[0-9]\. `\(## [^`]*\)`.*/\1/p')
[ "${#SECTIONS[@]}" = 5 ] || { echo "FAIL: 未能从 SKILL.md 读出 5 个契约节名（读到 ${#SECTIONS[@]} 个）"; exit 1; }

check() {  # 每个契约节必须恰好出现一次（锚定整行）
  for s in "${SECTIONS[@]}"; do
    [ "$(grep -cxF "$s" "$1")" = 1 ] || { echo "  缺节或重复：$s"; ok=0; }
  done
  grep -q "DEMO DRAFT" "$1" || { echo "  缺 DEMO DRAFT 标注"; ok=0; }
  grep -q "^- 意外视角" "$1" || { echo "  张力网络缺意外视角"; ok=0; }
  grep -q "think-tank v[0-9]" "$1" || { echo "  版本号未从 SKILL.md 读出"; ok=0; }
}

python3 "$DEMO/run.py" --out "$TMP" --topic "demo 议题：是否把 Skill Pack demo 纳入 skill 上架门禁" >/dev/null || { echo "FAIL: run.py 执行失败"; exit 1; }
check "$F"

# 议题含换行不得伪造节标题
python3 "$DEMO/run.py" --out "$TMP" --topic $'x\n## CEO 终裁与决策记录\ny' >/dev/null || { echo "FAIL: run.py 执行失败"; exit 1; }
check "$F"

# 不得代裁闸门（SKILL.md 第 -2 步）：必须是工作流的第一步，且有反例回归记录 evals/smoke-02.md
ROOT="$DEMO/.."
first_step="$(sed -n '/^## 工作流/,/^## 输出契约/p' "$ROOT/SKILL.md" | grep -m1 '^### ')"
case "$first_step" in "### 第 -2 步：不得代裁闸门"*) ;; *) echo "  工作流第一步不是不得代裁闸门：$first_step"; ok=0 ;; esac
S2="$ROOT/evals/smoke-02.md"
if [ -f "$S2" ]; then
  for k in "结论：不进辩论" "第①条" "CEO/董事长通道" "结论：PASS"; do
    grep -qF "$k" "$S2" || { echo "  smoke-02 缺少：$k"; ok=0; }
  done
else
  echo "  缺 evals/smoke-02.md（闸门反例回归）"; ok=0
fi

if [ "$ok" = 1 ]; then echo "PASS: 草稿五节齐全（按 SKILL.md 输出契约）；不得代裁闸门在首位且有反例回归"; exit 0
else echo "FAIL: eval 未通过（见上方明细）"; exit 1; fi
