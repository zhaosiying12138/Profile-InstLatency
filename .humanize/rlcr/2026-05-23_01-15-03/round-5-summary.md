# Round 5 Summary

## Work Completed
- Completed candidate-simulator Worker Anscombe commit `773f27d6 profile: fix peer T20 and short T12 exactness`.
  - Mirrored T20 pair observations into existing peer rows, so peer-only participants such as `vredsum_vs` are constrained by traces where they appear as `pair_instruction_id`.
  - Added a T12 exactness guard requiring a trailing no-stall residual plateau before rendering `exact_fit`.
  - Added focused regressions for peer-side T20 and the K0/K1 short-sweep T12 overclaim case.
  - Regenerated real-platform search, field-status, inventory, quality, and affected profile sidecar artifacts.
- Completed Humanize2 capture Worker Kepler commit `cfd9a788 humanize: refresh Round 5 agentic flow capture`.
  - Refreshed `results/common/agentic_flow/**` for Round 2-4 history and the current Round 5 boundary.
  - Updated replay, boards, events, cartridge, primitives, status panel, and Round 5 worker prompt/contract/output/verification/tool-call artifacts.
  - Recorded current artifact hashes, fail-closed real-platform gate state, and the explicit approval boundary.
- No `results/common/*approval*` artifact was created.

## Files Changed
- `scripts/search_model.py`
- `tests/test_search_model_candidate_sim.py`
- `results/common/search_model_real_platform.json`
- `results/common/search_model_real_platform_summary.md`
- `results/common/real_platform_field_status.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `results/vredsum_vs/profile.real_platform.yaml`
- `results/common/agentic_flow/**`

## Validation
- `python3 -m unittest tests.test_search_model_candidate_sim`: passed, 10 tests.
- `python3 -m pytest -q`: passed, 10 tests in 50.72s.
- `python3 -m py_compile scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py`: passed.
- JSON validation passed for:
  - `results/common/search_model_real_platform.json`
  - `results/common/real_platform_field_status.json`
  - `results/common/real_platform_inventory.json`
  - `results/common/agentic_flow/artifacts/tool_calls/worker-r5-capture-verification.json`
- `results/common/agentic_flow/events.jsonl`: JSONL parse passed.
- Field-status summary: 150 rows, 111 `inferred`, 39 `non_identifiable`, 0 `conflict`, 0 `insufficient_evidence`.
- `vredsum_vs` T20 peer-side evidence check:
  - `m1`: 9 T20 groups, counts `[2,3,4,6]`
  - `m2`: 9 T20 groups, counts `[2,3,4,6]`
  - `m4`: 9 T20 groups, counts `[2,3,4]` and `[2,3,4,6]`
- `find results/r01 results/r02 -name trace.json | wc -l`: `7190`.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: expected fail-closed only on:
  - missing exact `Gate status: PASS`
  - missing machine-readable human approval file under `results/common`
- `find results/common -maxdepth 1 -iname '*approval*' -print`: empty.
- `git diff --check`: passed.
- Stale active-claim checks:
  - `Status: Round 1 replay record`: absent from `results/common/agentic_flow/replay.md`
  - `only the T01 kill-check has real gem5 coverage`: absent as an active replay claim
  - `round: 0`: absent from `results/common/agentic_flow/boards/execution_state.yaml`

## Current Artifact Hashes
- `results/common/real_platform_inventory.json`: `d29e632b98c0a5734d541939c561872eeed691fd3c00b7ea83cf8aea666a536d`
- `results/common/real_platform_field_status.json`: `904cca46aff4a923bc230d069230e15eb164af043f020dab33e5546f18560179`
- `results/common/search_model_real_platform.json`: `d31ef8902821f272d8432f24f1e7f76da90261fdd3f47c56dfe60f0a3048bc73`
- `results/common/experiment_quality.md`: `6062c76f6f051eac6c60b0ead3be0e8ac74bc3f723841a0ec19d0d7a750e7307`

## Remaining Items
- The real-platform gate remains `NOT_READY` by design because explicit human approval is absent.
- 39 LLVM-facing real-platform rows remain `non_identifiable`, not conflicts:
  - 30 ProcResource rows remain underdetermined.
  - 6 Latency rows are T12 upper-bound/non-identifiable rows.
  - 3 `vcpop_m` LMUL m4 issue fields remain non-identifiable because the real-platform stream behavior is non-affine under the LLVM-facing model.
- These rows require either stronger follow-up experiments/modeling or explicit human risk acceptance tied to the current artifact hashes before AC-16 can pass.

## BitLesson Delta
Action: none
Lesson ID(s): NONE
Rationale: `.humanize/bitlesson.md` has no concrete lesson entries; the selector result for this round was `LESSON_IDS: NONE`.

## Goal Tracker Update Request

### Requested Changes:
- Mark the Round 4 open issue "T20 peer-side resource constraints are not mirrored into rows that only appear as `pair_instruction_id`" as resolved by commit `773f27d6`.
- Mark the Round 4 open issue "T12 clean-prefix exact inference can overclaim on too-short sweeps" as resolved by commit `773f27d6`.
- Mark the Round 4 open issue "Humanize2 replay/capture artifacts are stale after Round 1" as resolved by commit `cfd9a788`.
- Update T10 Raw-observation parameter search notes: peer-side T20 constraints and the T12 short-sweep guard are implemented and verified; current field status remains 111 inferred / 39 non-identifiable / 0 conflict / 0 insufficient-evidence.
- Update T6/T12 Humanize2 capture status to completed for the Round 2-5 replay/capture refresh, with evidence from `results/common/agentic_flow/replay.md`, boards, events, cartridge, and `worker-r5-capture` artifacts.
- Keep T9/T11 and AC-16 active because the real-platform gate still lacks explicit machine-readable human approval.
- Keep one open approval-focused issue for the 39 non-identifiable real-platform rows requiring stronger evidence/modeling or explicit human acceptance tied to the current artifact hashes.

### Justification:
Round 5 resolves the implementation and replay/capture blockers identified in the Round 4 review without crossing the real-platform approval boundary. The only remaining hard blocker is the intended AC-16 human decision point for accepting or resolving the 39 non-identifiable real-platform rows.
