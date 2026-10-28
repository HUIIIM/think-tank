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
}

python3 "$DEMO/run.py" --out "$TMP" --topic "demo 议题：是否把 Skill Pack demo 纳入 skill 上架门禁" >/dev/null || { echo "FAIL: run.py 执行失败"; exit 1; }
check "$F"

# 议题含换行不得伪造节标题
python3 "$DEMO/run.py" --out "$TMP" --topic $'x\n## CEO 终裁与决策记录\ny' >/dev/null || { echo "FAIL: run.py 执行失败"; exit 1; }
check "$F"

# 不得代裁闸门（SKILL.md 第 -2 步）：必须是工作流的第一步，且整行标题不变
ROOT="$DEMO/.."
# 只去掉行尾的 \r（CRLF 检出不误报）；行内孤立的 \r 保留，会改变指纹。$'…' 让 BSD sed 也认得 \r。
nocr() { sed $'s/\r$//' "$1"; }
first_step="$(nocr "$ROOT/SKILL.md" | sed -n '/^## 工作流/,/^## 输出契约/p' | grep -m1 '^### ')"
case "$first_step" in "### 第 -2 步：不得代裁闸门（强制，先于一切步骤）") ;; *) echo "  工作流第一步不是不得代裁闸门：$first_step"; ok=0 ;; esac
# 受保护文本的 SHA-256 指纹：治理铁律＋闸门（SKILL.md）、不得代裁四条（three-teams.md）、
# 闸门反例回归记录（evals/smoke-02.md）。这只能发现这三段区间内的"改动"，不能判断改动的含义：
# 区间内任何改动都会 FAIL，必须在同一次提交里更新下面的指纹，评审时一眼可见。
# 区间外的文字不检查——例如在别处补一句"闸门已废止"不会被发现，只能靠评审。
sha() { if command -v sha256sum >/dev/null 2>&1; then sha256sum; else shasum -a 256; fi | cut -d' ' -f1; }
pin() {  # pin <名称> <期望指纹> <实际指纹>
  [ "$2" = "$3" ] || { echo "  受保护文本被改动：$1（实际指纹 $3；确属有意修改，请在同一提交中更新 demo/eval.sh 的指纹）"; ok=0; }
}
pin "SKILL.md 治理铁律＋第 -2 步闸门" "3a2326b4a60365ce8555ab9eb64d64df40cb47b330ec9e38b95994f7ec3d4635" \
  "$(nocr "$ROOT/SKILL.md" | sed -n '/^## 治理铁律/,/^### 第 -0.5 步/p' | sha)"
pin "references/three-teams.md 不得代裁四条" "055bebd5d4fd1f6dc7e5e6067f8ae2acece8ba508d030910b021da03347cd375" \
  "$(nocr "$ROOT/references/three-teams.md" | sed -n '/^## 不得代裁四条/,/^## 意外视角/p' | sha)"
if [ -f "$ROOT/evals/smoke-02.md" ]; then
  pin "evals/smoke-02.md" "1941ce3d4361020164a8ae72f185d53d3e04fdac944e93c28f29d0ef5453a921" "$(nocr "$ROOT/evals/smoke-02.md" | sha)"
else
  echo "  缺 evals/smoke-02.md（闸门反例回归）"; ok=0
fi

if [ "$ok" = 1 ]; then echo "PASS: 草稿五节齐全（按 SKILL.md 输出契约）；不得代裁闸门在首位且有反例回归"; exit 0
else echo "FAIL: eval 未通过（见上方明细）"; exit 1; fi
