# think-tank

**Structured debate for real decisions.** A skill that runs red/blue/white teams plus an outside perspective through multi-round dialectic on a genuine pending decision, producing an ASCII-framed debate record, a coordinator's ruling, and a CEO verdict — archived as a D-numbered decision record.

Built for [Miao](https://vertciti.com) (Jiahui Miao) — N=1 founder IP infrastructure.

## What it delivers

One complete run produces, in order:

1. `## Opening definition` — The decidable proposition, defined terms, three verdict options (accept / revise / reject).
2. `## Tension network` — Perspective roster (red/blue/white + outside view) with positions.
3. `## Dialectic` — ≥2 rounds: per-perspective arguments + one-line compression + host's core dispute + ASCII framework diagram + next-level question.
4. `## Coordinator's ruling` — McKinsey-pyramid verdict: conclusion, consensus, real disagreements with rulings, red-team rebuttals, numbers, open items.
5. `## CEO verdict & decision record` — D-numbered archive (background / positions / recommendation / verdict / basis / review triggers).

Fatal-flaw pre-check can short-circuit weak propositions before debate begins.

## Quick start

```bash
cd demo
python3 run.py --topic "Your decision here"
# Draft lands in demo/output/decision-draft.md
```

See `demo/README.md` for the minimal runnable slice.

## Governance

- **D15**: The chairman's word is advisory — sound advice executes, unsound advice is rejected on the record.
- **Gate 0**: Every matter must pass the single-theme screen (operating Miao's life) before debate.
- Not for P0 emergencies (execute first, record within 24h).

## Credits

Debate-organization form inspired by roundtable mechanics (original framework author: 李继刚); reimplemented clean-room per D148 — ideas borrowed, no text copied. The think-tank charter (red/blue/white teams, McKinsey method) is our own.

## License

MIT — see [LICENSE](LICENSE).

## Author

**Jiahui Miao** — Founder, [vertciti](https://vertciti.com). Building procurement infrastructure for AI agents. Participates in 3GPP working on 6G core network standards.
