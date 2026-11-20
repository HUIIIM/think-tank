# evals/ 验收口径

本目录存放 skill 的验收运行记录（dry-run，均标 [试运行]，不进正式决策日志）。


> English summary: from 2026-11-20 an acceptance run counts only if (1) its criteria file was committed on its own before any run, (2) a transcript or session link is attached, and (3) each scenario runs at least 3 times and reports a pass rate. Runs that miss any rule are exploratory only. Existing records smoke-03 to smoke-15 are marked *source not auditable*; smoke-01 is self-graded; smoke-02 has no transcript. Record bodies are left unchanged because they are pinned by `demo/eval.sh`.

## 验收三规（中枢裁决 #30 第 5 项，执行单 #39；自 2026-11-20 起适用于所有新的验收运行）

1. **标准文件运行前单独提交**：通过标准与输入原文写成 `evals/criteria/<记录名>.md`，在任何运行之前以单独的提交入库；运行记录引用该提交。
2. **附 transcript 或会话链接**：每次运行的执行会话 transcript（或可公开访问的会话链接）随结果一并入库，评分依据可回查到原始输出。
3. **每个场景至少跑 3 次，报告通过率**：同一输入、同一 skill 版本至少运行 3 次；结论写成"通过率 k/n"，而不是单次 PASS。

不满足这三条的运行只能作为探索性记录，不能作为验收依据。

## 存量记录的来源标注

| 记录 | 状态 |
|---|---|
| smoke-01 | 来源不可审计：执行者自评，无独立评分，无 transcript |
| smoke-02 | 来源不可审计：无 transcript，只跑一次 |
| smoke-03 ～ smoke-14 | **来源不可审计**（中枢裁决 #30 第 5 项）：记录自述"标准运行前写定""全新会话执行"，但标准文件未在运行前入库，没有 transcript 或会话链接，每个输入只跑一次。记录保留原样，不删。 |
| smoke-15 | 来源不可审计：同上（标准文件未在运行前入库；无 transcript；只跑一次） |

记录正文不改动：smoke-02、03、10、12、13 由 `demo/eval.sh` 全文指纹保护，标注只写在本表和各汇总处。
