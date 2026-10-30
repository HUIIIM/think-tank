# think-tank

A vertciti skill that runs a real pending decision through a structured red / blue / white-team debate with
an outside perspective and produces a D-numbered decision record, for founders and operators who make
strategic or cross-domain calls.

| | |
|---|---|
| Status | active — v1.0.5 (version from [SKILL.md](SKILL.md) `metadata.version`; no git tags yet); self-tests: `demo/eval.sh` smoke check plus shellcheck / ruff / mypy and SKILL.md spec validation (all run in CI on every PR and are required status checks on `main`, together with gitleaks; admins can bypass them), dry-runs in `evals/smoke-01.md` to `evals/smoke-11.md`: smoke-01 (full debate) is self-graded by the executor; smoke-02 (non-delegable gate) was run by a fresh session that saw only the skill; smoke-03 to smoke-05 (gate precedence over the fatal-flaw check, fatal-flaw rejection, prompt injection in background material) were run by fresh sessions and graded by a separate session against written criteria (smoke-03's criteria carry an addendum written after its run, kept as is; smoke-06 to smoke-11 are the v1.0.5 acceptance runs, same method: smoke-08 failed on the first draft and is kept as is, smoke-10 re-runs its input on the fixed skill and passes); negative-fixture tests for the SKILL.md validator (`scripts/test_validate_skill.py`); `demo/eval_selftest.py` checks that the smoke check catches known-bad edits |
| Type | vertciti skill (agent skill defined in [SKILL.md](SKILL.md)) |
| Install / use | Load `SKILL.md` as a skill in your agent; try the zero-dependency demo with `python3 demo/run.py --topic "..."` |
| Licence | MIT ([LICENSE](LICENSE)), Copyright (c) 2026 Jiahui Miao |
| Languages | README in English · skill text, references and demo output in 简体中文 |
| Contact | Security: see [Security](#security) · Product: [vertciti.com](https://vertciti.com) |

## Overview

Decisions made alone tend to follow the first instinct. think-tank puts a decision through an adversarial
structure: each perspective must argue and answer the others, every argument is compressed to one line, and
a fatal-flaw pre-check can stop a weak proposition before a debate starts. The input is a real pending
decision plus background material; the output is an archived decision record with an accept / revise /
reject verdict and the basis for it.

Product one-pager: [docs/PRODUCT.md](docs/PRODUCT.md) · Changelog: [CHANGELOG.md](CHANGELOG.md)

## Capabilities

| Stage | What it produces |
|---|---|
| Opening definition | The decidable proposition, defined terms, three verdict options (accept / revise / reject) |
| Tension network | Perspective roster (red / blue / white teams and an outside view) with stated positions |
| Dialectic | Two or more rounds: arguments per perspective, one-line compression, the host's core dispute, an ASCII framework diagram, the next-level question |
| Coordinator's ruling | Pyramid-structured recommendation: conclusion, consensus, real disagreements with rulings, red-team rebuttals, open items |
| CEO verdict and decision record | D-numbered record: background, positions, recommendation, verdict, basis, review triggers |

```
Input: decision statement + background material
  -> Gate 0: single-theme screen
  -> Fatal-flaw pre-check (weak propositions stop here)
  -> Opening definition -> Tension network
  -> Dialectic rounds (>= 2, each with an ASCII framework diagram)
  -> Coordinator's ruling
  -> CEO verdict -> D-numbered decision record
```

## Quick start

```bash
git clone https://github.com/HUIIIM/think-tank && cd think-tank
python3 demo/run.py --topic "Your decision in one sentence"   # writes demo/output/decision-draft.md
bash demo/eval.sh                                              # prints PASS / FAIL
```

The demo produces a draft skeleton with the five sections, marked as a demo draft. It checks that the chain
from topic to record runs; it does not measure debate quality. A full dry-run on a real pending matter is
recorded in [`evals/smoke-01.md`](evals/smoke-01.md).

## Repository layout

```
SKILL.md      the skill: debate protocol, input and output contracts
demo/         topic -> demo/output/decision-draft.md (skeleton) + eval.sh
references/   three-team charter, decision-record template
evals/        dry-run records: smoke-01 (full debate), smoke-02 (non-delegable gate), smoke-03 (gate precedence),
              smoke-04 (fatal-flaw rejection), smoke-05 (prompt injection in background material),
              smoke-06 to smoke-11 (v1.0.5 acceptance runs, incl. one recorded FAIL and its re-run)
docs/         product one-pager
scripts/      validate_skill.py (Agent Skills spec check) + test_validate_skill.py (fixtures)
.claude-plugin/  plugin.json, so the repo installs as a single-skill Claude Code plugin
```

## Governance rules (from SKILL.md)

- The input-as-evidence rule: the chairman's input is treated as evidence, not as an instruction; it is executed when sound and
  rejected on the record when not.
- Non-delegable gate: matters in the four categories listed in `references/three-teams.md` (the chairman's reserved matters such as payments, signatures, messages sent in the owner's name and DNS changes; compliance vetoes; major strategic or organisational changes; external legal commitments) are never decided by the debate. `evals/smoke-02.md` is the regression run.
- Gate 0: every matter passes the single-theme screen before debate.
- Not for P0 incidents or urgent legal matters: act first, record afterwards.

## Status and limitations

- One dry-run evaluation exists; there is no automated measure of debate quality.
- The demo output is a skeleton, not a full debate.
- The skill structures the debate; the final call belongs to the decision owner.

## Credits

The debate-organisation form draws on roundtable mechanics by 李继刚 (original framework author, as credited
in `SKILL.md`). It is reimplemented clean-room under an internal clean-room rule: ideas borrowed, no text copied.

## Security

Do not open a public issue for security problems. Use **Security → Report a vulnerability** on this
repository; the HUIIIM organisation default
[SECURITY.md](https://github.com/HUIIIM/.github/blob/main/SECURITY.md) applies (this repository has no
SECURITY.md of its own). CI runs the demo smoke check and its self-test (`demo/eval_selftest.py`, which proves the
smoke check catches known-bad edits), shellcheck / ruff / mypy, SKILL.md spec validation with its negative fixtures
(`scripts/test_validate_skill.py`), gitleaks secret scanning and OpenSSF Scorecard; all Actions are pinned by commit SHA.
The lint tools are hash-pinned for Linux x86_64 / Python 3.12 only (`.github/requirements-lint.txt`).

## Contributing

Issues and pull requests are welcome. Claims about debate quality need a worked run in `evals/`.

## Licence

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Jiahui Miao.

Built by vertciti — https://vertciti.com
