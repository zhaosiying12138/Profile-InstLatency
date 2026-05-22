# Worker A Contract

Worker: A
Round: 0
Backfill source: `artifacts/worker_outputs/worker-a.md`
LESSON_IDS: NONE

## Owned Paths

- `README.md`
- `config/paths.yaml`
- `scripts/check_env.py`
- `results/common/agentic_flow/artifacts/worker_outputs/worker-a.md`

## Duties

- Bootstrap the Phase 0 environment checker.
- Keep `config/paths.yaml` simple enough for stdlib-only parsing.
- Document setup and mode separation in the README.
- Record verification commands and caveats in the worker output.

## Constraints

- Do not edit `.humanize/rlcr/**`.
- Do not run RLCR setup, gate, or cancel commands.
- Do not edit `docs/plan.md`.
- Do not revert or overwrite other workers' edits.
