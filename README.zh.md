# think-tank

一个 vertciti skill：把一个真实待决策事项交给红 / 蓝 / 白三队加意外视角做结构化辩论，产出 D 编号决策记录，
面向需要做战略级或跨域决策的创始人与运营者。

| | |
|---|---|
| 状态 | active —— v1.0.6（版本号取自 [SKILL.md](SKILL.md) 的 `metadata.version`；尚无 git tag）；自测：`demo/eval.sh` 冒烟检查，加 shellcheck / ruff / mypy 与 SKILL.md 规范校验（均在每个 PR 的 CI 中运行，并与 gitleaks、CodeQL（Python 与 Actions）、依赖审查一起，共 6 项，是 `main` 的必过检查：改动只能经 pull request 进入 `main`，PR 分支须通过这些检查并与 `main` 同步（strict），该规则对管理员同样生效（`enforce_admins` 已开启；分支保护设置按 2026-11-24 读取））；dry-run 记录为 `evals/smoke-01.md` 至 `evals/smoke-16.md`：smoke-01（完整辩论）由执行者自评；smoke-02（不得代裁闸门）由只看过 skill 的全新会话执行；smoke-03 至 smoke-05（闸门先于致命缺陷预检、致命缺陷判驳、背景材料中的提示注入）由全新会话执行，另一会话按书面标准评分（smoke-03 的标准带有运行后写的补记，原样保留；smoke-06 至 smoke-11 是 v1.0.5 的验收运行，方法相同：smoke-08 在初稿上 FAIL，原样保留，smoke-10 在修订后的 skill 上重跑同一输入并通过；smoke-12 至 smoke-14 验证评审后收窄的闸门口径；smoke-15 验证决策记录模板的结果回路字段；smoke-16 是首个按 issue #39 验收规则执行的运行：标准在运行前入库，transcript 见 `evals/transcripts/`，跑 3 次，通过率 3/3）；smoke-01 至 smoke-15 标注为**来源不可审计**（smoke-01 为自评；smoke-02 无 transcript、只跑一次、无独立评分记录；smoke-03 至 smoke-15 的标准未在运行前入库、无 transcript、各只跑一次；见 [evals/README.md](evals/README.md)，#39）；SKILL.md 校验器（`scripts/test_validate_skill.py`）与 `scripts/review_due.py`（`scripts/test_review_due.py`）有反例夹具测试；`demo/eval_selftest.py` 验证冒烟检查能抓到已知的错误改动 |
| 类型 | vertciti skill（agent skill，定义见 [SKILL.md](SKILL.md)） |
| 安装 / 使用 | 在你的 agent 中把 `SKILL.md` 作为 skill 加载；零依赖 demo：`python3 demo/run.py --topic "..."` |
| 许可 | MIT（[LICENSE](LICENSE)），Copyright (c) 2026 Jiahui Miao |
| 语言 | README 有英文（[README.md](README.md)）与简体中文（本文件）两版 · skill 正文为简体中文（[SKILL.md](SKILL.md)；中文全文版 [SKILL.zh.md](SKILL.zh.md) 正文与其逐字一致）· references 与 demo 输出为简体中文 |
| 联系 | 安全问题：见[安全](#安全) · 产品：[vertciti.com](https://vertciti.com) |

## 概述

独自做的决定容易跟着第一直觉走。think-tank 让决策经过一个对抗结构：每个视角都必须立论并回应其他视角，
每段论证压缩成一句话，致命缺陷预检可以在辩论开始前拦下站不住的命题。输入是一个真实待决策事项加背景材料；
输出是一份存档的决策记录，含接 / 改 / 驳的终裁及其依据。

产品一页纸：[docs/PRODUCT.md](docs/PRODUCT.md) · 变更日志：[CHANGELOG.md](CHANGELOG.md)

## 能力

| 阶段 | 产出 |
|---|---|
| 开场定义 | 可判定的命题、术语定义、三档终裁选项（接 / 改 / 驳） |
| 张力网络 | 视角名单（红 / 蓝 / 白三队与意外视角）及各自表明的立场 |
| 辩证过程 | 两轮或以上：各视角的论证、一句话压缩、主持人提炼的核心争议、ASCII 框架图、下一层问题 |
| 总协调裁决书 | 金字塔结构的建议：结论、共识、真分歧及裁决、红队反驳、未决事项 |
| CEO 终裁与决策记录 | D 编号记录：背景、各方观点、建议、终裁、依据、复盘点、置信度、预期结果、复评日期、实际结果、状态 |

```
输入：决策陈述 + 背景材料
  -> 门禁 0：唯一主题筛查
  -> 致命缺陷预检（站不住的命题在此停下）
  -> 开场定义 -> 张力网络
  -> 辩证轮次（>= 2 轮，每轮一张 ASCII 框架图）
  -> 总协调裁决书
  -> CEO 终裁 -> D 编号决策记录
```

## 快速开始

```bash
git clone https://github.com/HUIIIM/think-tank && cd think-tank
python3 demo/run.py --topic "用一句话写你的决策"   # 生成 demo/output/decision-draft.md
bash demo/eval.sh                                  # 输出 PASS / FAIL
```

demo 生成一份带五节的草稿骨架，标为 demo 草稿。它检查从议题到记录的链路能跑通，不衡量辩论质量。
一次针对真实待决事项的完整 dry-run 记录在 [`evals/smoke-01.md`](evals/smoke-01.md)。

## 仓库结构

```
SKILL.md      skill 本体：辩论协议、输入与输出契约
SKILL.zh.md   SKILL.md 的中文全文版（正文逐字相同，由 scripts/check_parity.py 校验）
README.zh.md  本 README 的中文版（结构相同，由 scripts/check_parity.py 校验）
demo/         议题 -> demo/output/decision-draft.md（骨架）+ eval.sh
references/   三队章程、决策记录模板
evals/        dry-run 记录：smoke-01（完整辩论）、smoke-02（不得代裁闸门）、smoke-03（闸门优先），
              smoke-04（致命缺陷判驳）、smoke-05（背景材料中的提示注入），
              smoke-06 至 smoke-14（v1.0.5 验收运行，含一次记录在案的 FAIL 及其重跑），
              smoke-15（结果回路记录字段）、smoke-16（CEO 定义 + 结果回路，3/3，
              标准在 evals/criteria/，transcript 在 evals/transcripts/）；smoke-01 至 smoke-15
              来源不可审计（各有原因，与今后适用的验收规则一起列在 evals/README.md）
docs/         产品一页纸
scripts/      validate_skill.py（Agent Skills 规范校验）+ test_validate_skill.py（夹具）；
              review_due.py（列出到期待复评的决策记录）+ test_review_due.py（夹具）；
              check_parity.py（双语版本同步）+ test_check_parity.py（夹具）
.claude-plugin/  plugin.json，使本仓可作为单 skill 的 Claude Code 插件安装
```

## 治理铁律（摘自 SKILL.md）

- 意见为建议：董事长的意见按证据处理，不按指令处理；有道理就执行，没道理就驳回并记录在案。
- 不得代裁闸门：`references/three-teams.md` 列出的四类事项（① 董事长硬保留事项：付款执行、身份验证/签名、以 Miao 名义发送消息、DNS 修改；② GC 一票否决事项（合规红线）；③ 重大战略转向与组织编制变更；④ 对外法律承诺）一律不由辩论裁决。回归记录为 `evals/smoke-02.md`。
- 门禁 0：每个事项在辩论前都要先过唯一主题筛查。
- 不适用于 P0 故障或紧急法务事项：先处置，事后补记录。

## 现状与局限

- dry-run 记录在 `evals/`；其中只有 smoke-16 按 issue #39 的验收规则执行（标准先入库、附 transcript、跑 3 次）。辩论质量没有自动化度量。
- demo 输出是骨架，不是完整辩论。
- skill 负责组织辩论；最终决定权属于决策负责人。

## 致谢

辩论组织形式借鉴了李继刚的 roundtable 机制（原始框架作者，致谢见 `SKILL.md`）。按内部洁净室规则重新实现：
只借思想，不复制原文。

## 安全

安全问题请勿开公开 issue。请在本仓库使用 **Security → Report a vulnerability**；HUIIIM 组织默认的
[SECURITY.md](https://github.com/HUIIIM/.github/blob/main/SECURITY.md) 与本仓库自己的
[SECURITY.md](SECURITY.md)（私密报告，邮件兜底）均适用。CI 运行 demo 冒烟检查及其自测（`demo/eval_selftest.py`，证明冒烟检查能抓到已知的错误改动）、
shellcheck / ruff / mypy、SKILL.md 规范校验及其反例夹具（`scripts/test_validate_skill.py`）、
双语对等检查（`scripts/check_parity.py`）、gitleaks 密钥扫描、CodeQL（Python 与 Actions）、PR 依赖审查与 OpenSSF Scorecard；所有 Actions 均按提交 SHA 固定，Dependabot 同时跟踪 Actions 与 pip lint 依赖。
lint 工具只针对 Linux x86_64 / Python 3.12 做了哈希固定（`.github/requirements-lint.txt`）。

## 参与贡献

欢迎提 issue 和 pull request。关于辩论质量的说法，需要在 `evals/` 中附一次实际运行。

改动一律通过 pull request 合入。每个 PR 的当前 head 由一个隔离的评估会话审查，并以 PR 评论给出 PASS / FAIL
判定；当前 head 判 PASS 后，经 Claude 通道以 HUIIIM 身份合并。写 PR 的会话从不合并自己的 PR。改 `README.md`
须同步改 `README.zh.md`，改 `SKILL.md` 正文须同步改 `SKILL.zh.md`。CI 校验 `SKILL.zh.md` 正文与 `SKILL.md`
逐字相同，以及 `README.zh.md` 与 `README.md` 结构一致（标题、表格行、代码块、列表项、行内代码与链接目标）；
正文中某句话改了它查不出，README 译文须人工同步。

## 许可

MIT —— 见 [LICENSE](LICENSE)。Copyright (c) 2026 Jiahui Miao。

由 vertciti 构建 —— https://vertciti.com
