# LLVM RVV Schedule Model Profiling Blog V2 Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` for task-by-task execution. The exact timing figures must be derived from checked-in experiment evidence before any GPT Image redraw is accepted.

**Goal:** Upgrade `blogs/llvm-rvv-sched-model-profile.html` into a Chinese technical-whitepaper article whose figures, tables, and TableGen sketches are grounded in real `gem5_minor` experiments for `vdivu.vv`.

**Architecture:** The article uses real gem5 artifacts as the primary evidence chain: `test.s` gives the instruction sequence, `trace.json` gives marker cycles, `gem5/exec.log` gives dynamic instruction cycles, and `profile.real_platform.yaml` plus `search_model_real_platform_summary.md` give inferred LLVM-facing values. Deterministic SVG/JSON evidence is generated first; GPT Image redraws then replace the old generic PNG assets while the HTML keeps deterministic tables and code snippets as the numeric authority.

**Tech Stack:** Static HTML/CSS, RVV assembly, gem5 MinorCPU Exec traces, repository profiling YAML/JSON/Markdown artifacts, deterministic SVG/PNG reference diagrams, GPT Image2 final redraws.

---

## User-Confirmed Scope

- Language: Chinese.
- Tone: technical whitepaper, concise and source-grounded.
- Main output: `blogs/llvm-rvv-sched-model-profile.html`.
- Asset directory: `blogs/assets/`.
- Representative instruction: `vdivu.vv`.
- Primary evidence mode: real platform profile, `backend: gem5_minor`.
- Synthetic calibration: keep only as a short contrast explaining why old `profile.yaml` and `mismatch_report.md` are calibration artifacts, not the main real-platform TableGen values.
- Required fields:
  - `IssueWidth`
  - `MicroOpBufferSize`
  - `ProcResource` / `ProcResGroup`
  - `Latency`
  - `ReleaseAtCycles`
  - `AcquireAtCycles`
  - `NumMicroOps`
  - `SingleIssue` / `BeginGroup` / `EndGroup`
  - `ReadAdvance`
  - `LMUL scaling`
  - `timestamp_model`
- Each field gets a real-experiment figure.
- `Latency`, `ReleaseAtCycles`, `AcquireAtCycles`, and `LMUL scaling` also get one integrated comprehensive figure that shows mixed LMULs, dependent and independent instructions, filler instructions, issue cycles, observed gaps, and bubbles in one sequence.
- Exact timing diagrams may be drawn as SVG/HTML first, but the final visible PNG assets must be redrawn with GPT Image2 and must match the deterministic SVG content.
- Old generic PNGs must not remain as article figures.
- LLVM implementation depth: TableGen draft/sketch level, not an upstream patch.

## Primary Real Evidence

- Global processor assumptions:
  - `results/common/processor.yaml`
  - `results/common/experiment_quality.md`
- Real `vdivu.vv` inferred values:
  - `results/vdivu_vv/profile.real_platform.yaml`
  - `results/common/search_model_real_platform_summary.md`
- Existing real experiments to cite and draw:
  - T10 independent stream:
    - `results/r01/vdivu_vv/experiments/t10-vdivu-vv-m1-n4/test.s`
    - `results/r01/vdivu_vv/experiments/t10-vdivu-vv-m1-n4/trace.json`
    - `results/r01/vdivu_vv/experiments/t10-vdivu-vv-m1-n4/gem5/exec.log`
  - T11 self RAW chain:
    - `results/r01/vdivu_vv/experiments/t11-vdivu-vv-m1-n4/test.s`
    - `results/r01/vdivu_vv/experiments/t11-vdivu-vv-m1-n4/trace.json`
    - `results/r01/vdivu_vv/experiments/t11-vdivu-vv-m1-n4/gem5/exec.log`
  - T12 consumer RAW gap:
    - `results/r01/vdivu_vv/experiments/t12-vdivu-vv-m1-k4-vadd-vv/test.s`
    - `results/r01/vdivu_vv/experiments/t12-vdivu-vv-m1-k4-vadd-vv/trace.json`
    - `results/r01/vdivu_vv/experiments/t12-vdivu-vv-m1-k4-vadd-vv/gem5/exec.log`
  - T20 pairwise pipe classification:
    - `results/r01/vdivu_vv/experiments/t20-vdivu-vv-vredsum-vs-m1-n4/test.s`
    - `results/r01/vdivu_vv/experiments/t20-vdivu-vv-vredsum-vs-m1-n4/trace.json`
    - `results/r01/vdivu_vv/experiments/t20-vdivu-vv-vredsum-vs-m1-n4/gem5/exec.log`
  - T21 scalar pairing:
    - `results/r01/vdivu_vv/experiments/t21-vdivu-vv-m1-n4/test.s`
    - `results/r01/vdivu_vv/experiments/t21-vdivu-vv-m1-n4/trace.json`
    - `results/r01/vdivu_vv/experiments/t21-vdivu-vv-m1-n4/gem5/exec.log`
  - T00 timestamp marker:
    - `results/r01/common/experiments/t00-marker/test.s`
    - `results/r01/common/experiments/t00-marker/trace.json`
    - `results/r01/common/experiments/t00-marker/gem5/exec.log`

## New Comprehensive Experiment

Create one blog-specific experiment under `experiments/blog/vdivu-vv-composite-real/` and run it into `results/blog/vdivu_vv_composite/experiments/vdivu-vv-composite-real/`.

The experiment must:

- Use zero-cost `TIMESTAMP_MARK` labels.
- Include `vdivu.vv` at `e32,m1`, `e32,m2`, and `e32,m4`.
- Include an independent stream segment to show `ReleaseAtCycles`.
- Include a RAW chain segment to show `Latency`.
- Include a filler-gap segment (`vadd.vv` fillers before a dependent `vadd.vv`) to show how bubbles disappear when the gap covers readiness.
- Include a segment that illustrates the absence of claimed `AcquireAtCycles` and `ReadAdvance`: the article must state that the current evidence observes issue/readiness but does not infer delayed acquire or consumer-specific bypass fields.
- Save theory-vs-observed evidence in `results/blog/vdivu_vv_composite/experiments/vdivu-vv-composite-real/analysis.md`.

Expected real-platform values to use when deriving the theoretical schedule:

| LMUL | Latency | ReleaseAtCycles | ProcResource | NumMicroOps | SingleIssue |
| --- | ---: | ---: | --- | ---: | --- |
| `m1` | 4 | 1 | `YuShuXinVPipe0` | 1 | false |
| `m2` | 4 | 2 | `YuShuXinVPipe0` | 1 | false |
| `m4` | 4 | 4 | `YuShuXinVPipe0` | 1 | false |

Formula fits:

- `Latency = 4 + 0 * LMUL`
- `ReleaseAtCycles = 0 + 1 * LMUL`

## Figure Set

Every final PNG below must be regenerated from a deterministic SVG reference and saved under `blogs/assets/`.

- `issue-width.png`: T21 scalar pairing, dual-issue grouping, `IssueWidth = 2`.
- `micro-op-buffer-size.png`: in-order marker-window execution, `MicroOpBufferSize = 0`.
- `proc-resource.png`: T20 pairwise classification plus the global pipe-label mirror caveat, `YuShuXinVPipe0` canonical resource.
- `latency.png`: T11 RAW chain, `delta = 12` for four instructions, inferred `Latency = 4`.
- `release-at-cycles.png`: T10 independent stream, `delta = 3` for four `m1` instructions, inferred `ReleaseAtCycles = 1`.
- `acquire-at-cycles.png`: same stream/resource timeline with acquire-at-issue shown; current experiments do not infer a delayed `AcquireAtCycles` list.
- `num-micro-ops.png`: T10/T21 evidence for one dynamic micro-op per `vdivu.vv`, `NumMicroOps = 1`.
- `single-issue-group.png`: T21 vector+scalar pairing, `SingleIssue = false`; no `BeginGroup`/`EndGroup` claim.
- `read-advance.png`: T12 producer/filler/consumer gap, no consumer-specific `ReadAdvance` claim.
- `lmul-scaling.png`: m1/m2/m4 T10 evidence, release scales 1/2/4 while latency stays 4.
- `timestamp-model.png`: T00 adjacent marker evidence, zero-cost label marker.
- `composite-schedule.png`: new comprehensive mixed-LMUL example showing issue, execution/resource occupancy, dependency readiness, fillers, bubbles, and inferred fields together.

## Article Structure

1. Background: why LLVM schedule models need cycle-accurate profiling.
2. Evidence chain: `test.s` + `trace.json` + `exec.log` + `profile.real_platform.yaml` + gate report.
3. Field taxonomy: common processor fields versus instruction-local fields.
4. One section per required field:
   - field meaning in LLVM;
   - complete key assembly fragment;
   - marker and dynamic-cycle evidence;
   - diagram interpretation;
   - inferred value and TableGen sketch;
   - boundaries when the field is not claimed.
5. Comprehensive mixed-LMUL schedule section.
6. Real-platform TableGen draft for `vdivu.vv`.
7. Synthetic calibration contrast.
8. Summary of claimed fields, non-claimed fields, and follow-up experiments.

## Execution Tasks

### Task 1: Refresh Plan And Evidence

- [ ] Update this plan to real-gem5 primary evidence.
- [ ] Extract `vdivu.vv` real values from `profile.real_platform.yaml`.
- [ ] Extract marker deltas and dynamic instruction cycles from the listed real experiments.
- [ ] Confirm `experiment_quality.md` reports `Gate status: PASS`.

### Task 2: Add Comprehensive Experiment

- [ ] Create `experiments/blog/vdivu-vv-composite-real/experiment.yaml`.
- [ ] Create `experiments/blog/vdivu-vv-composite-real/test.s`.
- [ ] Run `python3 scripts/run_experiment.py experiments/blog/vdivu-vv-composite-real --mode real_platform_profile --backend gem5_minor --results-root results/blog`.
- [ ] Write `analysis.md` with observed marker cycles, selected `exec.log` rows, and theory-vs-observed interpretation.

### Task 3: Generate Deterministic Figures

- [ ] Create/update a small project-local generator for blog SVG references.
- [ ] Generate all SVG references and reference PNGs under `blogs/assets/reference/`.
- [ ] Ensure the deterministic figures use only values read from checked-in trace/profile evidence.

### Task 4: Redraw With GPT Image2

- [ ] For each reference PNG, call GPT Image2 to redraw the same content as a polished technical timing diagram.
- [ ] Save final assets under the exact `blogs/assets/*.png` filenames.
- [ ] Reject or regenerate any output that changes numeric values, instruction order, marker cycles, or highlighted conclusions.

### Task 5: Rewrite Blog HTML

- [ ] Replace the old article body with real-gem5 evidence.
- [ ] Include complete key assembly fragments for T10, T11, T12, T20, T21, T00, and the comprehensive experiment.
- [ ] Include trace excerpts and exec-log tables.
- [ ] Include TableGen sketches based on real-platform values.
- [ ] Include the synthetic calibration contrast without making it the main result.

### Task 6: Verify And Commit

- [ ] Verify HTML image references and anchors.
- [ ] Verify required field names appear.
- [ ] Verify article values match `profile.real_platform.yaml` and `search_model_real_platform_summary.md`.
- [ ] Run `pytest tests/test_file_line_limits.py -q`.
- [ ] Run `python3 -m html.parser blogs/llvm-rvv-sched-model-profile.html`.
- [ ] Confirm no touched documentation file exceeds 2000 lines.
- [ ] Commit the blog v2 work on the isolated branch.
