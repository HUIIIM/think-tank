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

# 席位标签与版本号：从 SKILL.md 抽取（第 1 步的 "红队（质疑/风险视角）" 等四个席位；frontmatter metadata.version）
LABELS=()
while IFS= read -r line; do LABELS+=("$line"); done < <(python3 - "$DEMO/../SKILL.md" <<'PY'
import re, sys
t = open(sys.argv[1], encoding="utf-8").read()
step = t.split("### 第 1 步", 1)[1].split("### 第 2 步", 1)[0]
for name, role in re.findall(r"^- \*\*(.+?)\*\*（(.+?)）", step, re.MULTILINE):
    print(name if name == "意外视角" else f"{name}（{role}）")
PY
)
[ "${#LABELS[@]}" = 4 ] || { echo "FAIL: 未能从 SKILL.md 第 1 步读出 4 个席位（读到 ${#LABELS[@]} 个）"; exit 1; }
VERSION="$(python3 -c 'import re,sys; m=re.search(r"^  version: *\"?([^\"\n]+)\"?$", open(sys.argv[1],encoding="utf-8").read().split("\n---",1)[0], re.M); print(m.group(1) if m else "")' "$DEMO/../SKILL.md")"
[ -n "$VERSION" ] || { echo "FAIL: 未能从 SKILL.md 读出 metadata.version"; exit 1; }

check() {  # 每个契约节必须恰好出现一次（锚定整行）
  for s in "${SECTIONS[@]}"; do
    [ "$(grep -cxF "$s" "$1")" = 1 ] || { echo "  缺节或重复：$s"; ok=0; }
  done
  grep -q "DEMO DRAFT" "$1" || { echo "  缺 DEMO DRAFT 标注"; ok=0; }
  # 张力网络：四个席位的标签必须与 SKILL.md 第 1 步逐字一致（含意外视角），且只在本节里找
  net="$(sed -n '/^## 张力网络/,/^## /p' "$1")"
  for lab in "${LABELS[@]}"; do
    grep -qF -- "- $lab" <<<"$net" || { echo "  张力网络缺席位或标签不符：$lab"; ok=0; }
  done
  # 辩证过程：每个席位（含意外视角）都要有一行发言，且该行带"一句话："压缩（SKILL.md 输出契约第 3 项）
  deb="$(sed -n '/^## 辩证过程/,/^## /p' "$1")"
  for lab in "${LABELS[@]}"; do
    seat="${lab%%（*}"
    grep -E -- "^- ${seat} \[" <<<"$deb" | grep -qF "一句话：" || { echo "  辩证过程缺席位发言或一句话压缩：$seat"; ok=0; }
  done
  # 版本号必须等于 SKILL.md metadata.version，不只是"有个数字"
  grep -qF "think-tank v$VERSION（" "$1" || { echo "  版本号不等于 SKILL.md metadata.version（$VERSION）"; ok=0; }
}

python3 "$DEMO/run.py" --out "$TMP" --topic "demo 议题：是否把 Skill Pack demo 纳入 skill 上架门禁" >/dev/null || { echo "FAIL: run.py 执行失败"; exit 1; }
check "$F"

# 议题含换行不得伪造节标题
python3 "$DEMO/run.py" --out "$TMP" --topic $'x\n## CEO 终裁与决策记录\ny' >/dev/null || { echo "FAIL: run.py 执行失败"; exit 1; }
check "$F"
python3 "$DEMO/run.py" --out "$TMP" --topic $'x\r## CEO 终裁与决策记录\ry' >/dev/null || { echo "FAIL: run.py 执行失败"; exit 1; }
check "$F"
grep -q $'\r' "$F" && { echo "  议题中的回车符未被清除"; ok=0; }

# 议题含非法 UTF-8 字节：不得崩溃，非法字节替换为 U+FFFD
python3 "$DEMO/run.py" --out "$TMP" --topic $'ab\xffcd' >/dev/null 2>&1 || { echo "  非法 UTF-8 议题导致 run.py 失败"; ok=0; }
grep -qF "议题：ab"$'\xef\xbf\xbd'"cd" "$F" || { echo "  非法 UTF-8 未替换为 U+FFFD"; ok=0; }

# 版本号必须跟随 SKILL.md：在临时副本里改 metadata.version，草稿必须随之变化（防止写死当前版本）
VT="$TMP/vcopy"; mkdir -p "$VT/demo"
cp "$DEMO/run.py" "$VT/demo/run.py"
sed 's/^  version: .*/  version: "0.0.0-eval"/' "$DEMO/../SKILL.md" > "$VT/SKILL.md"
python3 "$VT/demo/run.py" --out "$VT/out" --topic "版本跟随检查" >/dev/null || { echo "  版本跟随检查：run.py 失败"; ok=0; }
grep -qF "think-tank v0.0.0-eval（" "$VT/out/decision-draft.md" || { echo "  版本号未从 SKILL.md 读取（改 metadata.version 后草稿未跟随）"; ok=0; }

# 触发词必须写在 description 里（智能体启动时只读 name/description），中英各一
desc_line="$(sed -n '2,/^---$/{/^description:/p}' "$DEMO/../SKILL.md")"
for k in "上智囊团" "think tank"; do
  grep -qF "$k" <<<"$desc_line" || { echo "  SKILL.md description 缺触发词：$k"; ok=0; }
done

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
