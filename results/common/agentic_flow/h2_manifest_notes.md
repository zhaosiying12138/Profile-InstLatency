# Humanize2 Manifest Notes

Status: preliminary Round 0 capture.

This tree mirrors the Humanize2 concepts in `docs/plan.md` without depending on
an available Humanize2 hub. It records enough structure for an empty-context
session to replay the RLCR workflow with plain scripts first, then replace the
draft cartridge nodes with executable Humanize2 primitives as the workflow
stabilizes.

Current mode labels:

- `synthetic_calibration`: allowed to use configured cmodel ground truth for
  mismatch repair.
- `real_platform_profile`: must stop on coverage, stability, confidence,
  documented assumptions, conflict resolution, and human approval.
