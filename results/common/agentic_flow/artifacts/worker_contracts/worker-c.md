# Worker C Contract

Worker: C
Round: 0
Backfill source: `artifacts/worker_outputs/worker-c.md`
LESSON_IDS: NONE

## Owned Paths

- `scripts/gen_asm.py`
- `templates/rvv_program.s.tpl`
- `experiments/generated/**`
- `results/common/agentic_flow/artifacts/worker_outputs/worker-c.md`

## Duties

- Implement deterministic RVV assembly experiment generation scaffolding.
- Generate marker and kill-check fixtures plus suite metadata.
- Record generator support limits and verification commands.

## Constraints

- Do not edit `.humanize/rlcr/**`.
- Do not run RLCR setup, gate, or cancel commands.
- Do not edit `docs/plan.md`.
- Do not revert or overwrite other workers' edits.
