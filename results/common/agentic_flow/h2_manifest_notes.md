# Humanize2 Manifest Notes

Status: Round 1 capture after synthetic calibration and gem5 kill-check.

This tree mirrors the Humanize2 concepts in `docs/plan.md` without depending on
an available Humanize2 hub. It records enough structure for an empty-context
session to replay the RLCR workflow with plain scripts, then map the same
control flow into executable Humanize2 primitives.

Current mode labels:

- `synthetic_calibration`: allowed to use configured cmodel ground truth for
  mismatch repair.
- `real_platform_profile`: must stop on coverage, stability, confidence,
  documented assumptions, conflict resolution, and human approval.

Current gate state:

- Synthetic calibration: pass, see `results/common/mismatch_report.md`.
- gem5 T01 kill-check: pass, see `results/common/experiments/t01-*/trace.json`.
- Real-platform full timing: not ready, see `results/common/experiment_quality.md`.
