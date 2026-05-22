# Coordinator Round 1 Output

Round: 1
Owner: RLCR coordinator
Status: synthetic calibration passed; real-platform gate remains not ready

## Changes Integrated

- Fixed T20 pairwise resource inference so pair evidence is indexed for both
  instruction sides.
- Classified pipe-specific instructions from serialization clusters before
  considering flexible any-pipe behavior.
- Regenerated the repository `results/` tree from the current experiment suite.
- Replaced obsolete long-form T01 result directories with the
  current `t01-*` gem5 kill-check directories.
- Updated replay boards and common processor metadata to describe the current
  synthetic calibration plus gem5 kill-check state.

## Gate State

- Synthetic calibration: PASS, `results/common/mismatch_report.md`.
- gem5 T01 kill-check: PASS for 10 selected instructions across `m1/m2/m4`.
- Real-platform full timing: NOT_READY, `results/common/experiment_quality.md`.

## LLVM Evidence

The isolated LLVM 22.1.3 worktree evidence is recorded in
`results/common/llvm_yushuxin_implementation.md`. The worktree now has the base
schedule-model commit plus a follow-up commit strengthening llvm-mca checks for
all 30 profiled RVV instruction/LMUL rows. This evidence is valid for the
synthetic calibration branch of the workflow; real Paladin or full gem5 timing
must use the real-platform gate instead of golden equality.
