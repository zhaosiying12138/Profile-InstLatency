# RVV Instruction Latency Profiling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `humanize-rlcr` as the coordinator loop. Independent implementation tasks may use parallel writable workers in disjoint directories/worktrees. Worker/subagent tasks must not start RLCR, run the RLCR gate, edit `.humanize/`, or write round summaries.

**Goal:** Build a platform-first profiling workflow that uses gem5 MinorCPU to profile selected non-memory RVV instruction timing, records structured results, and preserves enough metadata to later fill an LLVM RISC-V processor schedule model.

**Architecture:** First prove a gem5 MinorCPU RVV baseline can execute the selected 10 RVV instructions. Then add a configurable two-pipe RVV timing model and zero-cost timestamp marker path, generate assembly experiments, run them, infer LLVM-aligned scheduling fields, and write reproducible results under `results/`. LLVM is read-only in this plan and only constrains the data schema.

**Tech Stack:** gem5 MinorCPU, RISC-V RVV assembly, existing RISC-V assembler toolchain, Python orchestration/analysis, YAML/JSON result files, Humanize RLCR, Codex worker agents.

---

## Scope

This plan targets the first platform-first phase. It does not modify `/home/zhaosiying/codebase/compiler/llvm-project-21`; it only reads LLVM source to define which fields the profiler must infer.

The first simulator baseline is gem5 MinorCPU. gem5 is selected because its current releases include RVV support/fixes, and MinorCPU is an in-order model with configurable functional units, issue limits, issue delay, and issue-to-commit timing. If gem5 cannot stably execute the 10 selected RVV instructions in the early kill-check, switch to a candidate comparison phase before implementing timing patches.

## Source Facts To Preserve

LLVM schedule-model fields to align with:

- `MCSchedModel::IssueWidth`: hard per-cycle issue-group width.
- `MCSchedModel::MicroOpBufferSize`: `0`/`1` for in-order style scheduling; `>1` means out-of-order. Our assumed processor uses in-order, no ROB.
- `ProcResource` / `ProcResGroup`: execution resource kinds and groups.
- `WriteRes` / `SchedWriteRes`: per-write resource use, `Latency`, `NumMicroOps`, `AcquireAtCycles`, `ReleaseAtCycles`, `SingleIssue`, `BeginGroup`, `EndGroup`.
- `ReadAdvance`: consumer-specific bypass/read timing adjustment.

Relevant LLVM files:

- `/home/zhaosiying/codebase/compiler/llvm-project-21/llvm/include/llvm/MC/MCSchedule.h`
- `/home/zhaosiying/codebase/compiler/llvm-project-21/llvm/include/llvm/Target/TargetSchedule.td`
- `/home/zhaosiying/codebase/compiler/llvm-project-21/llvm/lib/Target/RISCV/RISCVScheduleV.td`
- `/home/zhaosiying/codebase/compiler/llvm-project-21/llvm/lib/Target/RISCV/RISCVSchedSiFiveP800.td`
- `/home/zhaosiying/codebase/compiler/llvm-project-21/llvm/lib/Target/RISCV/RISCVInstrInfoV.td`
- `/home/zhaosiying/codebase/compiler/llvm-project-21/llvm/lib/Target/RISCV/RISCVInstrInfoVPseudos.td`

External references:

- gem5 RVV release notes: `https://github.com/gem5/gem5/releases`
- gem5 MinorCPU documentation: `https://gem5.googlesource.com/public/gem5-website/+/8b2140126ae476cef25e873d688ff57e3f4472e4/_pages/documentation/general_docs/cpu_models/minor_cpu.md`

## Processor Assumptions For First Model

- RVV instructions are issued in order.
- Dual issue is available.
- There is no out-of-order execution and no ROB.
- There are two RVV execution pipelines.
- RVV pipelines are fully pipelined unless a configured instruction says otherwise.
- First profiling matrix fixes `SEW=e32` and uses `LMUL={m1,m2,m4}`.
- `e16` and `e64` are out of first-version scope.
- Timing functions should allow forms such as `latency = base + k * LMUL` and `occupancy = base + k * LMUL`.
- Vector load/store timing is not part of the 10 instruction set. It is recorded under `results/common/`.

## Initial 10 RVV Instruction Set

Use this set unless the gem5 kill-check proves one is unsupported. If one fails, replace it with the closest supported instruction in the same schedule family and document the substitution.

| ID | Instruction | LLVM schedule family target | Purpose |
| --- | --- | --- | --- |
| `vadd_vv` | `vadd.vv` | `WriteVIALUV` | simple integer vector ALU |
| `vsll_vv` | `vsll.vv` | `WriteVShiftV` | vector shift |
| `vmul_vv` | `vmul.vv` | `WriteVIMulV` | integer multiply |
| `vdivu_vv` | `vdivu.vv` | `WriteVIDivV` | long-latency integer divide |
| `vmseq_vv` | `vmseq.vv` | `WriteVICmpV` | compare producing mask |
| `vcpop_m` | `vcpop.m` | `WriteVMPopV` | mask population count |
| `viota_m` | `viota.m` | `WriteVIotaV` | mask-to-vector operation |
| `vslideup_vx` | `vslideup.vx` | `WriteVSlideUpX` | slide pipeline behavior |
| `vrgather_vv` | `vrgather.vv` | `WriteVRGatherVV` | permutation/gather behavior |
| `vredsum_vs` | `vredsum.vs` | `WriteVIRedV_From` | reduction behavior |

## Result Tree Contract

The workflow must create exactly this top-level shape:

```text
results/
  common/
    processor.yaml
    llvm_field_map.yaml
    experiments/
      <experiment-id>/
        experiment.yaml
        test.s
        trace.json
        analysis.md
  vadd_vv/
    profile.yaml
    experiments/
      <experiment-id>/
        experiment.yaml
        test.s
        trace.json
        analysis.md
  vsll_vv/
    profile.yaml
    experiments/
      <experiment-id>/
        experiment.yaml
        test.s
        trace.json
        analysis.md
  vmul_vv/
    profile.yaml
    experiments/
      <experiment-id>/
        experiment.yaml
        test.s
        trace.json
        analysis.md
  vdivu_vv/
    profile.yaml
    experiments/
      <experiment-id>/
        experiment.yaml
        test.s
        trace.json
        analysis.md
  vmseq_vv/
    profile.yaml
    experiments/
      <experiment-id>/
        experiment.yaml
        test.s
        trace.json
        analysis.md
  vcpop_m/
    profile.yaml
    experiments/
      <experiment-id>/
        experiment.yaml
        test.s
        trace.json
        analysis.md
  viota_m/
    profile.yaml
    experiments/
      <experiment-id>/
        experiment.yaml
        test.s
        trace.json
        analysis.md
  vslideup_vx/
    profile.yaml
    experiments/
      <experiment-id>/
        experiment.yaml
        test.s
        trace.json
        analysis.md
  vrgather_vv/
    profile.yaml
    experiments/
      <experiment-id>/
        experiment.yaml
        test.s
        trace.json
        analysis.md
  vredsum_vs/
    profile.yaml
    experiments/
      <experiment-id>/
        experiment.yaml
        test.s
        trace.json
        analysis.md
```

`results/common/processor.yaml` records global inferred processor properties:

```yaml
schema_version: 1
processor:
  issue_width:
    value: null
    evidence: []
  micro_op_buffer_size:
    value: 0
    evidence: []
  rvv_pipelines:
    count:
      value: 2
      evidence: []
    resources:
      - name: VPipe0
        kind: proc_resource
      - name: VPipe1
        kind: proc_resource
  timestamp_model:
    kind: zero_cost_marker
    occupies_issue_slot: false
    cycles: 0
common_measurements:
  load_hit_latency:
    value: null
    status: deferred_to_common_experiment
  scalar_issue_baseline:
    value: null
    evidence: []
```

Each `results/<instr>/profile.yaml` records LLVM-facing fields first and hardware-interpretation fields second:

```yaml
schema_version: 1
instruction:
  id: vadd_vv
  asm: vadd.vv
  sew: 32
measurements:
  m1:
    llvm:
      proc_resource:
        value: null
        confidence: unknown
        evidence: []
      latency:
        value: null
        confidence: unknown
        evidence: []
      release_at_cycles:
        value: null
        confidence: unknown
        evidence: []
      acquire_at_cycles:
        value: []
        confidence: assumed_default
        evidence: []
      num_micro_ops:
        value: 1
        confidence: assumed_until_tested
        evidence: []
      single_issue:
        value: false
        confidence: assumed_until_tested
        evidence: []
      read_advance:
        value: {}
        confidence: unknown
        evidence: []
    hardware_interpretation:
      issue_delay_cycles:
        value: null
        identifiable: partial
        evidence: []
      execute_latency_cycles:
        value: null
        identifiable: partial
        evidence: []
      writeback_latency_cycles:
        value: null
        identifiable: false
        reason: LLVM/gem5 marker experiments observe producer-consumer readiness, not a separate physical writeback stage unless the model exposes it.
fit:
  latency_formula:
    form: base_plus_lmul_times_k
    base: null
    k: null
  release_formula:
    form: base_plus_lmul_times_k
    base: null
    k: null
```

## Experiment Template IDs

Every experiment directory must use one of these template IDs in `experiment.yaml`.

### `T00_BASELINE_MARKER`

Purpose: confirm zero-cost marker behavior and simulator cycle-read consistency.

Shape:

```asm
TIMESTAMP_MARK t0
TIMESTAMP_MARK t1
```

Expected first-version result: `t1 - t0 == 0` or a documented constant marker read delta. If the marker creates any pipeline cost, stop and fix the timestamp implementation before continuing.

### `T01_DECODE_EXEC_KILLCHECK`

Purpose: prove gem5 can assemble, decode, and execute the instruction for `e32,m1`, `e32,m2`, and `e32,m4`.

Shape:

```asm
vsetvli x0, xN, e32, <lmul>, ta, ma
<initialize input vector registers>
TIMESTAMP_MARK before
<instruction under test>
TIMESTAMP_MARK after
```

Expected result: no illegal instruction, no simulator assert, trace contains both markers, and architectural execution reaches program end.

### `T10_INDEPENDENT_STREAM_THROUGHPUT`

Purpose: infer resource occupancy / `ReleaseAtCycles` lower bound.

Shape:

```asm
vsetvli x0, xN, e32, <lmul>, ta, ma
TIMESTAMP_MARK start
<IUT using v0/v1 -> v8>
<IUT using v2/v3 -> v9>
<IUT using v4/v5 -> v10>
<IUT using v6/v7 -> v11>
<IUT using v12/v13 -> v16>
<IUT using v14/v15 -> v17>
TIMESTAMP_MARK end
```

Analysis: run for several stream lengths. The slope gives steady-state cycles per instruction for independent instances. With dual issue and a fully pipelined single resource, same-resource throughput should be one per cycle; if `ReleaseAtCycles > 1`, slope increases.

### `T11_SELF_RAW_CHAIN`

Purpose: infer producer-consumer latency for chainable instructions.

Shape:

```asm
vsetvli x0, xN, e32, <lmul>, ta, ma
TIMESTAMP_MARK start
<IUT using v8/v1 -> v8>
<IUT using v8/v1 -> v8>
<IUT using v8/v1 -> v8>
<IUT using v8/v1 -> v8>
<IUT using v8/v1 -> v8>
<IUT using v8/v1 -> v8>
TIMESTAMP_MARK end
```

Analysis: slope estimates observable RAW latency for the instruction's own result path. For non-chainable instructions, use `T12_CONSUMER_RAW_GAP`.

### `T12_CONSUMER_RAW_GAP`

Purpose: measure latency from IUT result to selected consumer read type and estimate `ReadAdvance` differences.

Shape:

```asm
TIMESTAMP_MARK start
<IUT writes result R>
<K independent filler instructions>
<consumer reads R>
TIMESTAMP_MARK end
```

Analysis: sweep `K`. The smallest `K` that eliminates the stall estimates the producer-to-consumer readiness distance. Repeat with different consumers when LLVM has distinct `SchedRead` categories.

### `T20_PAIRWISE_PIPE_CLASSIFICATION`

Purpose: classify pipe affinity and flexible resource groups.

Shape:

```asm
TIMESTAMP_MARK start
<A independent instance 0>
<B independent instance 0>
<A independent instance 1>
<B independent instance 1>
<A independent instance 2>
<B independent instance 2>
<A independent instance 3>
<B independent instance 3>
TIMESTAMP_MARK end
```

Analysis: compare `A/A`, `B/B`, and `A/B` slopes. If `A/B` approaches two instructions per cycle while `A/A` and `B/B` do not, A and B likely occupy different single pipelines. If A pairs well with both pipe-specific sentinels, model A as a `ProcResGroup`.

### `T21_PAIR_WITH_SCALAR`

Purpose: test whether a vector instruction behaves as `NumMicroOps=2`, `SingleIssue`, `BeginGroup`, or `EndGroup`.

Shape:

```asm
TIMESTAMP_MARK start
<IUT independent instance 0>
add x20, x21, x22
<IUT independent instance 1>
add x23, x24, x25
<IUT independent instance 2>
add x26, x27, x28
<IUT independent instance 3>
add x29, x30, x31
TIMESTAMP_MARK end
```

Analysis: if scalar pairing is consistently blocked even without vector resource conflict, mark `single_issue` or `num_micro_ops > 1` as a candidate and require confirmation by parameter search.

### `T30_LMUL_SCALING`

Purpose: fit `base + k * LMUL` timing formulas.

Shape: rerun `T10`, `T11`, and `T12` for `m1`, `m2`, and `m4`.

Analysis: fit latency and release formulas. Record exact points and residuals; do not overfit beyond `base + k * LMUL` in the first version.

### `T40_COMMON_VLSU_LOAD_HIT`

Purpose: record common vector load-hit timing separately from the 10 non-memory instruction profiles.

Shape: use unit-stride vector loads with cache-warmed aligned memory and a dependent vector consumer.

Analysis: record under `results/common/`, not under any of the 10 instruction directories.

## Inference Strategy

Use a mixed strategy:

1. Rule-based extraction produces initial candidates:
   - `T10` gives independent throughput and resource occupancy lower bound.
   - `T11`/`T12` gives observable latency.
   - `T20` gives pipe class/resource group candidates.
   - `T21` flags single-issue or multi-micro-op candidates.
   - `T30` fits LMUL scaling.
2. Parameter search validates candidates:
   - Enumerate small integer values for `Latency`, `ReleaseAtCycles`, pipe assignment, `NumMicroOps`, and `SingleIssue`.
   - Re-simulate expected template timings with the candidate timing model.
   - Choose the minimal parameter set explaining all observed experiments.
3. Conflict reporting:
   - If rule extraction and search disagree, keep both in `analysis.md`.
   - Mark the affected YAML fields as `confidence: conflict`.
   - Add a proposed follow-up experiment with a concrete template ID and operands.

## Implementation Phases

### Phase 0: Repository And Toolchain Bootstrap

Deliverables:

- `README.md` with setup and one-command overview.
- `scripts/check_env.py` verifying Python, RISC-V assembler, gem5 checkout, and LLVM checkout path.
- `config/paths.yaml` containing absolute or repo-relative tool paths.

Acceptance:

- Running `python3 scripts/check_env.py` prints a JSON summary and exits `0` when required tools exist.
- It exits non-zero with actionable messages when a required tool is missing.

### Phase 1: Read-Only LLVM Field Extractor

Deliverables:

- `scripts/llvm_sched_extract.py`
- `results/common/llvm_field_map.yaml`
- Documentation in `docs/llvm-sched-model-notes.md`

Responsibilities:

- Read the LLVM files listed above.
- Extract the schedule families for the 10 selected RVV instructions.
- Record which LLVM fields must be inferred and which are assumed.
- Do not modify LLVM.

Acceptance:

- The generated map lists all 10 instruction IDs and their target `SchedWrite` family.
- The notes explain why `Latency` and `ReleaseAtCycles` are the primary LLVM fields, while separate physical writeback latency is not directly represented unless modeled indirectly.

### Phase 2: gem5 RVV Kill-Check

Deliverables:

- `third_party/gem5/` or a configured external gem5 checkout path.
- `experiments/killcheck/*.s`
- `scripts/run_killcheck.py`
- `results/common/experiments/T01_DECODE_EXEC_KILLCHECK-*/`

Responsibilities:

- Assemble and run one minimal program per instruction and per LMUL in `m1,m2,m4`.
- Confirm gem5 can execute all selected instructions.
- Confirm the workflow can collect a trace/log reaching program end.

Kill condition:

- If any selected instruction cannot assemble or execute after one narrow fix attempt, stop gem5 implementation work.
- Create `docs/simulator-candidate-comparison.md` comparing at least gem5, Spike plus timing wrapper, and one additional RVV-capable simulator or emulator.
- Pick the next simulator only after documenting RVV support, timing expressiveness, custom marker feasibility, and LLVM-field coverage.

### Phase 3: Zero-Cost Timestamp Marker Path

Deliverables:

- gem5 patch or wrapper support for `TIMESTAMP_MARK <label>`.
- Trace schema in `docs/trace-schema.md`.
- `T00_BASELINE_MARKER` experiments in `results/common/`.

Marker semantics:

- The marker samples the current simulator cycle.
- It does not occupy an issue slot.
- It does not enter any functional unit.
- It does not affect scoreboard dependencies.
- It writes to simulator trace/log, not to architectural registers.

Acceptance:

- Two adjacent markers produce zero delta or one documented constant delta.
- The analysis layer subtracts the documented marker baseline before using measurements.

### Phase 4: Configurable Two-Pipe RVV Timing Model

Deliverables:

- gem5 timing configuration file, for example `config/rvv_timing_model.yaml`.
- Two RVV resources: `VPipe0` and `VPipe1`.
- Per-instruction parameter table for the selected 10 instructions.

Initial synthetic parameter target:

```yaml
vadd_vv:      {pipe: any,    latency_base: 2,  latency_lmul_k: 0, release_base: 1, release_lmul_k: 0}
vsll_vv:      {pipe: any,    latency_base: 3,  latency_lmul_k: 1, release_base: 1, release_lmul_k: 1}
vmul_vv:      {pipe: any,    latency_base: 5,  latency_lmul_k: 1, release_base: 1, release_lmul_k: 1}
vdivu_vv:     {pipe: pipe1,  latency_base: 12, latency_lmul_k: 6, release_base: 4, release_lmul_k: 2}
vmseq_vv:     {pipe: any,    latency_base: 2,  latency_lmul_k: 0, release_base: 1, release_lmul_k: 0}
vcpop_m:      {pipe: pipe0,  latency_base: 3,  latency_lmul_k: 1, release_base: 1, release_lmul_k: 0}
viota_m:      {pipe: pipe0,  latency_base: 4,  latency_lmul_k: 2, release_base: 1, release_lmul_k: 1}
vslideup_vx:  {pipe: pipe0,  latency_base: 3,  latency_lmul_k: 1, release_base: 1, release_lmul_k: 0}
vrgather_vv:  {pipe: pipe1,  latency_base: 5,  latency_lmul_k: 2, release_base: 1, release_lmul_k: 1}
vredsum_vs:   {pipe: pipe1,  latency_base: 6,  latency_lmul_k: 3, release_base: 1, release_lmul_k: 1}
```

These values are synthetic ground truth for validating the profiler. They must be recorded separately from inferred results so mismatch analysis can compare inferred vs configured values.

### Phase 5: Assembly Generator

Deliverables:

- `scripts/gen_asm.py`
- `templates/*.s.j2` or equivalent structured templates.
- `experiments/generated/<experiment-id>/test.s`

Responsibilities:

- Generate RVV setup for `e32,m1`, `e32,m2`, and `e32,m4`.
- Rotate vector registers to avoid accidental RAW/WAW dependencies in independent-stream tests.
- Generate explicit RAW dependencies for chain/gap tests.
- Generate scalar pairing probes for `T21`.
- Emit marker labels that match `experiment.yaml`.

Acceptance:

- Generated assembly is deterministic.
- Each generated file has an adjacent `experiment.yaml`.
- The generator can reproduce all experiments from the metadata alone.

### Phase 6: Runner And Trace Collector

Deliverables:

- `scripts/run_experiment.py`
- `scripts/run_suite.py`
- `results/**/trace.json`

Responsibilities:

- Assemble generated assembly into a binary.
- Run gem5 with the configured timing model.
- Collect marker trace entries.
- Normalize trace output to JSON.

Trace entry schema:

```json
{
  "marker": "start",
  "cycle": 1234,
  "pc": "0x80000000",
  "experiment_id": "T10-vadd_vv-m1-n64"
}
```

Acceptance:

- `python3 scripts/run_suite.py --killcheck` populates only kill-check results.
- `python3 scripts/run_suite.py --all` populates common and all 10 instruction result directories.

### Phase 7: Analyzer And Parameter Search

Deliverables:

- `scripts/analyze.py`
- `scripts/search_model.py`
- `results/<instr>/profile.yaml`
- `results/<instr>/experiments/<id>/analysis.md`

Responsibilities:

- Compute deltas from marker traces.
- Fit throughput slopes and RAW latency slopes.
- Classify pipe affinity using pairwise throughput.
- Fit LMUL formulas.
- Run parameter search to verify consistency.
- Write field confidence and evidence links into YAML.

Acceptance:

- Every non-null inferred value has at least one evidence experiment ID.
- Every conflict has an `analysis.md` explanation and a concrete next experiment proposal.
- In synthetic gem5 mode, inferred values must match configured values or appear in the mismatch report.

### Phase 8: Mismatch And Experiment-Quality Evaluation

Deliverables:

- `results/common/mismatch_report.md`
- `results/common/experiment_quality.md`
- `scripts/check_calibration_gate.py`

Responsibilities:

- Compare inferred values with synthetic configured ground truth.
- Identify template weaknesses:
  - marker semantics accidentally affect timing,
  - insufficient independent register rotation,
  - hidden dependencies through mask/passthru operands,
  - LMUL register overlap,
  - scalar frontend bottleneck mistaken as vector pipe bottleneck,
  - cache/memory effects leaking into non-memory experiments.
- Recommend new experiments when a field is not identifiable.

Acceptance:

- Report lists all 10 instructions.
- Report separates simulator implementation bugs from experiment design limits.
- `python3 scripts/check_calibration_gate.py --mode synthetic_calibration` exits `0` only when every claimed field matches configured synthetic ground truth or is explicitly marked not identifiable.
- `python3 scripts/check_calibration_gate.py --mode real_platform_profile` never checks golden equality and instead verifies coverage, stability, confidence, and documented assumptions.

### Phase 9: LLVM Model Draft Export

Deliverables:

- `results/common/llvm_model_draft.td`
- `results/common/llvm_model_mapping.md`

Responsibilities:

- Generate a draft schedule-model snippet from profiled fields.
- Mark all generated content as draft.
- Do not write into LLVM checkout.

Acceptance:

- The draft includes `ProcessorModel`, two RVV `ProcResource`s, any `ProcResGroup`, and per-instruction-family `WriteRes` entries for the selected instructions.
- The mapping document explains every generated field and evidence source.

### Phase 10: LLVM 22.1.3 YuShuXin Schedule Model Implementation

This phase is gated. It must not start until the synthetic cmodel calibration report shows the inferred profile agrees with the configured cmodel ground truth for all fields that the first-version experiment claims to identify.

Entry gate:

- `results/common/mismatch_report.md` exists.
- Every configured synthetic value used by the first-version profiler is either:
  - matched by the inferred value, or
  - explicitly marked as not claimed / not identifiable by the first-version experiment.
- No field with `confidence: conflict` is used to generate the LLVM implementation.
- `results/common/llvm_model_mapping.md` maps every emitted LLVM field back to evidence.
- `results/common/agentic_flow/replay.md` documents the final calibrated cmodel workflow before LLVM code is edited.

Worktree setup:

```bash
cd /home/zhaosiying/codebase/compiler/llvm-project-21
git rev-parse llvmorg-22.1.3^{commit}
git worktree add /home/zhaosiying/codebase/compiler/llvm-project-22.1.3-yushuxin-sched-model llvmorg-22.1.3 -b riscv-yushuxin-sched-model
```

If `llvmorg-22.1.3` is not available, stop and verify the local tag name before creating a worktree. Do not guess `v22.1.3` without checking.

Deliverables in the profiling repo:

- Profiling-repo helper: `scripts/prepare_llvm_yushuxin_worktree.py`.
- A checked-in note under the profiling repo, not the LLVM worktree, linking the LLVM patch to profile evidence:
  - `results/common/llvm_yushuxin_implementation.md`

Deliverables in the LLVM worktree:

- New RISC-V schedule model TableGen file, expected shape: `llvm/lib/Target/RISCV/RISCVSchedYuShuXin.td`.
- Processor registration in the RISC-V backend, expected location: `llvm/lib/Target/RISCV/RISCVProcessors.td` or the current equivalent in the 22.1.3 checkout.
- Include wiring from the RISC-V schedule include surface, expected location: `llvm/lib/Target/RISCV/RISCV.td` or the current equivalent in the 22.1.3 checkout.
- LLVM tests proving the CPU model is accepted and the selected RVV instructions use the intended schedule resources/latencies. Expected test areas:
  - `llvm/test/CodeGen/RISCV/`
  - `llvm/test/tools/llvm-mca/RISCV/`

Implementation requirements:

- Expose the CPU name as `YuShuXin` and add tests that invoke the exact spelling expected by the user.
- Model the assumed global processor properties:
  - in-order scheduling,
  - `IssueWidth = 2`,
  - no out-of-order micro-op buffer / no ROB,
  - two RVV pipeline resources,
  - fully pipelined behavior where `ReleaseAtCycles` indicates one-cycle occupancy.
- Emit per-instruction-family `WriteRes` / `SchedWriteRes` values only from fields that were validated by the profiler.
- Preserve unknown or non-identifiable fields conservatively; do not invent `ReadAdvance` or physical writeback behavior just to make the model look complete.
- Keep the implementation scoped to the RISC-V backend schedule model and tests. Do not modify unrelated LLVM backends or generic scheduler code.

Verification commands must be discovered from the worktree, but the first target set should include:

```bash
ninja -C <llvm-build-dir> llc llvm-mca FileCheck not count
<llvm-build-dir>/bin/llvm-lit llvm/test/CodeGen/RISCV/<new-yushuxin-tests>.ll -v
<llvm-build-dir>/bin/llvm-lit llvm/test/tools/llvm-mca/RISCV/<new-yushuxin-tests>.s -v
```

Acceptance:

- `llc -mtriple=riscv64 -mcpu=YuShuXin` accepts the CPU name.
- RVV codegen tests compile with the new CPU and selected vector extension features.
- `llvm-mca` or equivalent schedule-model tests show the intended `IssueWidth`, RVV resources, and per-instruction latency/resource behavior for the 10 profiled instruction families.
- The LLVM patch is committed in the isolated worktree, not in `/home/zhaosiying/codebase/compiler/llvm-project-21`.
- The profiling repo records the LLVM commit hash, worktree path, exact test commands, and profile evidence used.

## Golden Calibration Versus Real Platform Flow

The synthetic gem5/cmodel loop is allowed to use configured ground truth. Its purpose is to debug the experiment templates, prompts, result schema, inference code, and Humanize2 workflow primitives. In that calibration mode, the workflow may iterate until inferred values match configured values because the configured cmodel table is known.

That loop must be explicitly labeled as `mode: synthetic_calibration` in:

- `results/common/processor.yaml`
- `results/common/mismatch_report.md`
- `results/common/agentic_flow/boards/execution_state.yaml`
- `results/common/agentic_flow/events.jsonl`

The real Paladin/hardware flow must be labeled `mode: real_platform_profile`. In real platform mode:

- The workflow knows only prior assumptions such as in-order issue, dual issue, no ROB, two RVV pipelines, and fully pipelined pipes.
- There is no configured per-instruction latency ground truth.
- The workflow must not use “predicted equals real” as a loop condition.
- Iteration is allowed only to improve internal consistency, reduce confidence conflicts, add discriminating experiments, and make the final confidence report stronger.
- Exit criteria are based on coverage and confidence:
  - all required LLVM-facing fields are either inferred with evidence, assumed with justification, or marked non-identifiable,
  - repeated experiments are stable within the configured tolerance,
  - pairwise/resource classifications are internally consistent,
  - unresolved conflicts are documented with concrete risks and follow-up experiments.

The final Humanize2 replay flow must preserve both modes:

- `synthetic_calibration`: with cmodel ground truth and mismatch repair loop.
- `real_platform_profile`: without golden values, using confidence-based stopping and human approval before LLVM implementation.

## RLCR And Multi-Agent Execution Plan

Execution starts only after this plan is approved for implementation.

Coordinator setup:

```bash
"/home/zhaosiying/.codex/skills/humanize/scripts/setup-rlcr-loop.sh" docs/plan.md --agent-teams --codex-model gpt-5.5:xhigh --max 42 --skip-quiz
```

Coordinator rules:

- The main agent owns RLCR state and is the only process allowed to run `rlcr-stop-gate.sh`.
- The main agent assigns independent tasks to workers.
- The main agent reviews worker changes, resolves conflicts, runs integration tests, commits, writes RLCR summaries, and runs the gate.

Worker rules:

- Use `gpt-5.5` with `xhigh` reasoning when the platform allows model override.
- Work in disjoint directories or isolated worktrees.
- Do not edit `.humanize/`.
- Do not start or stop RLCR.
- Do not run `rlcr-stop-gate.sh`.
- Return changed paths, verification commands, and unresolved risks.

Parallelizable work packages:

- Worker A: LLVM read-only extractor and mapping docs.
- Worker B: gem5 RVV kill-check assembly and runner.
- Worker C: timestamp marker implementation and trace schema.
- Worker D: assembly generator and template metadata.
- Worker E: analyzer, fitting, and parameter search.
- Worker F: results schema validation and report generation.
- Worker G: Humanize2 primitive capture, cartridge draft, and replay documentation.
- Worker H: gated LLVM 22.1.3 YuShuXin schedule-model implementation and LLVM tests.

Sequential integration gates:

1. Kill-check must pass before timestamp and timing-model patches are treated as production path.
2. Timestamp baseline must pass before latency experiments are trusted.
3. Timing-model synthetic ground truth must be configured before analyzer validation.
4. Analyzer must pass synthetic mismatch checks before LLVM draft export.
5. LLVM worktree implementation must wait until synthetic calibration agrees with cmodel ground truth for all claimed fields.
6. Real platform runs must use confidence-based stopping and require human approval before LLVM implementation because no per-instruction golden values exist.

RLCR per-round requirements:

- Read the current `.humanize/rlcr/<timestamp>/round-N-prompt.md`.
- Integrate worker outputs.
- Run the focused verification command for the round.
- Commit changes.
- Write `.humanize/rlcr/<timestamp>/round-N-summary.md`.
- Run:

```bash
"/home/zhaosiying/.codex/skills/humanize/scripts/rlcr-stop-gate.sh"
```

## Humanize2 Primitive Capture Plan

Implementation must continuously record enough structured workflow data to reconstruct the final one-command agentic flow as a Humanize2 cartridge. This is not a final retrospective activity; every implementation round must update the capture artifacts while the prompts, tool calls, decisions, and control flow are still fresh.

Humanize2 concepts to mirror:

- `h2-workflow`: top-level replayable workflow cartridge.
- `h2-manifest`: declared capabilities for agents, scripts, artifact schemas, human input, and dashboard views.
- `h2-state`: persistent `h2-board`, `h2-artifact`, and `h2-event` definitions.
- `h2-template`: reusable prompt bodies.
- `h2-flow`: executable control-flow graph.
- Executable nodes: `h2-check`, `h2-agent`, `h2-human`, `h2-transform`, `h2-loop`, `h2-branch`, `h2-parallel`, `h2-await`, `h2-message`, `h2-sleep`, and `h2-end`.
- Agent contracts: `h2-input`, `h2-expect`, and soft `h2-hook`.
- Runtime surfaces: `agent_run`, `agent_spawn_child`, `agent_send_message`, `agent_wait`, `artifact_deliver`, `artifact_get`, `board_patch`, `board_get`, `event_emit`, `human_request`, `human_answer`, and `view_publish`.

The implementation must create this capture tree:

```text
results/common/agentic_flow/
  h2_manifest_notes.md
  h2_primitives.yaml
  boards/
    goal_tracker.yaml
    execution_state.yaml
    simulator_selection.yaml
    experiment_matrix.yaml
    inference_state.yaml
  artifacts/
    prompts/
      <prompt-id>.md
    tool_calls/
      <tool-call-id>.json
    worker_contracts/
      <worker-id>.md
    worker_outputs/
      <worker-id>.md
    decisions/
      <decision-id>.md
    verification/
      <verification-id>.md
  events.jsonl
  views/
    status_panel.html
  cartridges/
    rvv-profile-workflow.draft.html
  replay.md
```

`h2_primitives.yaml` must classify every reusable workflow primitive:

```yaml
schema_version: 1
workflow:
  id: rvv-profile-workflow
  source_plan: docs/plan.md
manifest:
  capabilities:
    agent_tools: [codex]
    scripts:
      - check_env
      - run_killcheck
      - run_suite
      - analyze
      - export_llvm_draft
    artifact_schemas:
      - rvv.prompt.v1
      - rvv.toolCall.v1
      - rvv.workerContract.v1
      - rvv.workerOutput.v1
      - rvv.decision.v1
      - rvv.verification.v1
    human_input: true
    view: true
templates: []
boards: []
artifacts: []
events: []
flow_nodes: []
```

Every prompt used by the coordinator or a worker must be saved under `artifacts/prompts/` and registered in `h2_primitives.yaml` as an `h2-template` candidate. The saved prompt must include:

- prompt ID,
- task owner,
- target files/directories,
- allowed write scope,
- required inputs,
- expected artifacts,
- model and reasoning effort requested,
- timeout assumptions,
- exact success criteria.

Every tool call that changes state or produces verification evidence must be saved under `artifacts/tool_calls/` as normalized JSON:

```json
{
  "id": "tool-run-killcheck-001",
  "round": 1,
  "primitive": "h2-script",
  "tool_surface": "shell",
  "command": "python3 scripts/run_suite.py --killcheck",
  "cwd": "/home/zhaosiying/codebase/compiler/profile_inst_latency",
  "inputs": ["docs/plan.md", "config/paths.yaml"],
  "outputs": ["results/common/experiments"],
  "exit_code": 0,
  "evidence_path": "results/common/agentic_flow/artifacts/verification/killcheck-001.md"
}
```

Every major decision must be logged as an event and artifact:

- `simulator.killcheck.pass`
- `simulator.killcheck.fail`
- `timestamp.baseline.pass`
- `timing_model.ground_truth.updated`
- `experiment.generated`
- `experiment.run.completed`
- `analysis.conflict.detected`
- `worker.dispatched`
- `worker.completed`
- `integration.conflict.resolved`
- `human.approval.required`
- `llvm.export.generated`
- `profile.mode.selected`
- `synthetic.golden.match`
- `synthetic.golden.mismatch`
- `real_platform.confidence.stop`
- `llvm.yushuxin.worktree.created`
- `llvm.yushuxin.tests.passed`

`events.jsonl` must use one JSON object per event:

```json
{"time":"2026-05-23T00:00:00+08:00","round":1,"type":"worker.dispatched","data":{"worker":"B","contract":"artifacts/worker_contracts/worker-b.md"}}
```

The draft cartridge `cartridges/rvv-profile-workflow.draft.html` must be updated at phase boundaries, not only at the end. It should initially be a coarse cartridge with `h2-check` and `h2-agent` nodes for each phase. As implementation stabilizes, replace coarse nodes with concrete `h2-parallel`, `h2-loop`, `h2-branch`, `h2-transform`, and `h2-await` structure that mirrors the actual successful execution.

Minimum cartridge shape:

```html
<h2-workflow id="rvv-profile-workflow" name="RVV Profile Workflow" version="0.1.0" schema="humanize2.workflow.html.v1">
  <h2-manifest>
    <h2-capability name="agent" tools="codex"></h2-capability>
    <h2-capability name="artifact" schemas="rvv.prompt.v1,rvv.toolCall.v1,rvv.workerOutput.v1,rvv.verification.v1"></h2-capability>
    <h2-capability name="script" allow="check_env,run_killcheck,run_suite,analyze,export_llvm_draft"></h2-capability>
    <h2-capability name="human-input"></h2-capability>
    <h2-capability name="view"></h2-capability>
  </h2-manifest>
  <h2-state>
    <h2-board id="execution-state" schema="rvv.executionState.v1"></h2-board>
    <h2-board id="experiment-matrix" schema="rvv.experimentMatrix.v1"></h2-board>
    <h2-board id="inference-state" schema="rvv.inferenceState.v1"></h2-board>
  </h2-state>
  <h2-template id="llvm-extractor-prompt" type="prompt">
    Read the implementation plan and the LLVM RISC-V schedule files listed in it. Do not modify LLVM.
    Deliver llvm-field-map with the 10 selected RVV instruction IDs, their target SchedWrite families, and the LLVM fields that profiling must infer.
  </h2-template>
  <h2-template id="timestamp-baseline-prompt" type="prompt">
    Implement or verify the zero-cost timestamp marker path described by the plan. Run T00_BASELINE_MARKER and deliver timestamp-baseline with status pass or fail, trace paths, and marker delta evidence.
  </h2-template>
  <h2-template id="simulator-comparison-prompt" type="prompt">
    The gem5 RVV kill-check failed. Compare gem5, Spike plus timing wrapper, and one additional RVV-capable simulator. Deliver simulator-comparison with RVV support, timing expressiveness, custom marker feasibility, and recommended next baseline.
  </h2-template>
  <h2-flow>
    <h2-check id="env-check" uses="check_env"></h2-check>
    <h2-agent id="llvm-extractor" role="worker" tool="codex" prompt="#llvm-extractor-prompt" short-name="llvm-extractor" timeout="45m">
      <h2-expect artifact="llvm-field-map" schema="rvv.verification.v1"></h2-expect>
    </h2-agent>
    <h2-branch id="killcheck-route" on="artifact.killcheck.status">
      <h2-case value="pass" goto="timestamp-baseline"></h2-case>
      <h2-default goto="simulator-candidate-comparison"></h2-default>
    </h2-branch>
    <h2-agent id="timestamp-baseline" role="worker" tool="codex" prompt="#timestamp-baseline-prompt" short-name="timestamp-baseline" timeout="45m">
      <h2-expect artifact="timestamp-baseline" schema="rvv.verification.v1"></h2-expect>
    </h2-agent>
    <h2-agent id="simulator-candidate-comparison" role="worker" tool="codex" prompt="#simulator-comparison-prompt" short-name="simulator-compare" timeout="45m">
      <h2-expect artifact="simulator-comparison" schema="rvv.verification.v1"></h2-expect>
    </h2-agent>
    <h2-end id="complete"></h2-end>
  </h2-flow>
</h2-workflow>
```

`replay.md` must explain how to replay the final workflow in an empty-context session:

- required checkout paths,
- environment variables,
- how to build/start Humanize2 hub if available,
- how to load the draft cartridge,
- fallback commands when Humanize2 MCP is unavailable,
- exact order of scripts,
- expected artifacts after each phase,
- how to resume after failure using the recorded boards/events/artifacts.

Per-round coordinator checklist:

- Update `boards/execution_state.yaml`.
- Save all new coordinator and worker prompts.
- Save state-changing or verification tool calls.
- Append events for dispatch, completion, verification, branch decisions, and conflicts.
- Update the draft cartridge when a new stable control-flow segment is discovered.
- Include the agentic-flow capture delta in the RLCR round summary.

## One-Command Empty-Context Handoff

The implementation should eventually provide:

```bash
python3 scripts/check_env.py
python3 scripts/run_suite.py --killcheck
python3 scripts/run_suite.py --all
python3 scripts/analyze.py --all
python3 scripts/export_llvm_draft.py
python3 scripts/check_calibration_gate.py --mode synthetic_calibration
python3 scripts/prepare_llvm_yushuxin_worktree.py --tag llvmorg-22.1.3 --cpu YuShuXin
```

The final empty-context instruction for a fresh Codex session should be:

```text
Read docs/plan.md. Start humanize RLCR with docs/plan.md. Use gem5 MinorCPU as baseline. Do not modify llvm-project-21. Run the kill-check first. Parallelize only the work packages listed in the plan, using isolated writable directories. Keep results under results/.
```

For synthetic cmodel calibration, the final LLVM implementation phase is allowed only after `check_calibration_gate.py --mode synthetic_calibration` passes. For a real Paladin run, do not run the LLVM implementation phase automatically; produce the confidence report and ask for explicit human approval because no per-instruction golden latency table exists.

When Humanize2 is available, the empty-context handoff should instead prefer:

```text
Read docs/plan.md and results/common/agentic_flow/replay.md. Start the Humanize2 hub, load results/common/agentic_flow/cartridges/rvv-profile-workflow.draft.html, deliver docs/plan.md as the implementation-plan artifact, and execute the workflow. If Humanize2 is unavailable, follow replay.md fallback commands exactly.
```

## Acceptance Criteria

- AC-1: The plan is executable from an empty context and identifies exact phases, files, and verification commands.
- AC-2: LLVM is not modified in the first platform-first phase.
- AC-3: gem5 MinorCPU is the first simulator baseline, with an explicit RVV kill-check and fallback candidate-comparison path.
- AC-4: The first instruction set has 10 non-memory RVV instructions spanning distinct schedule families.
- AC-5: First matrix uses `SEW=e32` and `LMUL={m1,m2,m4}`.
- AC-6: Timestamp markers are zero-cost simulator annotations and do not occupy issue bandwidth.
- AC-7: Results are recorded under `results/common/` and one folder per instruction.
- AC-8: Profiles record LLVM-facing fields first and hardware interpretation fields second.
- AC-9: Analysis uses rule inference plus parameter search consistency checks.
- AC-10: Synthetic configured values are compared against inferred values and mismatches are reported.
- AC-11: Future implementation runs through Humanize RLCR with the main agent coordinating and workers isolated from RLCR state.
- AC-12: Implementation continuously records Humanize2-style prompts, tool calls, boards, artifacts, events, decisions, and control flow under `results/common/agentic_flow/`.
- AC-13: The final workflow can be replayed from `results/common/agentic_flow/replay.md` and a draft Humanize2 cartridge without relying on the original chat transcript.
- AC-14: Synthetic cmodel mode distinguishes golden-value calibration from real-platform profiling and records the active mode in results and agentic-flow state.
- AC-15: The `YuShuXin` LLVM 22.1.3 schedule-model implementation starts only after synthetic calibration matches all claimed cmodel ground-truth fields.
- AC-16: Real Paladin/platform profiling never uses golden equality as an exit condition; it stops on coverage, stability, confidence, documented assumptions, and explicit human approval before LLVM implementation.
- AC-17: The LLVM implementation is created in an isolated `llvmorg-22.1.3` worktree and includes RISC-V backend model changes plus focused CodeGen/llvm-mca tests for `-mcpu=YuShuXin`.

## Open Risks

- gem5's current RVV implementation may execute the chosen instructions functionally but require nontrivial work to expose per-RVV-instruction timing hooks in MinorCPU.
- Some instructions, especially mask/reduction forms, may have implicit passthru or mask dependencies that make naive RAW templates invalid.
- Zero-cost markers are easier to reason about but do not model a real custom instruction; hardware migration will need a separate `TIMESTAMP xN` backend using GPR/memory result export.
- LLVM's `ReadAdvance` may not be identifiable from a single consumer type; the first version should mark unknown or assumed fields honestly.
- Separate physical writeback latency is not directly an LLVM field; first-version output should avoid claiming it as independently identified unless the simulator model exposes it.
- Humanize2 `h2-dev` is transitional. The implementation must record a fallback `replay.md` path using plain scripts and RLCR even if the Humanize2 MCP hub or cartridge runner changes.
- The local LLVM tag spelling must be verified before worktree creation. Prior local evidence suggests `llvmorg-22.1.3`, but implementation must check the current repo instead of assuming it.
- `YuShuXin` exact-case CPU naming may interact with LLVM's RISC-V CPU parser conventions. The implementation must test the exact `-mcpu=YuShuXin` spelling and report if LLVM requires a lowercase alias or additional parser wiring.
- The synthetic cmodel can drive prompt/template repair through golden mismatch loops; the real platform cannot. If the final Humanize2 cartridge accidentally depends on golden equality, it is not valid for Paladin deployment.
