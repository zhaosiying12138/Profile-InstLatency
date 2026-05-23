# Humanize2 Replay Notes

Status: Round 6 capture package for the Round 5 candidate-simulator code
worker, preserving the Rounds 2-4 lineage and Round 5 review outcome. This is
intentionally not a completion claim: Round 5 review accepted commit
`773f27d6` for the candidate-simulator scope, but the real-platform gate still
lacks explicit machine-readable human approval.

## Checkout

Use the profiling checkout:

```bash
cd /home/zhaosiying/codebase/compiler/profile_inst_latency
```

The read-only LLVM source checkout referenced by the plan is:

```bash
/home/zhaosiying/codebase/compiler/llvm-project-21
```

The gated LLVM implementation evidence is recorded in:

```text
results/common/llvm_yushuxin_implementation.md
```

## RLCR State

The persistent RLCR prompt, review, and summary files are under:

```text
.humanize/rlcr/2026-05-23_01-15-03/
```

Important files for replay:

- `round-2-summary.md` and `round-2-review-result.md`: shared real-platform
  candidate search was introduced, but review kept AC-9/AC-16 blocked by
  non-chainable T11 latency evidence, skipped T20 resource checks, conflicts,
  and missing approval.
- `round-3-summary.md` and `round-3-review-result.md`: generated and ran the
  expanded real T20 diagnostics, reached 7190 checked-in `results/r01` and
  `results/r02` trace files, and converted the remaining conflicts into
  conservative `non_identifiable` rows; review kept T20 and T12 simulator gaps
  open.
- `round-4-summary.md` and `round-4-review-result.md`: added subject-side T20
  pair checks and T12 clean-prefix constraints, regenerated real-platform
  artifacts, and reopened AC-12/AC-13 because this capture tree was stale.
- `round-5-prompt.md`: Round 5 boundary. It identifies the Round 4 blockers:
  peer-side T20 constraints, T12 short-sweep exactness guard, stale
  Humanize2/agentic-flow capture, and missing explicit approval.
- `round-5-summary.md`: records candidate-simulator Worker Anscombe at commit
  `773f27d6` and capture Worker Kepler at commit `cfd9a788`.
- `round-5-review-result.md`: accepts the candidate-simulator fixes from
  `773f27d6`, finds the Round 5 code-worker capture package missing, and keeps
  AC-16 blocked by absent explicit approval plus approval-validation risk.

Do not edit `.humanize/rlcr/**` from worker tasks. This replay records where
those files are read, not a modification of RLCR state.

## Modes

- `synthetic_calibration`: use configured cmodel ground truth to repair
  templates, prompts, schemas, inference, and mismatch reporting.
- `real_platform_profile`: do not use golden equality. Stop on coverage,
  stability, confidence, assumptions, conflict resolution, and explicit human
  approval.

## Evidence Snapshot

Round 4 summary hashes, preserved as the review baseline:

| Artifact | SHA-256 |
| --- | --- |
| `results/common/real_platform_inventory.json` | `5371f4c4c8dd8c7c292b6143243f1d9e5c68fdcbf70d2fa75274afe58885f9f4` |
| `results/common/real_platform_field_status.json` | `a629c52497ca8eade0e197d6e8e398558f1c89ea13d85823d21a1b443f21a4a8` |
| `results/common/search_model_real_platform.json` | `ed813bcec76b943e36134efcbedbe87866a1f5f73aba40206be211ebec24f935` |
| `results/common/experiment_quality.md` | `8206055ea8ab05c8864203890332cb9d742d3508430c986dca7b78e5df19b9b8` |

Current Round 5 boundary hashes at `main` commit `773f27d6`:

| Artifact | SHA-256 |
| --- | --- |
| `results/common/real_platform_inventory.json` | `d29e632b98c0a5734d541939c561872eeed691fd3c00b7ea83cf8aea666a536d` |
| `results/common/real_platform_field_status.json` | `904cca46aff4a923bc230d069230e15eb164af043f020dab33e5546f18560179` |
| `results/common/search_model_real_platform.json` | `d31ef8902821f272d8432f24f1e7f76da90261fdd3f47c56dfe60f0a3048bc73` |
| `results/common/experiment_quality.md` | `6062c76f6f051eac6c60b0ead3be0e8ac74bc3f723841a0ec19d0d7a750e7307` |

Current source-backed counts:

- `find results/r01 results/r02 -name trace.json | wc -l` returns `7190`.
- `results/common/experiment_quality.md` reports 178/178 required real gem5
  groups, 3595 stable repeat groups, and 0 unstable repeat groups.
- `results/common/real_platform_field_status.json` has 150 rows: 111
  `inferred`, 39 `non_identifiable`, 0 `conflict`, and 0
  `insufficient_evidence`.
- `results/common/experiment_quality.md` reports `Gate status: NOT_READY`,
  `Confidence: awaiting_human_approval`, and `Human approval status: absent`.
- `find results/common -maxdepth 1 -iname '*approval*' -print` is empty.

## Round 5 Code Worker Capture Package

Worker Anscombe's original prompt transcript was not checked in. The replay
therefore uses normalized reconstructed artifacts, explicitly labeled as such:

- Prompt: `artifacts/prompts/round-5-code-worker-candidate-simulator.md`
- Contract: `artifacts/worker_contracts/worker-r5-code.md`
- Output: `artifacts/worker_outputs/worker-r5-code.md`
- Verification: `artifacts/verification/worker-r5-code.md`
- Tool calls: `artifacts/tool_calls/worker-r5-code-normalized.json`

Allowed write scope reconstructed from commit `773f27d6`:

- `scripts/search_model.py`
- `tests/test_search_model_candidate_sim.py`
- `results/common/search_model_real_platform.json`
- `results/common/search_model_real_platform_summary.md`
- `results/common/real_platform_field_status.json`
- `results/common/real_platform_inventory.json`
- `results/common/experiment_quality.md`
- `results/vredsum_vs/profile.real_platform.yaml`

Success criteria reconstructed from Round 5 review:

- Peer-side T20 observations constrain rows that only appear as
  `pair_instruction_id`.
- `vredsum_vs` receives peer-side T20 groups in the regenerated real-platform
  search artifact.
- T12 clean-prefix exact latency requires trailing no-stall residual plateau
  coverage.
- Short K0/K1 T12 sweeps remain `non_identifiable`.
- Unit tests and review regeneration checks pass.
- Synthetic gate passes.
- Real-platform gate fails closed until explicit approval exists.

State-changing commands captured for replay:

```bash
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output results/common/search_model_real_platform.json --format json
python3 scripts/analyze.py --all --root results
```

Verification commands captured for replay:

```bash
python3 -m unittest tests.test_search_model_candidate_sim
python3 -m pytest -q
python3 -m py_compile scripts/search_model.py scripts/check_calibration_gate.py scripts/analyze.py scripts/gen_asm.py scripts/run_experiment.py scripts/run_suite.py
python3 -m json.tool results/common/search_model_real_platform.json >/dev/null
python3 -m json.tool results/common/real_platform_field_status.json >/dev/null
python3 -m json.tool results/common/real_platform_inventory.json >/dev/null
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
find results/common -maxdepth 1 -iname '*approval*' -print
sha256sum results/common/real_platform_inventory.json results/common/real_platform_field_status.json results/common/search_model_real_platform.json results/common/experiment_quality.md
git diff --check
```

The real-platform gate command is expected to return nonzero until a current,
machine-readable human approval artifact exists and the quality report says
`Gate status: PASS`.

## Replay Commands

### Environment and Generation

The strict environment check is:

```bash
python3 scripts/check_env.py
```

Dry-run replay must opt in to relaxed tool checks and must not be used as real
platform evidence:

```bash
python3 scripts/check_env.py --allow-dry-run-missing-tools
python3 scripts/check_env.py --command dry_run
```

Regenerate the experiment suite metadata without executing gem5:

```bash
python3 scripts/gen_asm.py suite --output-root experiments/generated
python3 scripts/gen_asm.py suite --manifest-only
```

### Synthetic Calibration

```bash
python3 scripts/run_suite.py --all --backend synthetic_cmodel --results-root results
python3 scripts/analyze.py --all --root results
python3 scripts/search_model.py --profile results --output results/common/search_model_summary.md --format markdown
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results
```

The synthetic gate is the only path that justified the existing LLVM
YuShuXin implementation evidence. It is not approval for real-platform timing
claims.

### Real-Platform Analysis and Search

Do not run heavy gem5 as part of a lightweight replay. To re-analyze checked-in
real traces:

```bash
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output /tmp/profile-inst-latency-real-search-current.json --format json
python3 -m json.tool /tmp/profile-inst-latency-real-search-current.json >/dev/null
cmp /tmp/profile-inst-latency-real-search-current.json results/common/search_model_real_platform.json
python3 scripts/analyze.py --all --root results
```

The Round 4 checked-in artifact regeneration used:

```bash
python3 scripts/search_model.py --profile results --mode real_platform_profile --backend gem5_minor --output results/common/search_model_real_platform.json --format json
python3 scripts/analyze.py --all --root results
```

### Gates and Integrity Checks

```bash
python3 -m json.tool results/common/search_model_real_platform.json >/dev/null
python3 -m json.tool results/common/real_platform_field_status.json >/dev/null
python3 -m json.tool results/common/real_platform_inventory.json >/dev/null
find results/r01 results/r02 -name trace.json | wc -l
sha256sum results/common/real_platform_inventory.json results/common/real_platform_field_status.json results/common/search_model_real_platform.json results/common/experiment_quality.md
python3 scripts/check_calibration_gate.py --mode synthetic_calibration --profile-root results
python3 scripts/check_calibration_gate.py --mode real_platform_profile --profile-root results
find results/common -maxdepth 1 -iname '*approval*' -print
```

The real-platform gate is expected to fail closed until the report contains an
exact `Gate status: PASS` line and a machine-readable human approval artifact is
created under `results/common`. No approval artifact exists in this capture.

## Round History

### Round 0-1

Initial workers A-H built the synthetic calibration path, gem5 T01 kill-check,
Humanize2 capture scaffold, and gated LLVM YuShuXin evidence. Round 1 replay
state was valid only for synthetic calibration plus T01 real gem5 coverage.

### Round 2

Round 2 implemented the first shared real-platform candidate simulator in
`scripts/search_model.py` and regenerated real-platform search, field-status,
inventory, quality, and profile sidecars. The review kept the round blocked
because non-chainable T11 placeholders were still used as latency evidence,
T20 was not a hard resource constraint, `vcpop_m` LMUL m4 still had conflicts,
and explicit approval was absent.

### Round 3

Round 3 generated expanded T20 pair-count sweeps, added `vcpop_m` LMUL m4
diagnostics, removed non-chainable T11 suite emissions, ran the missing real
gem5 coverage, and regenerated real-platform artifacts. It reached 7190
checked-in r01/r02 traces and 3595/3595 stable repeat groups. The review still
blocked completion because T20 was recorded but skipped by the candidate
simulator, T12 latency readiness was absent, and approval was absent.

### Round 4

Round 4 added focused tests, subject-owned T20 candidate checks, T12
clean-prefix exact/upper-bound constraints, solver-context preservation, and a
fresh real-platform artifact regeneration. Current field status is 150 rows:
111 inferred and 39 non-identifiable, with no conflict or insufficient-evidence
rows. The review kept AC-9 partial because peer-only T20 rows are not
constrained and T12 exactness needs a short-sweep guard. It reopened AC-12 and
AC-13 because this capture tree still described Round 1/T01-only state.

### Round 5 Boundary

Worker Anscombe owned `scripts/search_model.py`,
`tests/test_search_model_candidate_sim.py`, generated real-platform outputs,
common real-platform JSON/Markdown artifacts, and
`results/vredsum_vs/profile.real_platform.yaml`. Current `main` includes that
worker's commit `773f27d6`; Round 5 review accepted the candidate-simulator
fixes for peer-side T20 mirroring and the T12 short-sweep guard.

This Round 6 capture package owns only `results/common/agentic_flow/**`. It
records the missing Round 5 code-worker control flow and replay commands, does
not resolve the 39 non-identifiable rows by approval, and does not cross the
explicit approval boundary.

## Humanize2 Hub Path

If a Humanize2 hub is available, load:

```text
results/common/agentic_flow/cartridges/rvv-profile-workflow.draft.html
```

Deliver `docs/plan.md` as the implementation-plan artifact and this file as the
replay artifact. Boards under `results/common/agentic_flow/boards/` provide the
current persistent state.

## Resume After Failure

1. Read `events.jsonl` to find the latest captured event and active round.
2. Read `boards/execution_state.yaml` for active mode, gate status, and owned
   write boundaries.
3. Read `boards/inference_state.yaml` for real-platform artifact hashes,
   current field-status counts, and replay commands.
4. Read `.humanize/rlcr/2026-05-23_01-15-03/round-*-prompt.md`,
   `round-*-summary.md`, and `round-*-review-result.md` for the exact RLCR
   prompt/result lineage.
5. Re-run only the failed lightweight check or worker-owned package. Do not run
   heavy gem5 unless the active worker explicitly owns that task.
6. Append a new event and verification artifact before asking the coordinator
   to integrate the result.
