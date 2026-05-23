# Round 3 Summary

## Work Completed
- Completed Worker G3-A commit `57d9641b Extend generated pair diagnostics`.
  - Generated T20 pair-count sweeps for N=2,3,4 and register-supported N=6 cases.
  - Added fixed-scalar-destination `vcpop_m` LMUL m4 T10 diagnostics.
  - Removed non-chainable T11 suite emissions.
- Completed Worker G3-C commit `f6464f86 Fix search model evidence routing`.
  - T11 latency constraints now require generated true RAW-chain evidence.
  - Non-chainable latency rows are reported as non-identifiable with T12 follow-up.
  - T20 startup+slope evidence is recorded without the previous pair-count divisibility overfilter.
- Completed coordinator commit `7d4dc8e5 Record Round 3 real diagnostics`.
  - Ran the expanded real gem5 coverage for the new T10/T20 diagnostics in `results/r01` and `results/r02`.
  - Added 748 newly missing real trace runs; final real trace count across r01/r02 is 7190.
  - Classified the non-affine `vcpop_m` LMUL m4 stream observations as non-identifiable instead of conflict, with concrete follow-up sweep text.
  - Regenerated `search_model_real_platform.json`, `real_platform_field_status.json`, `real_platform_inventory.json`, `experiment_quality.md`, repeatability shards, and all 10 `profile.real_platform.yaml` sidecars.
- Stopped two stale `codex exec` review processes that were still writing into this worktree, removed the erroneous `scripts/search_model_io.py` split, and restored `scripts/search_model.py` to a single-file implementation plus the intended Round 3 patch.

## Files Changed
- `scripts/gen_asm.py`: expanded T20 matrix, added fixed scalar destination diagnostics, removed non-chainable T11 suite generation.
- `scripts/search_model.py`: corrected latency evidence routing, recorded T20 startup+slope groups, and classified non-affine direct-interval conflicts as non-identifiable with executable follow-up.
- `experiments/generated/**`: regenerated suite metadata and assembly for the expanded matrix.
- `results/r01/**` and `results/r02/**`: added the real gem5 trace/analysis/test artifacts for the expanded T20 coverage.
- `results/common/**`: regenerated real-platform search, inventory, field-status, quality, repeatability, and summary artifacts.
- `results/*/profile.real_platform.yaml`: regenerated per-instruction real-platform profile sidecars.
- No `results/common/*approval*` artifact was created.

## Validation
- `python3 -m py_compile scripts/check_env.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py scripts/analyze.py scripts/search_model.py scripts/check_calibration_gate.py`: passed.
- `python3 scripts/gen_asm.py suite`: passed in Worker G3-A and produced 3221 generated suite entries.
- Real gem5 rerun for missing Round 3 coverage: 748/748 runs passed, failures=0.
- `find results/r01 results/r02 -name trace.json | wc -l`: `7190`.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output results/common/search_model_real_platform.json --format json`: passed.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-real-search-current.json --format json` plus `cmp` against `results/common/search_model_real_platform.json`: passed.
- `python3 scripts/analyze.py --all --root results`: passed.
- JSON checks for `search_model_real_platform.json`, `real_platform_field_status.json`, and `real_platform_inventory.json`: passed.
- Field-status summary: 150 rows, 102 `inferred`, 48 `non_identifiable`, 0 `conflict`, 0 `insufficient_evidence`.
- Repeatability summary: 3595 repeat groups found, 3595 stable, 0 unstable.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: expected fail-closed only on missing `Gate status: PASS` and missing machine-readable human approval file under `results/common`.
- `git diff --check` and `git diff --cached --check`: passed before commit.
- Staged hygiene check found no `results/**/build/`, no `results/**/gem5/`, and no `scripts/search_model_io.py`.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: empty.

## Remaining Items
- The real-platform gate remains `NOT_READY` by design because explicit human approval is absent.
- 48 LLVM-facing real-platform fields remain `non_identifiable`; these are not blocking conflicts, but they require either stronger future experiments/modeling or explicit human risk acceptance before the real-platform gate may pass.
- The generated `vcpop_m` LMUL m4 follow-up now names the concrete stream-length/alignment/scalar-destination/source-register sweep needed to study the non-affine effect on a real platform.

## BitLesson Delta
Action: none
Lesson ID(s): NONE
Rationale: `.humanize/bitlesson.md` has no concrete lesson entries; the selector result for this round was `LESSON_IDS: NONE`.

## Goal Tracker Update Request

### Requested Changes:
- Mark Worker G3-A work as completed with evidence from commit `57d9641b` and `python3 scripts/gen_asm.py suite`.
- Mark Worker G3-C work as completed with evidence from commit `f6464f86` and the corrected field-status output.
- Mark the expanded real gem5 coverage portion of T9 as completed: r01/r02 now contain 7190 trace files, 3595/3595 repeat groups are stable, and no unstable repeat groups remain.
- Update T10/T20 status to reflect that T20 pair-count sweeps were generated and run, T20 startup+slope evidence is recorded, and ProcResource is no longer overclaimed where the evidence remains non-identifying.
- Update the `vcpop_m` LMUL m4 open issue: the prior conflict rows are resolved into `non_identifiable` rows with concrete follow-up sweep text; no blocking `conflict` rows remain.
- Keep AC-16 / real-platform approval active until a machine-readable human approval artifact is explicitly provided by the user.
- Add a Plan Evolution Log entry for the conservative classification rule: non-affine real-platform observations outside the LLVM-facing affine `startup+(N-1)*field` model are recorded as `non_identifiable` rather than forced into a guessed schedule field.

### Justification:
Round 3 resolves the review-blocking conflict state without inventing unsupported LLVM fields. The real-platform gate remains fail-closed, which preserves the plan's approval boundary for running the same workflow on Paladin or other real hardware where golden values are unavailable.
