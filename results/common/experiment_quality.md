# Experiment Quality Report

Status: preliminary scaffold.
Mode: real_platform_profile
Gate status: NOT_READY

This report is initialized before real platform profiling data exists. It records
the real-platform gate vocabulary so later runs do not inherit the synthetic
golden-value loop by accident.

## Coverage

Coverage is currently zero because no real platform traces have been collected.
The complete first-version coverage target is the 10 non-memory RVV instruction
set across `e32,m1`, `e32,m2`, and `e32,m4`, with LLVM-facing fields either
inferred with evidence, assumed with justification, or marked non-identifiable.

## Stability

No repeated measurements are available yet. Later reports must record repeat
counts, tolerance, and unstable experiment IDs before any real-platform stop
decision is proposed.

## Confidence

Confidence is preliminary and no LLVM-facing schedule field is claimed here.
For real platform profiling, confidence must be based on evidence links,
template coverage, repeated-run stability, and resolved conflicts.

## Assumptions

- The assumed machine is in-order, dual issue, no ROB, with two RVV pipelines.
- Timestamp markers are expected to be zero-cost simulator annotations in the
  synthetic flow; hardware migration needs separate validation.
- Physical writeback latency is not independently claimed unless the platform
  exposes evidence for it.
- Real platform mode does not use golden equality as an exit condition.

## Human Approval

Human approval is required before any LLVM implementation phase starts from real
platform data. The real-platform gate may recommend readiness, but it must not
open the LLVM worktree implementation automatically.
