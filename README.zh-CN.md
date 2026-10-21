![think-tank](docs/assets/social-preview.png)

# think-tank · 智囊团

[English](README.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.1-blue.svg)](SKILL.md)

**别再只在脑子里做决定。把一个真实的待决事项放进结构化的红/蓝/白队辩论——走出来时，你手里是一份经得起推敲的 D 编号决策记录。**

[官网](https://vertciti.com) · [快速开始](#快速开始) · [它做什么](#它做什么) · [诚实约定](#诚实约定) · [测试实证](#测试实证) · [Demo](#demo) · [FAQ](#faq)

> think-tank 是 vertciti 为创始人自用的技能工具。状态：🟡 建设中（数据截至 2026-10-21）。

大多数 AI “建议”只是一个礼貌的声音在附和你。think-tank 是一个 [Vertciti Skill Pack](https://vertciti.com)，它针对一个真实决策运行真正的多轮辩证：三支立场对立的队伍加一个外部视角、压缩过的论点、协调人的裁定，以及一份 CEO 结论——全部归档为带编号的决策记录。

为 [Miao](https://vertciti.com)（Jiahui Miao）而建——N=1 创始人 IP 基础设施。

## 快速开始
```bash
cd demo
python3 run.py --topic "Your decision here"
# Draft lands in demo/output/decision-draft.md
```

见 `demo/README.md` 了解最小可运行切片。

## 它做什么

### 它解决的真实问题
独自做的大决策会坍缩成创始人的第一直觉。think-tank 迫使决策穿过对抗式结构：每个视角都必须既攻又守，每个论点都要被压缩成一行，让空话无处藏身；薄弱的提案可以在浪费一场辩论之前，就被致命缺陷预检杀掉。

### 它交付什么
喂给它**一个真实的待决事项**（不是抽象话题，不是练习题），外加背景材料。一次运行按顺序产出：

1. `Opening definition` —— 可裁定的提案、术语定义、三个结论选项（接受 / 修订 / 拒绝）。
2. `Tension network` —— 视角名单（红 / 蓝 / 白队 + 外部视角）及各自陈述的立场。
3. `Dialectic` —— ≥2 轮：各视角论点 + 一行压缩 + 主持人的核心争点 + ASCII 框架图 + 下一层问题。
4. `Coordinator's ruling` —— McKinsey 金字塔式裁定：结论、共识、附裁定的真实分歧、红队反驳、数字、未决事项。
5. `CEO verdict & decision record` —— D 编号归档（背景 / 立场 / 建议 / 结论 / 依据 / 复查触发条件）。

致命缺陷预检可以在辩论开始前短路掉薄弱提案——坏主意不配仪式。

### 何时使用
| 场景 | 产出 |
|---|---|
| “我们要不要采用这个机制/路线/投资？” | 附记录依据的接受 / 修订 / 拒绝结论 |
| 路线图取舍（A 对 B，两者都想要） | 结构化论点 + 一行压缩，没有含糊其辞 |
| 团队之间的跨域争议 | 张力网络，让每个立场的逻辑显形 |
| 尽早杀掉薄弱提案 | 致命缺陷预检，不搞仪式 |

### 它如何运行（是结构，不是装饰）
```
Input: decision statement + background material
  ↓  Gate 0 — single-theme screen (must serve the operating theme)
  ↓  Fatal-flaw pre-check (weak propositions killed here)
  ↓  Opening definition → Tension network
  ↓  Dialectic rounds (≥2, each with ASCII framework diagram)
  ↓  Coordinator's ruling (McKinsey pyramid)
  ↓  CEO verdict → D-numbered decision record
```

### 仓库结构
```
think-tank/
  SKILL.md      # the skill itself: full debate protocol, input/output contracts
  demo/         # 30-second runnable slice → demo/output/decision-draft.md
  references/   # think-tank charter (red/blue/white teams, McKinsey method)
  evals/        # smoke evaluation with a real dry-run record
``` demo 输出包含一个完整的工作示例（`demo/output/decision-draft.md`），以及 `evals/smoke-01.md` 中的一份自测记录。

## Demo
仓库内附带一次完整的工作运行：

- `demo/output/decision-draft.md` —— 一次真实 dry-run 的完整辩论记录（开场定义 → 带 ASCII 框架图的辩证 → 协调人裁定 → CEO 结论）
- `evals/smoke-01.md` —— 自测记录：执行器在一个真实待决事项（“trust-rule 式 lasting allow 机制是否排进开发计划”）上跑完整个五节流程，按标准评级 pass/fail

> 完整运行录像/截图：待补（占位）——逐步运行实录在计划中；上面的工作输出文件已经是真实且可运行的。

状态：⚪ 计划中 — Full run-through recording/screenshot（见上行占位说明）。

## 治理
- **D15**：董事长的话是建议性质——合理的建议执行，不合理的建议驳回并留痕。
- **Gate 0**：每个事项在辩论前都必须通过单一主题筛查（运营 Miao 的人生）。
- 不适用于 P0 紧急事件（先执行，24h 内补记录）。

## 路线图
- 带实录捕获的完整辩论运行 dry-run harness（计划中，见 `evals/`）。
- 决策记录归档索引（按话题/结论跨 D 编号检索）。
- D148 洁净室原则适用于所有未来修订：重实现想法，绝不复制文本。

状态：⚪ 计划中 — 本节条目均为 planned。

## 诚实约定
- 每个数字标注来源与抓取时间；抓不到的标“需手动补”，绝不编数。
- Toy 话题在 `demo/` 里能跑，但技能的约定很明确：生产环境只接受真实待决事项。抽象练习题不给结论——整个要点就在于结论会被归档、有人认领。
- 不适用于 P0 紧急事件（先执行，24h 内补记录）。
- 输出为辅助结论，不构成投资、法律或税务建议。

## 测试实证
| 指标 | 数字 | 来源 · 数据截至 |
|---|---|---|
| demo eval | PASS：决策记录草稿五节齐全 | `bash demo/eval.sh` 实跑 · 2026-10-21 |
| quickstart | 草稿落在 demo/output/decision-draft.md | `python3 run.py --topic "Your decision here"`（demo/）实跑 · 2026-10-21 |
| evals/smoke-01.md | 自测记录（五节流程 dry-run） | 仓内文件 `evals/smoke-01.md` · 2026-10-21 核对 |

## FAQ
**我需要一个“真实”决策，还是可以用 toy 话题测试？**
Toy 话题在 `demo/` 里能跑，但技能的约定很明确：生产环境只接受真实待决事项。抽象练习题不给结论——整个要点就在于结论会被归档、有人认领。

**“CEO 结论”是给谁的？**
给决策负责人。技能负责组织辩论；最终拍板由人（或你的运营代理）做出，D 编号记录证明当时考虑过什么。

**为什么是四个视角？**
红队攻击、蓝队建设、白队仲裁、外部视角打破框架。三个视角足够产生分歧；四个视角才能让盲点浮现。

**这能替代紧急事件响应吗？**
不能。不适用于 P0 紧急事件——先执行，24h 内补记录。辩论适合能从 2 小时结构中受益的决策，不适合需要 2 分钟行动的场面。

## 参与贡献
欢迎 Issues 和 PRs。保持证据导向：关于辩论质量的主张需要在 `evals/` 里有一次工作运行佐证，不要形容词。

## 致谢
辩论组织形式受圆桌机制启发（原始框架作者：李继刚）；按 D148 洁净室重实现——借鉴想法，未复制文本。think-tank 章程（红/蓝/白队、McKinsey 方法）是我们自己的。

## 关于 vertciti
vertciti 把全部资源用来运营一个人的人生：创始人苗家辉。官网 [vertciti.com](https://vertciti.com) · 仿冒预警：vertciti 从未发行任何代币。

**Jiahui Miao** —— [vertciti](https://vertciti.com) 创始人。正在构建 N=1 个人 AI 基础设施。参与 3GPP，从事 6G 核心网标准工作。

## 许可证
| 模块 | 许可证 | 白话含义 |
|---|---|---|
| 全部文件 | MIT | 可商用、可修改、需署名 |

见 [LICENSE](LICENSE)。

MIT · 运营主体 VERTCITY LLC
