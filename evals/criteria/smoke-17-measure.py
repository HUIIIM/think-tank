#!/usr/bin/env python3
"""Measurement helper for evals/criteria/smoke-17.md (committed with the criteria, before any run).

Usage: python3 evals/criteria/smoke-17-measure.py <output.md>

Counts, using the run-bounds definition in SKILL.md (字数 = characters after removing all
whitespace):
- total: the whole deliverable, ASCII diagrams included;
- rounds: headings of the form "第 N 轮" (levels 2-4);
- speeches: each block that starts at a line carrying an action tag ([陈述]/[质疑]/[补充]/
  [反驳]/[修正]/[综合]) and ends at the next "一句话：" line, fenced code excluded.
Drafts and host summaries are measured by the grader with the same counting rule.
"""

import re
import sys


def chars(s: str) -> int:
    return len(re.sub(r"\s", "", s))


def main() -> int:
    text = open(sys.argv[1], encoding="utf-8").read()
    nofence = re.sub(r"(?ms)^ {0,3}(`{3,}|~{3,}).*?^ {0,3}\1[ \t]*$", "", text)
    rounds = re.findall(r"(?m)^#{2,4} *第 *(\d+) *轮", text)
    speeches = re.findall(r"(?ms)^[^\n]*\[(?:陈述|质疑|补充|反驳|修正|综合)\][^\n]*\n.*?一句话[:：][^\n]*", nofence)
    lengths = [chars(s) for s in speeches]
    print(f"total_chars={chars(text)}")
    print(f"round_headings={len(rounds)} numbers={rounds}")
    print(f"speeches={len(lengths)} max_chars={max(lengths) if lengths else 0} over_400={sum(n > 400 for n in lengths)}")
    print(f"has_cap_note={'按运行上限执行' in text} has_capped_open_item={'触顶未收敛' in text}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
