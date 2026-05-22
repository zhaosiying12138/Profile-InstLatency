# Worker E Contract

Worker: E
Round: 0
LESSON_IDS: NONE

## Owned Paths

- `scripts/analyze.py`
- `scripts/search_model.py`
- `scripts/check_calibration_gate.py`
- `scripts/prepare_llvm_yushuxin_worktree.py`
- `results/common/mismatch_report.md`
- `results/common/experiment_quality.md`
- `results/common/llvm_model_draft.td`
- `results/common/llvm_model_mapping.md`
- `results/common/agentic_flow/**` except existing worker A-D outputs

## Duties

- Implement stdlib-only analysis scaffolding over marker trace JSON files.
- Implement conservative deterministic timing-parameter search placeholder.
- Implement synthetic and real-platform calibration gate checks with distinct stopping rules.
- Implement a dry-run-by-default LLVM `llvmorg-22.1.3` worktree helper.
- Create preliminary Humanize2 capture scaffolding for Round 0.
- Verify with `python3 -m py_compile`, calibration-gate smoke tests, and worktree helper help output.

## Constraints

- Do not edit `.humanize/rlcr/**`.
- Do not run RLCR setup, gate, or cancel commands.
- Do not edit `docs/plan.md`.
- Do not revert or overwrite other workers' edits.
