# LLVM RVV Schedule Model Profiling Blog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Chinese, technical-whitepaper-style HTML blog explaining which LLVM scheduling-model parameters must be profiled, using `vdivu.vv` as the single detailed instruction example and GPT Image2 diagrams as visual companions.

**Architecture:** The blog is a self-contained static HTML article under `blogs/`, with generated raster diagrams under `blogs/assets/`. Deterministic facts come from checked-in YAML, trace JSON, assembly snippets, and TableGen draft output; generated images are illustrative only and never the sole source of numeric truth.

**Tech Stack:** Static HTML/CSS, checked-in profiling artifacts under `results/`, RVV assembly snippets, LLVM TableGen snippets, GPT Image2 generated PNG assets.

---

## User-Confirmed Scope

- Language: Chinese.
- Tone: blog article with technical-whitepaper discipline; concise, non-colloquial, and principle-first.
- Main output: `blogs/llvm-rvv-sched-model-profile.html`.
- Asset directory: `blogs/assets/`.
- Representative instruction: `vdivu.vv` only.
- Broader instruction set: mention that the suite covers 10 instructions, but do not deeply explain all 10.
- Evidence format: combine `trace.json` marker deltas, `profile.yaml` inferred values, and `results/common/mismatch_report.md` PASS.
- Assembly format: show complete key experiment fragments, not every generated file in full.
- LLVM implementation depth: explain how to express the result in the TableGen draft, not how to land a full upstream LLVM patch.
- Unknown fields: state that current experiments cannot identify them and therefore the blog does not generate LLVM claims for those fields.
- Visual requirement: each parameter section gets a GPT Image2 visual; deterministic HTML tables and code blocks carry exact values.

## Source Evidence

- Planning background: `docs/plan.md`.
- LLVM concept notes: `docs/llvm-sched-model-notes.md`.
- Common processor profile: `results/common/processor.yaml`.
- LLVM field map: `results/common/llvm_field_map.yaml`.
- TableGen draft: `results/common/llvm_model_draft.td`.
- Synthetic calibration mismatch report: `results/common/mismatch_report.md`.
- Representative instruction profile: `results/vdivu_vv/profile.yaml`.
- Key experiments:
  - `results/vdivu_vv/experiments/t10-vdivu-vv-m1-n4/test.s`
  - `results/vdivu_vv/experiments/t10-vdivu-vv-m1-n4/trace.json`
  - `results/vdivu_vv/experiments/t11-vdivu-vv-m1-n4/test.s`
  - `results/vdivu_vv/experiments/t11-vdivu-vv-m1-n4/trace.json`
  - `results/vdivu_vv/experiments/t20-vdivu-vv-vredsum-vs-m1-n4/test.s`
  - `results/vdivu_vv/experiments/t20-vdivu-vv-vredsum-vs-m1-n4/trace.json`
  - `results/vdivu_vv/experiments/t30-vdivu-vv-t12-m1-k0/test.s`
  - `results/vdivu_vv/experiments/t30-vdivu-vv-t12-m1-k0/trace.json`

## Output Structure

- `docs/plan-blog.md`: this execution plan.
- `blogs/llvm-rvv-sched-model-profile.html`: final static blog.
- `blogs/assets/issue-width.png`
- `blogs/assets/micro-op-buffer-size.png`
- `blogs/assets/proc-resource.png`
- `blogs/assets/latency.png`
- `blogs/assets/release-at-cycles.png`
- `blogs/assets/acquire-at-cycles.png`
- `blogs/assets/num-micro-ops.png`
- `blogs/assets/single-issue-group.png`
- `blogs/assets/read-advance.png`
- `blogs/assets/lmul-scaling.png`
- `blogs/assets/timestamp-model.png`
- `results/common/experiment_quality.md`: keep as a short navigational main report under 2000 lines.
- `results/common/experiment_quality_repeatability_part1.md` and `results/common/experiment_quality_repeatability_part2.md`: keep long repeatability rows split under 2000 lines each.

## Article Sections

1. Background: why cycle-accurate profiling is needed before writing an LLVM scheduling model.
2. Field taxonomy: common processor fields versus instruction-specific fields.
3. `IssueWidth`: meaning, evidence from the processor profile, and TableGen `let IssueWidth = 2`.
4. `MicroOpBufferSize`: in-order meaning, evidence from the processor profile, and TableGen `let MicroOpBufferSize = 0`.
5. `ProcResource` / `ProcResGroup`: two vector pipes and `YuShuXinVPipe1` for `vdivu.vv`.
6. `Latency`: dependent-readiness meaning, T11/T12 assembly, marker delta, `Latency = 18/24/36`.
7. `ReleaseAtCycles`: resource-occupancy meaning, T10 assembly, marker delta, `ReleaseAtCycles = 6/8/12`.
8. `AcquireAtCycles`: delayed-resource acquisition meaning, current empty default, and why no LLVM claim is emitted.
9. `NumMicroOps`: issue-width pressure meaning, current non-identifiable state, and why no LLVM claim is emitted.
10. `SingleIssue` / `BeginGroup` / `EndGroup`: dispatch-group isolation meaning, current non-identifiable state, and why no LLVM claim is emitted.
11. `ReadAdvance`: consumer-specific bypass meaning, current non-identifiable state, and why no LLVM claim is emitted.
12. LMUL scaling: exact formulas `Latency = 12 + 6 * LMUL`, `ReleaseAtCycles = 4 + 2 * LMUL`, with LMUL interpreted as `m1=1`, `m2=2`, `m4=4`.
13. Timestamp model: zero-cost marker contract as methodology, not a target LLVM scheduling field.
14. TableGen expression: show the relevant `SchedMachineModel`, resources, and `YuShuXinWriteVIDivV_M1/M2/M4` draft definitions.
15. Boundary statement: synthetic calibration PASS, real hardware claims are separate.

## Image Prompts

Use GPT Image2 for each asset. The images must be clean technical timing diagrams with minimal English labels because exact Chinese text and numeric values are supplied by HTML beside each image.

- `issue-width.png`: dual-issue timeline showing at most two micro-ops entering one cycle group, with a third waiting.
- `micro-op-buffer-size.png`: in-order pipeline with no reorder buffer, arrows from decode to execute in program order.
- `proc-resource.png`: two vector pipes, one instruction pinned to pipe1 and flexible instructions able to use a group.
- `latency.png`: producer `vdivu.vv` result becoming visible to a dependent consumer after a long readiness interval.
- `release-at-cycles.png`: independent `vdivu.vv` stream occupying a vector resource for several cycles before release.
- `acquire-at-cycles.png`: contrast default acquire-at-issue versus delayed acquisition, with the default path emphasized.
- `num-micro-ops.png`: one instruction expanding into one or multiple scheduler micro-ops, with current evidence marked unknown by visual styling.
- `single-issue-group.png`: a dispatch group where an instruction may force begin/end group boundaries, with current evidence marked unknown.
- `read-advance.png`: two consumers reading the same producer result with hypothetical bypass arrows, current profile marked no claim.
- `lmul-scaling.png`: three lanes for LMUL m1/m2/m4 with increasing latency and resource occupancy bars.
- `timestamp-model.png`: zero-cost label markers bracketing code while the pipeline timeline remains unchanged.

## Tasks

### Task 1: Gather Fixed Evidence

**Files:**
- Read: `results/common/processor.yaml`
- Read: `results/common/mismatch_report.md`
- Read: `results/common/llvm_model_draft.td`
- Read: `results/vdivu_vv/profile.yaml`
- Read: key `test.s` and `trace.json` files listed above.

- [ ] Extract exact `vdivu.vv` values: resource `YuShuXinVPipe1`, latency `18/24/36`, release `6/8/12`, formulas, and non-claimed fields.
- [ ] Extract exact marker deltas for T10, T11, T20, and T30 examples.
- [ ] Extract exact TableGen draft snippets for machine model, resources, and `YuShuXinWriteVIDivV_M1/M2/M4`.

### Task 2: Repair Stop-Hook Documentation Size

**Files:**
- Modify: `results/common/experiment_quality.md`
- Modify: `results/common/experiment_quality_repeatability_part1.md`
- Modify: `results/common/experiment_quality_repeatability_part2.md`

- [ ] Preserve the current report summary and PASS/human-approval status in `results/common/experiment_quality.md`.
- [ ] Replace the giant repeatability table in the main report with links to the two split repeatability files.
- [ ] Regenerate or refresh the split repeatability files so each remains under 2000 lines.
- [ ] Verify `wc -l` for all three report files.

### Task 3: Generate GPT Image2 Assets

**Files:**
- Create: `blogs/assets/*.png`

- [ ] Generate the 11 visual assets listed in the Image Prompts section using GPT Image2.
- [ ] Move or copy each generated asset into `blogs/assets/` with the exact filenames listed above.
- [ ] Inspect the final asset list and verify every HTML-referenced image exists.

### Task 4: Write Static HTML Blog

**Files:**
- Create: `blogs/llvm-rvv-sched-model-profile.html`

- [ ] Build a readable article layout with a constrained main column, sticky section navigation, code blocks, evidence cards, and figure captions.
- [ ] Write the Chinese technical content for every section listed above.
- [ ] Include deterministic tables for exact values and claim status.
- [ ] Include complete key assembly fragments for T10, T11, T20, and T30/T12.
- [ ] Include trace JSON excerpts with start/end cycles and primary deltas.
- [ ] Include the TableGen draft snippets for the machine model, resources, and `vdivu.vv` LMUL writes.
- [ ] Explicitly state that generated images are visual aids and that numeric truth is in code/data blocks.

### Task 5: Verify

**Files:**
- Verify: `docs/plan-blog.md`
- Verify: `blogs/llvm-rvv-sched-model-profile.html`
- Verify: `blogs/assets/*.png`
- Verify: `results/common/experiment_quality*.md`

- [ ] Run `wc -l` on touched documentation and HTML files; no file may exceed 2000 lines.
- [ ] Run a local link/image-reference check for the HTML file.
- [ ] Search the blog for every required parameter name.
- [ ] Verify `vdivu.vv` values in the blog match `profile.yaml` and `llvm_model_draft.td`.
- [ ] Run `git status --short` and review the final diff without reverting unrelated pre-existing changes.

