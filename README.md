# think-tank

A vertciti skill that runs a real pending decision through a structured red / blue / white-team debate with
an outside perspective and produces a D-numbered decision record, for founders and operators who make
strategic or cross-domain calls.

| | |
|---|---|
| Status | active — v1.0.2 (version from [SKILL.md](SKILL.md); no git tags yet); self-tests: `demo/eval.sh` smoke check (run in CI) and one dry-run in `evals/smoke-01.md`; no unit tests |
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
evals/        smoke evaluation with one dry-run record
docs/         product one-pager
```

## Governance rules (from SKILL.md)

- D15: the chairman's input is treated as evidence, not as an instruction; it is executed when sound and
  rejected on the record when not.
- Non-delegable gate: the four matter types listed in `references/three-teams.md` (e.g. sending messages in the owner's name, payments, DNS) are never decided by the debate.
- Gate 0: every matter passes the single-theme screen before debate.
- Not for P0 incidents or urgent legal matters: act first, record afterwards.

## Status and limitations

- One dry-run evaluation exists; there is no automated measure of debate quality.
- The demo output is a skeleton, not a full debate.
- The skill structures the debate; the final call belongs to the decision owner.

## Credits

The debate-organisation form draws on roundtable mechanics by 李继刚 (original framework author, as credited
in `SKILL.md`). It is reimplemented clean-room under internal rule D148: ideas borrowed, no text copied.

## Security

Do not open a public issue for security problems. Use **Security → Report a vulnerability** on this
repository; the HUIIIM organisation default
[SECURITY.md](https://github.com/HUIIIM/.github/blob/main/SECURITY.md) applies (this repository has no
SECURITY.md of its own). CI runs the demo smoke check, gitleaks secret scanning and OpenSSF Scorecard; all Actions are pinned by commit SHA.

## Contributing

Issues and pull requests are welcome. Claims about debate quality need a worked run in `evals/`.

## Licence

MIT — see [LICENSE](LICENSE). Copyright (c) 2026 Jiahui Miao.

Built by vertciti — https://vertciti.com
