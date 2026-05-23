# Humanize2 Manifest Notes

Status: Round 6 capture package for the Round 5 candidate-simulator worker,
after Round 4 real-platform artifact refresh and current `main` commit
`773f27d6`.

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
- Real gem5 checked-in r01/r02 traces: 7190, with 178/178 required groups and
  3595 stable repeat groups.
- Real-platform field status: 150 rows, 111 inferred, 39 non-identifiable, 0
  conflict, 0 insufficient-evidence.
- Real-platform gate: `NOT_READY`, see `results/common/experiment_quality.md`.
  The approval artifact is absent and must not be created without explicit
  user approval tied to current risk IDs and hashes.
- Current Round 5 boundary hashes are `d29e632b...` for inventory,
  `904cca46...` for field status, `d31ef890...` for real search, and
  `6062c76f...` for experiment quality. The older Round 4 review hashes remain
  recorded in replay and events as the review baseline.

Round 5 ownership:

- This worker owns only `results/common/agentic_flow/**`.
- Worker Anscombe owned `scripts/search_model.py`,
  `tests/test_search_model_candidate_sim.py`, generated real-platform outputs,
  common real-platform JSON/Markdown artifacts, and
  `results/*/profile.real_platform.yaml`; current `main` commit `773f27d6`
  is that worker's code/result change.
- Round 5 review accepted the candidate-simulator scope for peer-side T20 and
  short T12 exactness, but requested this missing code-worker capture package
  plus separate AC-16 approval hardening.
- `.humanize/rlcr/**` is read-only for this worker; replay points there for
  prompt/result history.
