# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/common/experiments/t40-common-vlsu-load-hit-m1/trace.json`
- Experiment ID: `t40-common-vlsu-load-hit-m1`
- Template ID: `T40_COMMON_VLSU_LOAD_HIT`
- Mode: `synthetic_calibration`
- Instruction: `unknown`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 2 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `None` |
| `latency_cycles` | `1` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `2` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 2 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t40-common-vlsu-load-hit-m1` at `results/common/experiments/t40-common-vlsu-load-hit-m1/trace.json`.
