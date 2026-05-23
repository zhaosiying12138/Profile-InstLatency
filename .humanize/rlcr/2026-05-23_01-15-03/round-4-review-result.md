# Round 4 Review Result

Recommendation: REQUEST CHANGES

Architectural Status: BLOCK

Round 4 made real implementation progress: T12 is no longer absent, subject-owned T20 observations are now checked by the shared candidate simulator, real-platform artifacts were regenerated, the real gate remains fail-closed, and Claude's reported field-status counts and hashes match the checkout. The work is still not complete against `docs/plan.md`. T20 constraints are one-sided for peer-only rows, Humanize2 replay/capture artifacts are stale after Round 1, T12 exactness can be overclaimed on short sweeps, and AC-16 still lacks explicit human approval.

## Part 1: Goal Tracker Audit

### 1.1 Acceptance Criteria Status

| AC | Status | Evidence if met | Blocker if not met | Justification if deferred |
|----|--------|-----------------|--------------------|---------------------------|
| AC-1 | MET | `docs/plan.md` lists phases, files, and commands, including replay and gate commands (`docs/plan.md:1013-1038`). | n/a | n/a |
| AC-2 | MET | First platform phase evidence and tracker keep `/home/zhaosiying/codebase/compiler/llvm-project-21` read-only; LLVM implementation is in the isolated 22.1.3 worktree. | n/a | n/a |
| AC-3 | MET | Real gem5 coverage is present: `experiment_quality.md` reports 178/178 required groups and 7190 checked-in `results/r01`/`results/r02` traces. | n/a | n/a |
| AC-4 | MET | The plan and result tree cover the 10 selected non-memory RVV instruction families. | n/a | n/a |
| AC-5 | MET | Profiles and real-platform sidecars cover `SEW=e32` with `LMUL={m1,m2,m4}`. | n/a | n/a |
| AC-6 | MET | Marker contract is `PASS` and T00 checked real gem5 traces are recorded (`results/common/experiment_quality.md:3663-3668`). | n/a | n/a |
| AC-7 | MET | `results/common/` plus 10 instruction directories and 10 `profile.real_platform.yaml` sidecars exist. | n/a | n/a |
| AC-8 | MET | Search/profile records expose LLVM-facing fields first and include hardware/result metadata sidecars. | n/a | n/a |
| AC-9 | PARTIAL | Round 4 uses candidate tuples, T12 clean-prefix constraints, T20 subject-side pair checks, T21 checks, and regenerated field status. | T20 observations are not mirrored to peer-only rows such as `vredsum_vs`; T12 exact inference can overclaim on very short sweeps. | n/a |
| AC-10 | MET | `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results` passed. | n/a | n/a |
| AC-11 | MET | RLCR state, round summaries, and tracker are present; worker/RLCR ownership rules are recorded. | n/a | n/a |
| AC-12 | PARTIAL | Capture tree exists under `results/common/agentic_flow/`. | It is stale: `replay.md` still says Round 1/T01-only coverage and `execution_state.yaml` is round 0 (`results/common/agentic_flow/replay.md:3-4`, `results/common/agentic_flow/replay.md:106-107`, `results/common/agentic_flow/boards/execution_state.yaml:2-26`). | n/a |
| AC-13 | PARTIAL | `replay.md` and the draft cartridge exist. | The replay does not describe Round 2-4 real-platform runs, T20/T12 candidate-simulator changes, current hashes, or the current approval boundary. | n/a |
| AC-14 | MET | Real search filters are `mode=real_platform_profile`, `backend=gem5_minor`, with synthetic traces separated from the real gate. | n/a | n/a |
| AC-15 | MET | Synthetic gate passes before the recorded LLVM 22.1.3 YuShuXin worktree evidence. | n/a | n/a |
| AC-16 | NOT MET | Coverage/repeatability/marker-contract evidence is strong and conflict rows are zero. | `experiment_quality.md` is `NOT_READY`, human approval is absent, 39 rows are non-identifiable, and the real gate fails on missing PASS plus missing machine-readable approval (`results/common/experiment_quality.md:3-12`). | n/a |
| AC-17 | MET | The isolated `llvm-project-22.1.3-yushuxin-sched-model` worktree and focused llvm-mca/codegen evidence are recorded. | n/a | n/a |

### 1.2 Forgotten Items Detection

- Forgotten item found: per-round Humanize2 capture updates from the original plan were not maintained. The plan requires every round to update boards, prompts, tool calls, events, cartridge, and replay (`docs/plan.md:811`, `docs/plan.md:1004-1011`), but the current replay and boards are stale at Round 1/Round 0.
- Forgotten item found: T20 peer-side enforcement was not tracked before this review. Existing real traces pair other instructions with `vredsum_vs`, but `vredsum_vs` rows report empty T20 groups and `observed_counts=[]` (`results/common/real_platform_field_status.json:31249-31250`).
- Forgotten item found: T12 exactness lacks a short-sweep guard. The helper can render `exact_fit` from only K0/K1 plateau evidence because it accepts `len(clean_gaps) >= 2` and a decreasing residual (`scripts/search_model.py:1356-1383`).
- Task marked complete but not current: T6 remained listed as completed even though the replay/capture artifacts no longer reflect the current implementation state. I reopened it in `goal-tracker.md`.

### 1.3 Deferred Items Audit

No items are explicitly deferred in the tracker. No deferral justification was accepted in this review.

### 1.4 Goal Completion Summary

Acceptance Criteria: 13/17 met (0 deferred; AC-9, AC-12, AC-13 partial; AC-16 not met)

Active Tasks: 5 remaining (`T6`, `T9`, `T10`, `T11`, `T12`)

Estimated remaining rounds: 2-3, depending on whether the 39 non-identifiable rows are resolved by modeling/experiments or by explicit human risk acceptance.

Critical blockers:
- T20 peer-side pair observations must constrain peer rows or the pair model must become global.
- Humanize2 replay/capture must be refreshed for Rounds 2-4.
- T12 exact inference needs a short-sweep guard and regression test.
- Real-platform gate needs explicit machine-readable human approval tied to current hashes, or the non-identifiable rows must be resolved.

## Part 2: Implementation Review

### HIGH 1. T20 pair constraints are still one-sided for peer-only rows

The plan requires T20 to provide pipe/resource candidates and the shared parameter search to validate candidate timings (`docs/plan.md:416-425`). Round 4 does check T20 groups for the instruction that owns the trace, but the observations are grouped only by `observation.instruction_id` (`scripts/search_model.py:770-771`) and `matching_t20_group` only searches that current group (`scripts/search_model.py:1111-1118`). The candidate loop only iterates `items` for the current key (`scripts/search_model.py:1676-1683`), so a pair observation where `vredsum_vs` appears only as `pair_instruction_id` never filters the `vredsum_vs` candidate row.

Evidence:
- `results/common/search_model_real_platform.json` reports empty T20 groups for `vredsum_vs` (`results/common/search_model_real_platform.json:42362`, `results/common/search_model_real_platform.json:43688`, `results/common/search_model_real_platform.json:45014`).
- The field-status follow-up for `vredsum_vs m1/m2/m4` says `observed_counts=[]` and asks for generated T20 sweeps (`results/common/real_platform_field_status.json:31249-31250`, `results/common/real_platform_field_status.json:31376-31377`, `results/common/real_platform_field_status.json:31503-31504`).
- Real T20 traces already exist with `vredsum_vs` as the peer, for example `results/r01/vadd_vv/experiments/t20-vadd-vv-vredsum-vs-m4-n3/trace.json`.

Action: mirror T20 observations into both participants' candidate groups or replace the per-row filter with a global pair-constraint solve. Regenerate search/profile/field-status/inventory/quality artifacts and add a regression test where a peer-only instruction is constrained by an existing pair observation.

### HIGH 2. Humanize2 replay/capture is stale and reopens AC-12/AC-13

The plan states that capture is continuous, not retrospective, and every round must update execution boards, prompts/tool calls, events, cartridge, and replay (`docs/plan.md:811`, `docs/plan.md:1004-1011`). Current artifacts are stale:
- `results/common/agentic_flow/replay.md:3-4` says it is a Round 1 replay record.
- `results/common/agentic_flow/replay.md:106-107` says real-platform quality is `NOT_READY` because only T01 kill-check coverage exists, which contradicts the Round 4 178/178 real coverage and 3595 stable repeat groups.
- `results/common/agentic_flow/boards/execution_state.yaml:2-26` is still round 0 and says real-platform timing coverage is absent.
- `results/common/agentic_flow/events.jsonl` has no events after Round 1.

Action: refresh `results/common/agentic_flow/` for Rounds 2-4, including current replay commands, boards, events, tool-call evidence, verification records, cartridge flow, artifact hashes, and the human approval boundary.

### MEDIUM 3. T12 exact inference can overclaim from insufficient K coverage

The new T12 helper accepts any clean prefix with at least two gaps (`scripts/search_model.py:1356-1367`) and renders exact latency when residual0 is larger than the minimum residual (`scripts/search_model.py:1377-1383`). A two-point plateau such as K0=4, K1=4 therefore returns `exact_fit` latency 2, even though the transition/no-stall region has not been observed. Current real artifacts use wider K0..K40 sweeps, so this does not appear to corrupt the regenerated Round 4 reports, but it is a workflow bug for empty-context reuse.

Reviewer reproducer:

```text
T12 K0 delta=4, K1 delta=4 with filler cadence 1 -> candidate_field_result('Latency') returns exact_fit value 2
```

Action: require a post-transition stable residual plateau or enough contiguous K coverage before `exact_fit`; otherwise emit an upper-bound or insufficient-evidence result. Add a focused regression test before regenerating artifacts.

### HIGH 4. AC-16 remains fail-closed and incomplete

This part is correct behavior, but it prevents completion. `results/common/experiment_quality.md` reports `Gate status: NOT_READY`, `Human approval status: absent`, and an absent approval artifact (`results/common/experiment_quality.md:3-12`). The fresh gate command fails:

```text
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
FAIL: real_platform_profile gate did not pass using results/common/experiment_quality.md
- quality report must contain exact line `Gate status: PASS`
- missing machine-readable human approval file under results/common
```

Action: after fixing the implementation/capture issues, either resolve the remaining 39 non-identifiable rows through stronger modeling/experiments or obtain explicit machine-readable human approval tied to:
- `results/common/real_platform_inventory.json`: `5371f4c4c8dd8c7c292b6143243f1d9e5c68fdcbf70d2fa75274afe58885f9f4`
- `results/common/real_platform_field_status.json`: `a629c52497ca8eade0e197d6e8e398558f1c89ea13d85823d21a1b443f21a4a8`

## Part 3: Goal Tracker Update Handling

I updated `.humanize/rlcr/2026-05-23_01-15-03/goal-tracker.md`.

Approved:
- Updated Plan Version to Round 4 review.
- Recorded that T12 clean-prefix exact/upper-bound modeling replaced the absent T12 path.
- Updated real-platform evidence to 150 rows, 111 inferred, 39 non-identifiable, 0 conflict, 0 insufficient-evidence.
- Kept T9/T11 and AC-16 active because the real-platform gate is still `NOT_READY` and explicit approval is absent.
- Added the approval/hash-focused issue for the 39 non-identifiable rows.

Rejected or modified:
- I did not mark the Round 3 T20 issue fully resolved. Subject-owned T20 checks exist, but peer-only rows are not constrained.
- I did not replace all open issues with only an approval issue. The review found T20 peer-side enforcement, stale Humanize2 capture, and T12 short-sweep exactness gaps.
- I reopened AC-12/AC-13 via T6/T12 because replay/capture is not current.

## Part 4: Progress Stagnation Check

Development is not stagnant. The round history shows meaningful progress: unresolved real-platform risks moved from 118 to 5 conflicts, then to 48 non-identifiable rows, then to 39 non-identifiable rows with 0 conflicts and subject-side T20/T12 simulator integration. The remaining feedback is narrower than prior rounds. Do not stop the loop yet.

## Reviewer Verification Commands

- `python3 -m unittest tests.test_search_model_candidate_sim`: passed, 8 tests.
- `python3 -m pytest -q`: passed, 8 tests in 52.66s.
- `python3 -m py_compile scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed as expected on missing `Gate status: PASS` and missing machine-readable approval.
- Structured JSON check: `results/common/real_platform_field_status.json` has 150 rows: 111 inferred, 39 non-identifiable, 0 conflict, 0 insufficient-evidence.
- `find results/r01 results/r02 -name trace.json | wc -l`: `7190`.
- `find results/common -maxdepth 1 -iname '*approval*' -print`: empty.
- Artifact hashes match Claude's summary.

REQUEST CHANGES
