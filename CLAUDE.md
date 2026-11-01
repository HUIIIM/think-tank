# think-tank

A published skill package: structured red/blue/white-team deliberation
for strategic decisions, producing a decision record. Public, bilingual
editions. Branch protection is on with strict required checks
(gitleaks, lint + typecheck, demo/eval.sh).

## How work happens here

- Direction arrives in-repo: GitHub Issues labeled `jarvis-task`, PR
  review comments, and `CLAUDE.md` / `LOOP.md`. Read both at session start.
- External Claude works on `claude/*` branches and opens PRs; it never
  merges its own PRs. Jarvis reviews and merges.
- Review verdicts exist only as PR comments.

## Working rules

- Bilingual parity is a publish gate: SKILL.md / SKILL.zh.md and
  README.md / README.zh.md ship together, sections aligned.
- Toolchain quirk: `validate_skill.py` requires the checkout directory to
  be named `think-tank`; a differently named clone fails validation for
  path reasons, not content reasons.
