# Changelog / 变更日志

本文件记录本仓库的所有重要变更，格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。
仓库尚无 git tag，因此暂不划分版本号区块；skill 自身的版本号见 `SKILL.md` frontmatter（当前 `1.0.1`）及其 Changelog 节。

All notable changes to this repository are documented here, following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
There are no git tags yet, so entries are grouped by date under `[Unreleased]`; the skill's own version lives in `SKILL.md` (currently `1.0.1`).

## [Unreleased]

### Added
- `docs/PRODUCT.md` 产品一页纸 / product one-pager.
- `CHANGELOG.md`（本文件 / this file）.
- README：状态行、`## 安全 / Security`、双语 `## 许可证 / License` 标题 / status line, Security section, bilingual License heading.

### Fixed
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
