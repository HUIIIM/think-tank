# Changelog / 变更日志

本文件记录本仓库的所有重要变更，格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。
仓库尚无 git tag，因此暂不划分版本号区块；skill 自身的版本号见 `SKILL.md` frontmatter（当前 `1.0.3`）及其 Changelog 节。

All notable changes to this repository are documented here, following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
There are no git tags yet, so entries are grouped by date under `[Unreleased]`; the skill's own version lives in `SKILL.md` (currently `1.0.3`).

## [Unreleased]

### Added
- `docs/PRODUCT.md` 产品一页纸 / product one-pager.
- `CHANGELOG.md`（本文件 / this file）.
- README：状态行、`## Security`、`## Licence` 节 / status line, Security and Licence sections (README is English-only since `2d7bf80`).
- SKILL.md v1.0.2：第 -2 步"不得代裁闸门"；"意见为建议"规则不覆盖不得代裁四条 / step -2 non-delegable gate; the input-as-evidence rule does not override the four non-delegable matter types.
- CI `Eval` 工作流：每个 PR 和推到 main 的 push 都运行 `demo/eval.sh` / `Eval` workflow runs `demo/eval.sh` on every PR and on pushes to main.
- `Eval` 新增阻断式 lint 作业：shellcheck、ruff、`mypy --strict`；工具按 `.github/requirements-lint.txt` 哈希安装 / blocking lint job (shellcheck, ruff, mypy --strict), tools installed with pinned hashes.
- `evals/smoke-02.md`：不得代裁闸门的反例回归（smoke-01 的议题必须在第 -2 步被拦下），由一个全新会话执行；`demo/eval.sh` 静态检查闸门位于工作流首位且该记录存在 / non-delegable gate regression run; eval checks the gate is the first step and the record exists.
- SKILL.md v1.0.3：闸门移到工作流最前；去向统一为"第 2、4 条走法务通道，第 1、3 条走 CEO/董事长通道"；写清"要不要花钱"可以辩论但只出建议，付款执行属硬保留 / gate moved first; routing unified; spending wording made consistent.

### Changed
- `demo/run.py` 节名对齐 SKILL.md 输出契约（`## 总协调裁决书`、`## CEO 终裁与决策记录`），版本号改为 1.0.2（原写 v1.1），新增 `--out` / demo headings match the SKILL.md output contract; version string fixed; `--out` option.
- `demo/eval.sh` 从 SKILL.md 读取契约节名、输出写临时目录（不再改动仓库文件）、新增换行注入用例 / eval reads contract headings from SKILL.md, writes to a temp dir, adds a newline-injection case.
- 全部 GitHub Actions 按 commit SHA 固定 / all GitHub Actions pinned by commit SHA.
- `evals/smoke-01.md` 加复核注记：该议题命中不得代裁第 1 条，PASS 只证明流程可跑 / review note: the topic hits non-delegable rule 1; the PASS only shows the flow runs.
- `evals/smoke-01.md` 脱敏：直接引语全部改为转述，移除精确时间戳、API 返回字段与内部文件引用（更早的提交历史中仍有原文） / redacted direct quotes, exact timestamps, API field names and internal file references.
- `SKILL.md` 推理外化纪律：逐字英文引文改为转述（洁净室规则：不复制原文），arXiv 编号标注"未核实" / verbatim quote replaced by a paraphrase; arXiv citation marked unverified.

### Removed
- README（`2d7bf80`）删去了 FAQ、场景表、Roadmap 与录屏占位 / README dropped the FAQ, scenario table, Roadmap and recording placeholder.

### Fixed
- `demo/run.py`：议题中的换行被压成空格，用户输入不能再伪造节标题 / newlines in the topic are collapsed so input cannot forge section headings.
- `gitleaks.yml`：在 `permissions` 中补 `pull-requests: read`，避免 gitleaks-action 在 PR 上 403 / add `pull-requests: read` so gitleaks-action does not 403 on PRs.

## 2026-10-22

### Added
- 采用 vertciti 工程基线：`.github/CODEOWNERS`、`.editorconfig`、`.github/dependabot.yml`、gitleaks 密钥扫描与 OpenSSF Scorecard 工作流 / Adopt vertciti engineering baseline: CODEOWNERS, .editorconfig, Dependabot, gitleaks and Scorecard workflows (`9ecb85e`).

## 2026-10-14

### Changed
- README 作者节：将已退役的采购定位替换为 N=1 标准表述 / README Author section: replace retired procurement positioning with the N=1 standard line (`b7766a9`).

## 2026-10-07

### Changed
- README 全面重构：slogan、首屏导航、Demo 节、场景表、FAQ、License 白话表 / README rewrite: slogan hook, top navigation, demo section, scenario table, FAQ, plain-language license table (`6a1cb6a`).

## 2026-10-06

### Added
- 首次公开发布（提交信息标注 v1.0）：`SKILL.md` 辩论协议、`demo/`（`run.py` + `eval.sh`）、`evals/smoke-01.md` dry-run 记录、`references/`（三队章程、决策记录模板）、MIT `LICENSE` / Initial public release (commit labelled v1.0): skill protocol, runnable demo, smoke eval record, references, MIT license (`d13d814`).
