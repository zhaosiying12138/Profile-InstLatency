# Round 1 Review Result

Recommendation: REQUEST CHANGES

Architectural Status: BLOCK

Round 1 made real progress on trace collection: `results/r01` and `results/r02` contain 6442 checked-in real gem5 trace files, and the inventory reports 178/178 required real gem5 template/instruction/LMUL groups with 3221/3221 stable repeat groups. That is not enough for completion. The current real-platform branch is not approval-ready because the parameter search reports unresolved field conflicts/insufficient evidence, the gate inventory does not consume those field results, and the real-platform LLVM-facing profile artifacts are still absent.

## Findings

### HIGH 1. `search_model.py --profile results` mixes synthetic calibration traces into the real-platform search

The plan requires synthetic and real-platform flows to stay distinct, with the real flow using no golden latency table and stopping on confidence/conflict state (`docs/plan.md:723-744`; AC-14 and AC-16 at `docs/plan.md:1056-1058`). The search loader recursively consumes every `trace.json` under the provided path (`scripts/search_model.py:182-185`, `scripts/search_model.py:464-476`) and then groups all observations together without filtering mode/backend (`scripts/search_model.py:946-1024`, `scripts/search_model.py:1122-1127`).

This means `python3 scripts/search_model.py --profile results` combines 3191 `synthetic_calibration` / `synthetic_cmodel` traces with 6472 `real_platform_profile` / `gem5_minor` traces. The synthetic trace cycles are derived from the configured cmodel values, so they are golden-derived observations even if `trace.synthetic` metadata is marked reference-only.

Observed result:

- `results/common/search_model_summary.md:7-9` says the search used 9663 traces and 9657 marker observations.
- Recomputed status counts: 30/30 `Latency` rows are `conflict`, 30/30 `ReleaseAtCycles` rows are `conflict`, and 30/30 rows each for `ProcResource`, `NumMicroOps`, and `SingleIssue` are `insufficient_evidence`.
- The summary itself shows this starting at `results/common/search_model_summary.md:35-49`.

This rejects the T10 completion request. The search is not a clean real-platform parameter search and cannot be used as approval evidence.

### HIGH 2. The real-platform gate ignores the search/profile field conflicts it is supposed to enforce

Phase 8 requires the real gate to verify coverage, stability, confidence, and documented assumptions (`docs/plan.md:630-635`). The real-platform exit criteria require all LLVM-facing fields to be inferred, assumed with justification, or marked non-identifiable, with unresolved conflicts documented (`docs/plan.md:740-744`).

The current inventory only records trace coverage, repeatability, mode/backend classification, assumptions, conflicts from repeat instability, and approval (`scripts/analyze.py:1400-1522`). It does not ingest `results/common/search_model_summary.md`, the JSON search output, or any real-platform per-instruction field profile. As a result:

- `results/common/real_platform_inventory.json:23-31` reports only `explicit_human_approval` as failed and `unresolved_total: 0`.
- `results/common/real_platform_inventory.json:1140-1146` marks `no_unresolved_conflicts: true`.
- `results/common/experiment_quality.md:10-12` lists only missing human approval as the approval blocker.
- At the same time, `results/common/search_model_summary.md:35-70` already reports unresolved conflicts/insufficient evidence for required LLVM-facing fields.

The gate code checks the inventory confidence/conflict records (`scripts/check_calibration_gate.py:883-884`), but those records are not tied to the search/profile field status. After an approval artifact and regenerated report are added, this gate can pass without proving that `Latency`, `ReleaseAtCycles`, `ProcResource`, `NumMicroOps`, and `SingleIssue` are resolved or explicitly accepted as risks.

This rejects the T11 completion request. The gate is data-derived for trace inventory, but not for the required LLVM-facing field confidence.

### HIGH 3. The parameter search is still not the planned candidate-resimulation search

The plan is explicit: enumerate small integer values for `Latency`, `ReleaseAtCycles`, pipe assignment, `NumMicroOps`, and `SingleIssue`; re-simulate expected template timings; choose the minimal parameter set explaining all observations (`docs/plan.md:422-425`). It also requires parameter search to verify consistency and write field confidence/evidence into YAML (`docs/plan.md:586-608`).

The current implementation enumerates fields mostly independently:

- `Latency` is constrained by direct equality such as `delta == iterations * Latency` and `delta == filler_count + Latency` (`scripts/search_model.py:554-583`).
- `ReleaseAtCycles` is constrained by direct equality `delta == iterations * ReleaseAtCycles` (`scripts/search_model.py:586-609`).
- `ProcResource` mostly depends on non-synthetic trace labels, which real traces do not carry, so it stays unknown (`scripts/search_model.py:677-733`).
- `NumMicroOps` and `SingleIssue` depend on an ad hoc T21 formula after release is exact (`scripts/search_model.py:736-823`).

There is no shared timing-model simulation that schedules the actual generated template body, no minimal parameter-set selection, and no integration of conflict explanations into per-experiment `analysis.md`. The current output confirms the implementation is not yet useful for the real branch: all required field rows are conflict or insufficient evidence.

This rejects the T10 completion request independently of the mode-mixing bug.

### MEDIUM 4. No real-platform per-instruction profile artifacts are produced

Phase 7 deliverables include `results/<instr>/profile.yaml`, and AC-8 requires profiles to record LLVM-facing fields first and hardware interpretation second (`docs/plan.md:586-593`, `docs/plan.md:1049-1051`). The only checked-in instruction profiles are still synthetic calibration profiles: for example, `results/vadd_vv/profile.yaml:1-7` has `mode: "synthetic_calibration"`. There are no `profile.yaml` files under `results/r01` or `results/r02`.

This leaves the real-platform branch without a machine-readable LLVM-facing profile that records real field values, assumptions, non-identifiable fields, confidence, and evidence. A markdown search summary is not enough for the gate or for a replayable Humanize2 workflow.

### MEDIUM 5. The marker path is validated as a label-PC wrapper, not as true simulator marker events

Round 1 added real T00 evidence, and `results/r01/common/experiments/t00-marker/trace.json` shows adjacent `t0`/`t1` markers at the same PC/cycle. That improves the previous state. However, the implementation still lowers `TIMESTAMP_MARK` into assembler labels and comments (`scripts/run_experiment.py:402-439`) and recovers marker cycles from the first Exec-log instruction at each marker PC (`scripts/run_experiment.py:548-576`).

The plan allowed a gem5 patch or wrapper support, but AC-6 requires zero-cost simulator annotations that do not occupy issue bandwidth (`docs/plan.md:1048`). If the label-PC wrapper remains the chosen implementation, it needs to be promoted into a tested contract: prove no marker instructions are emitted, validate duplicate-PC marker ordering semantics, and make the gate require checked-in real T00 evidence with no marker warnings before timing data is trusted.

## Goal Alignment Summary

ACs: 14/17 addressed | Forgotten items: 3 | Unjustified deferrals: 0

- AC-6 is partially addressed but remains weak until the label-PC marker wrapper is fully documented and gate-checked as the chosen zero-cost marker contract.
- AC-9 is incomplete because the search both mixes modes and does not implement candidate timing-model resimulation/minimal selection.
- AC-14 is partially regressed in the search path because synthetic calibration traces are mixed into the combined `results` search.
- AC-16 is incomplete because real-platform approval is missing and the gate does not validate real LLVM-facing field confidence/conflicts.
- Forgotten items: mode-isolated real-platform search, gate consumption of field-status conflicts, and real-platform per-instruction profile artifacts.
- Explicitly deferred items: none in the tracker, but the missing human approval remains a required stop condition and prevents any final complete verdict.

## Goal Tracker Update Handling

Claude's requested goal-tracker updates were partially rejected.

- T9 was not moved to completed. The repeated gem5 trace coverage exists, but the quality report is not approval-ready because field confidence/conflict state is not integrated.
- T10 was not moved to completed. The current search reports unresolved conflicts/insufficient evidence for all 30 instruction/LMUL rows and mixes synthetic with real observations.
- T11 was not moved to completed. The gate validates trace inventory data but not search/profile field confidence.
- I updated only the mutable section of `goal-tracker.md`: Plan Version is now 4, a `1-review` plan-evolution row was added, T9/T10/T11 remain `needs_changes`, and new open issues were recorded for mode mixing, gate/search integration, and missing real-platform profiles.

## Directive Implementation Plan

Claude must execute this plan before requesting another completion review:

1. Add explicit mode/backend filtering to `scripts/search_model.py`. The real-platform report generation must run only over `mode == real_platform_profile`, `backend == gem5_minor`, and `dry_run_trace == false`. Generate a separate real report, for example `results/common/search_model_real_platform_summary.md` plus a JSON sidecar. Keep synthetic calibration search/reporting separate.
2. Replace the independent field equations in `search_model.py` with a candidate timing-model simulator. Build candidate tuples for each instruction/LMUL containing `Latency`, `ReleaseAtCycles`, `ProcResource`, `NumMicroOps`, and `SingleIssue`. Simulate expected deltas for T10/T11/T12/T20/T21/T30 from the generated body metadata with the processor assumptions `IssueWidth=2`, in-order issue, no ROB, marker cost 0, and scalar issue cost 1. Select the smallest candidate set that explains every real observation within the configured tolerance. If no candidate exists, emit `conflict`; if multiple remain, emit `insufficient_evidence` with a concrete follow-up experiment.
3. Generate real-platform LLVM-facing field artifacts. Do not overwrite the synthetic profiles. Add either `results/real_platform/<instr>/profile.yaml` or `results/<instr>/profile.real_platform.yaml` for all 10 instructions, and add `results/common/real_platform_field_status.json`. These artifacts must record every required LLVM-facing field as inferred, assumed with justification, non-identifiable, conflict, or insufficient evidence, with trace evidence links.
4. Wire the real-platform gate to those field artifacts. `check_calibration_gate.py --mode real_platform_profile` must fail if any required field is `conflict` or `insufficient_evidence`, unless a machine-readable human approval artifact explicitly accepts that exact unresolved risk and ties approval to both `real_platform_inventory.json` and `real_platform_field_status.json` hashes.
5. Update `experiment_quality.md` to list field-status blockers before human approval. The report must not say the only blocker is approval while search/profile field conflicts remain.
6. Strengthen the marker contract. Keep the label-PC wrapper only if it is documented and verified as the project wrapper: checked-in real T00 evidence, no marker extraction warnings, proof that marker labels emit no instructions, and gate checks that the marker baseline is valid before timing results are accepted.
7. Regenerate `results/common/search_model_summary.md`, the real-platform search/report artifacts, real-platform profiles, `real_platform_inventory.json`, `experiment_quality.md`, and agentic-flow evidence from the corrected mode-isolated workflow.
8. Re-run verification:
   - `python3 -m py_compile scripts/check_env.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py scripts/analyze.py scripts/search_model.py scripts/check_calibration_gate.py`
   - `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`
   - `python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-real-search.json --format json`
   - `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`
   - `find results/r01 results/r02 -name trace.json | wc -l`

Do not output `COMPLETE` unless the real-platform field artifacts have no unresolved unapproved conflicts, the real gate passes with explicit human approval, and no active/deferred plan tasks remain.

## Reviewer Verification Commands

- `python3 -m py_compile scripts/check_env.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py scripts/analyze.py scripts/search_model.py scripts/check_calibration_gate.py`: passed.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results`: passed.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results`: failed with missing `Gate status: PASS` and missing machine-readable human approval.
- `find results/r01 results/r02 -name trace.json | wc -l`: `6442`.
- `python3 scripts/search_model.py --profile results --output /tmp/profile-inst-latency-review-search.json --format json`: passed.
- `python3 -m json.tool /tmp/profile-inst-latency-review-search.json`: passed.
- Search status aggregation from the regenerated JSON: 30 `Latency` conflicts, 30 `ReleaseAtCycles` conflicts, 30 `ProcResource` insufficient-evidence rows, 30 `NumMicroOps` insufficient-evidence rows, and 30 `SingleIssue` insufficient-evidence rows.

REQUEST CHANGES
