# Round 1 Summary

## Work Completed

- Delegated the Round 1 implementation work under Agent Teams mode and integrated the resulting commits:
  - `93b9bc1f Add gem5 suite repeat support`
  - `561edc5f Add real-platform quality inventory`
  - `618ee298 Search timing parameters from raw observations`
  - `d8ce59d0 Enforce real-platform calibration gate`
  - `af6697fe Isolate synthetic calibration profile inputs`
  - `c7fb0ffd Isolate real-platform field status artifacts`
- Ran the full real-platform gem5 MinorCPU suite twice with repeat output roots:
  - Command: `python3 scripts/run_suite.py --all --backend gem5_minor --mode real_platform_profile --results-root results --repeat 2`
  - Checked-in repeat traces: `results/r01` and `results/r02`
  - Trace count under `results/r01 results/r02`: 6442
- Regenerated analysis artifacts over the combined results tree:
  - `results/common/real_platform_inventory.json`
  - `results/common/experiment_quality.md`
  - refreshed per-instruction/profile artifacts from the corrected analyzer behavior
- Added mode/backend filtering to `scripts/search_model.py` so the real-platform report is generated from `mode == real_platform_profile`, `backend == gem5_minor`, and non-dry-run observations only.
- Added real-platform search/profile outputs:
  - `results/common/search_model_real_platform.json`
  - `results/common/search_model_real_platform_summary.md`
  - `results/common/real_platform_field_status.json`
  - `results/<instr>/profile.real_platform.yaml` for all 10 selected instructions
- Wired `scripts/analyze.py` and `scripts/check_calibration_gate.py` to consume the real-platform field-status sidecar. The real gate now fails closed on unapproved `conflict` and `insufficient_evidence` LLVM-facing fields.
- Strengthened the marker-contract path for the label-PC wrapper. The inventory records checked-in real gem5 T00 evidence, zero corrected marker delta, and the contract that marker labels emit no issue-slot instruction.
- Corrected the T10/T11 marker-delta equations from `iterations * field` to `(iterations - 1) * field`, because the start/end markers measure intervals between operations. T12 is recorded but not used as an exact latency constraint without a bypass-gap simulator.
- Kept the real-platform approval gate fail-closed. No `results/common/human_approval.*` artifact was created because the user has not explicitly approved the current inventory and field-status risks.
- The `code-simplifier` command was not installed in this environment, so that optional hook step could not be run.

## Verification

- `python3 -m py_compile scripts/check_env.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py scripts/analyze.py scripts/search_model.py scripts/check_calibration_gate.py`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed as expected for missing `Gate status: PASS`, missing machine-readable human approval, and 118 unresolved real-platform LLVM field-status risks.
- `python3 -m json.tool results/common/real_platform_inventory.json`: passed.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-real-search.json --format json`: passed.
- `python3 -m json.tool /tmp/profile-inst-latency-real-search.json`: passed.
- `python3 -m json.tool results/common/real_platform_field_status.json`: passed.
- `python3 -m json.tool results/common/search_model_real_platform.json`: passed.
- `find results/r01 results/r02 -name trace.json | wc -l`: `6442`.
- `git diff --cached --check`: passed.
- `git diff --check`: passed.
- `git diff --cached --name-only | grep -E '^results/.*/(build|gem5)/' | wc -l`: `0`.
- `git status --porcelain=v1 --untracked-files=all`: no untracked files.

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes: No new reusable lesson was added in this coordinator summary step. The round kept the existing fail-closed approval boundary and recorded the current real-platform evidence state without creating a human approval artifact.

## Current Evidence State

- `results/common/experiment_quality.md` reports:
  - Trace files analyzed: 9663
  - Synthetic traces: 3191
  - Real-platform traces: 6472
  - Real gem5 traces: 6472
  - Covered required real gem5 groups: 178
  - Missing required real gem5 groups: 0
  - Repeat groups found: 3221
  - Stable repeat groups: 3221
  - Unstable repeat groups: 0
  - Field-status risk count: 118
  - Confidence: `unresolved_llvm_field_status`
- `results/common/real_platform_inventory.json` reports all trace coverage, repeatability, and marker-contract checks passing, but `required_llvm_field_status_clean_or_accepted` and `explicit_human_approval` fail.
- `results/common/real_platform_field_status.json` reports 150 LLVM-facing field rows: 32 inferred, 44 conflict, and 74 insufficient-evidence rows. This is an improvement from the previous 149 unresolved rows after the T10/T11 interval correction, but it is still not approval-ready.
- `results/common/search_model_real_platform_summary.md` is intentionally conservative: real-platform raw observations are used as evidence, and fields that cannot be identified from the current templates are reported as `conflict` or `insufficient_evidence`.

## Remaining Blocker

The real-platform gate is not yet approval-ready. It is blocked by 118 unresolved LLVM field-status risks and by the absence of an explicit human approval artifact. I have not created any approval artifact because the user has not approved accepting those risks.

The largest remaining technical issue is the reviewer-requested shared candidate timing-model simulator. The current implementation improved the field equations and gate wiring, but it still does not fully re-simulate each template body under candidate tuples for `Latency`, `ReleaseAtCycles`, `ProcResource`, `NumMicroOps`, and `SingleIssue`.

## Goal Tracker Update Request

### Requested Changes:

- Mark T9 real gem5 timing suite coverage as completed with evidence: `results/r01` and `results/r02` contain 6442 checked-in trace files from two complete gem5 MinorCPU suite repetitions, coverage is 178/178 required groups, and repeatability is 3221 stable groups with 0 unstable groups.
- Mark the mode-isolated real-platform search artifacts and real-platform profile artifact generation as completed evidence for T10, but keep T10 itself open until the shared candidate timing-model simulator is implemented or explicitly descoped.
- Mark T11 gate integration as completed for field-status and marker-contract enforcement, but keep the real-platform gate outcome blocked. Evidence: `scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results` now validates data-derived inventory fields, marker-contract evidence, and field-status risks, and fails on the current 118 unresolved field risks plus missing approval.
- Add or retain open issues: unresolved real-platform LLVM field-status risks remain; the candidate timing-model simulator is still incomplete; the user has not approved accepting the current inventory/field-status risks, so the real-platform gate must remain `NOT_READY` and no final `COMPLETE` claim should be made yet.

### Justification:

Several review-requested gaps have been closed without using golden equality for the real-platform branch: mode isolation, real field-status/profile artifacts, gate consumption of field risks, and marker-contract validation. The candidate-resimulation search gap remains, and the current field-status sidecar proves the real-platform profile is still blocked rather than ready for approval.
