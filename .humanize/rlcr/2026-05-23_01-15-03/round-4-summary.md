# Round 4 Summary

## Work Completed
- Completed Worker Godel commit `edc9ee77 Implement Round 4 candidate simulator fixes`.
  - Added focused candidate-simulator unit tests for T20 startup-free slopes, peer candidate options, `any` pipe allocation, single-count skip behavior, and conservative T12 exact/upper-bound inference.
  - Wired T20 pair observations into the shared candidate simulator using peer candidate options, two physical pipe allocation, release cadence, micro-op occupancy, and `SingleIssue`.
  - Added a T12 clean-prefix latency model that derives exact latency or a conservative upper-bound constraint without using non-chainable T11 placeholders as hard evidence.
- Integrated Round 4 reviewer findings from Kuhn and Russell in coordinator commit `7d716fcf profile: preserve T12 solver context in reports`.
  - Preserved T12 latency constraints on `CandidateSearchResult`, so field rendering uses the same `candidate_options` and `fixed_candidates` context as the solver.
  - Exposed exact T12 constraint metadata in Latency field records.
  - Kept T12 observations outside the clean prefix out of `candidate_simulator:Latency` evidence.
  - Rendered upper-bound-only T12 latency rows as bounded `non_identifiable` domains instead of fake singleton candidates.
- Regenerated real-platform artifacts in commit `71bb5a9a profile: refresh Round 4 real platform results`.
  - `results/common/search_model_real_platform.json`
  - `results/common/real_platform_field_status.json`
  - `results/common/real_platform_inventory.json`
  - `results/common/experiment_quality.md`
  - `results/common/search_model_real_platform_summary.md`
  - all 10 `results/*/profile.real_platform.yaml` sidecars
- Kept the real-platform approval boundary intact. No `results/common/*approval*` artifact was created.
- `code-simplifier` was not installed in the available local Codex plugin cache, so no code-simplifier pass was available to invoke.

## Files Changed
- `scripts/search_model.py`: T20 hard candidate checks, T12 clean-prefix exact/upper-bound constraints, T12 solver-context preservation, and safer field-status rendering.
- `tests/test_search_model_candidate_sim.py`: 8 focused regression tests for T20/T12 candidate-simulator behavior and report shape.
- `results/common/search_model_real_platform.json`: regenerated real-platform candidate search output.
- `results/common/search_model_real_platform_summary.md`: regenerated human-readable field summary.
- `results/common/real_platform_field_status.json`: regenerated LLVM-facing field-status inventory.
- `results/common/real_platform_inventory.json`: regenerated gate inventory.
- `results/common/experiment_quality.md`: regenerated quality report.
- `results/*/profile.real_platform.yaml`: regenerated per-instruction real-platform profiles.

## Validation
- `python3 -m unittest tests.test_search_model_candidate_sim`: passed, 8 tests.
- `python3 -m pytest -q`: passed, 8 tests in 51.07s.
- `python3 -m py_compile scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py`: passed.
- `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output results/common/search_model_real_platform.json --format json`: passed.
- `python3 scripts/analyze.py --all --root results`: passed.
- JSON validation passed for:
  - `results/common/search_model_real_platform.json`
  - `results/common/real_platform_field_status.json`
  - `results/common/real_platform_inventory.json`
- Field-status summary after regeneration: 150 rows, 111 `inferred`, 39 `non_identifiable`, 0 `conflict`, 0 `insufficient_evidence`.
- Per-field status summary:
  - `Latency`: 24 `inferred`, 6 `non_identifiable`
  - `ReleaseAtCycles`: 29 `inferred`, 1 `non_identifiable`
  - `ProcResource`: 30 `non_identifiable`
  - `NumMicroOps`: 29 `inferred`, 1 `non_identifiable`
  - `SingleIssue`: 29 `inferred`, 1 `non_identifiable`
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: expected fail-closed only on:
  - missing exact `Gate status: PASS`
  - missing machine-readable human approval file under `results/common`
- `git diff --check`: passed.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: empty.

## Current Artifact Hashes
- `results/common/real_platform_inventory.json`: `5371f4c4c8dd8c7c292b6143243f1d9e5c68fdcbf70d2fa75274afe58885f9f4`
- `results/common/real_platform_field_status.json`: `a629c52497ca8eade0e197d6e8e398558f1c89ea13d85823d21a1b443f21a4a8`
- `results/common/search_model_real_platform.json`: `ed813bcec76b943e36134efcbedbe87866a1f5f73aba40206be211ebec24f935`
- `results/common/experiment_quality.md`: `8206055ea8ab05c8864203890332cb9d742d3508430c986dca7b78e5df19b9b8`

## Remaining Items
- The real-platform gate remains `NOT_READY` by design because explicit human approval is absent.
- 39 LLVM-facing rows are `non_identifiable`, not conflicts:
  - 30 ProcResource rows remain underdetermined after T20 hard checks.
  - 6 Latency rows are T12 upper-bound-only rows.
  - 3 `vcpop_m` LMUL m4 issue fields remain non-identifiable because the real-platform stream behavior is non-affine under the LLVM-facing model.
- These rows require either stronger follow-up experiments/modeling or explicit human risk acceptance tied to the current artifact hashes before AC-16 can pass.

## BitLesson Delta
Action: none
Lesson ID(s): NONE
Rationale: `.humanize/bitlesson.md` has no concrete lesson entries; the selector result for this round was `LESSON_IDS: NONE`.

## Goal Tracker Update Request

### Requested Changes:
- Update Plan Version to Round 4 review.
- Add a Plan Evolution Log entry: Round 4 replaced the skipped/placeholder T20 and T12 paths with shared candidate-simulator constraints, while preserving fail-closed real-platform approval.
- Mark the Round 3 open issue "T20 resource classification is recorded but still not enforced by the shared candidate simulator" as resolved by `edc9ee77` and `7d716fcf`.
- Mark the Round 3 open issue "T12 latency modeling remains absent for non-chainable instruction results" as resolved by the T12 clean-prefix exact/upper-bound model in `edc9ee77` and the solver-context report fix in `7d716fcf`.
- Update T10 Raw-observation parameter search status to reflect that the shared simulator now consumes T20 and T12 hard constraints. Current evidence: 150 field rows, 111 inferred, 39 non-identifiable, 0 conflict, 0 insufficient-evidence.
- Keep T9/T11 and AC-16 active because the real-platform quality report is still `NOT_READY` and explicit machine-readable human approval is absent.
- Replace the old open issues with one approval-focused issue: 39 non-identifiable real-platform rows require either stronger follow-up experiments/modeling or explicit human acceptance tied to the current `real_platform_inventory.json` and `real_platform_field_status.json` hashes.

### Justification:
Round 4 completes the concrete implementation gaps identified by the Round 3 review without overclaiming real-platform fields. The remaining blocker is now the intended AC-16 boundary: the workflow has coverage, repeatability, no conflict rows, and no insufficient-evidence rows, but it cannot pass the real-platform gate until a human explicitly accepts or resolves the remaining non-identifiable risk rows.
