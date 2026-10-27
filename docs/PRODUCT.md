# think-tank（智囊团辩证决策）— 产品一页纸

> 状态：active · 版本：1.0.2（`SKILL.md` frontmatter；尚无 git tag）· 更新：2026-10-26
> 所属：[vertciti](https://vertciti.com) — 一家公司，一个人生。

## 一句话
决策负责人（首要是 Miao 本人或其运营 agent）用它把一个**真实待决策事项**交给红/蓝/白三队加意外视角做结构化多轮辩论，得到总协调裁决书、CEO 终裁（接/改/驳）和一份可回溯的 编号决策记录。

*English:* A Claude skill that runs a real pending decision through a structured red/blue/white-team debate (plus an outside view) and outputs a coordinator's ruling, a CEO verdict (accept / revise / reject) and a D-numbered decision record.

## 解决什么问题
- 痛点：独自做重大决策时容易滑向第一直觉；普通 AI 建议往往是"一个附和你的声音"（README Overview）。频率与代价：未确认（TBD）。
- 现在的替代做法：在脑中自行权衡，或向单一 AI 对话求建议；缺少对抗结构、论点压缩和存档，事后无法回溯"当时为什么这么选"。

## 给谁
- 首要用户：Miao 本人及其运营 agent（`SKILL.md`："Stake 是 Miao 的人生"）；也可供需要结构化研判战略级/跨域决策的使用者参考。
- 不是给谁：P0 故障/舆情/涉法紧急事项（先执行、24h 内补记录）；纯执行层调度；抽象议题或练笔（`SKILL.md` "不适用清单"）。

## 怎么用（三步）
1. 准备输入：决策陈述 + 背景材料（必须是真实待决策事项）；在 Claude 中说"上智囊团"触发 skill。
2. skill 按 `SKILL.md` 工作流执行：门禁 0 / 致命缺陷预检 → 开场定义 → 张力网络 → ≥2 轮辩证（含一句话压缩与 ASCII 框架图）→ 总协调裁决书。
3. 决策负责人做 CEO 终裁，存档 编号决策记录（模板见 `references/decision-record-template.md`）。

本地 30 秒体验（只生成草稿骨架）：`python3 demo/run.py --topic "你的议题"`，再 `bash demo/eval.sh` 校验 PASS/FAIL。

## 为什么是我们（差异化）
| 维度 | 我们 | 常见替代 |
|---|---|---|
| 输入 | 只接真实待决策事项，输出可执行结论（接/改/驳＋谁做＋何时） | 抽象话题讨论 |
| 结构 | 红/蓝/白三队＋意外视角对抗，每段发言一句话压缩 | 单一声音的建议 |
| 闭环 | 总协调裁决书 + CEO 终裁是流程必经步骤 | 停在"多角度观点" |
| 沉淀 | 编号决策记录，可回溯引用 | 对话结束即丢失 |
| 前置过滤 | 致命缺陷预检可在辩论前直接判"驳" | 无 |

（以上来自 `SKILL.md` "与通用 roundtable 的四点区别"，为设计意图描述，未做对比评测。）

## 证据
- 测试：无单元测试。`demo/eval.sh` 冒烟检查（按 `SKILL.md` 输出契约校验五节齐全，含换行注入用例）由 CI `Eval` 工作流在每个 push/PR 上运行；另有 gitleaks 与 Scorecard 工作流。
- 真实运行：`evals/smoke-01.md` —— 一次真实待决策事项的完整 dry-run 记录（议题："是否把 trust-rule 式 lasting allow 机制排进 10-18 开发计划"），自评结论 PASS，终裁"改"——2026-10-26 复核：该议题命中"不得代裁四条"第 1 条，本不应进辩论，PASS 只证明流程可跑；`demo/output/decision-draft.md` 为 demo 草稿输出。
- 不能证明的：辩论质量与决策质量的提升没有量化评估；smoke-01 为单次自测、由执行者自评；没有运行录屏/截图。

## 边界与风险
- 不做：P0 紧急事项、纯执行层事项、事实不清且无最低证据基线的议题（打回研究）、门禁 0 不过的议题。
- 已知限制：skill 本体是提示词协议（`SKILL.md`），质量依赖执行它的模型；demo 只验证"议题→草稿骨架"链路，不代表真实辩论质量。
- 安全与隐私：仓库代码不联网、不收集数据；`demo/run.py` 只在本地写 `demo/output/decision-draft.md`。实际运行时决策材料进入所用 Claude 环境，其存储与可见范围取决于该环境，未确认（TBD）。安全问题上报见 README `## 安全 / Security`。

## 与其他 vertciti 产品的组合
- 未确认（TBD）。README 将其称为 "Vertciti Skill Pack"；`SKILL.md` 致谢 live-panel-skill（MIT）的思想吸收，但仓库内没有与其他产品组合使用的具体说明。

## 路线图
| 阶段 | 内容 | 退出标准 |
|---|---|---|
| Now | 维持 v1.0.2 协议；补一次命中"不得代裁四条"的反例 dry-run | 未确认（TBD） |
| Next | 完整辩论 dry-run 测试工具，带 transcript 捕获（原 README Roadmap，`2d7bf80` 已删） | 未确认（TBD） |
| Later | 决策记录归档索引：按主题/结论检索 记录编号（原 README Roadmap，`2d7bf80` 已删） | 未确认（TBD） |

所有后续修订遵循 洁净室原则：只借思想，不复制原文。

## 衡量指标
- 北极星：未确认（TBD）。
- 护栏：`demo/eval.sh` 保持 PASS；每次完整运行满足 `SKILL.md` 输出契约（五节齐全，缺一即未完成）；其余未确认（TBD）。
