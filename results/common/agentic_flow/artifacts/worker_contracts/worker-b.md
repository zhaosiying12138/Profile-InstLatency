# Worker B Contract

Worker: B
Round: 0
Backfill source: `artifacts/worker_outputs/worker-b.md`
LESSON_IDS: NONE

## Owned Paths

- `scripts/llvm_sched_extract.py`
- `docs/llvm-sched-model-notes.md`
- `results/common/llvm_field_map.yaml`
- `results/common/agentic_flow/artifacts/worker_outputs/worker-b.md`

## Duties

- Implement read-only LLVM RISC-V schedule extraction.
- Preserve field mapping evidence for the selected RVV instruction set.
- Verify missing-checkout handling and deterministic output generation.

## Constraints

- Do not edit `.humanize/rlcr/**`.
- Do not run unsafe external bitlesson selector commands.
- Do not edit `docs/plan.md`.
- Do not revert or overwrite other workers' edits.
