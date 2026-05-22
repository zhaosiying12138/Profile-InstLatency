# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/common/experiments/t00-marker/trace.json`
- Experiment ID: `t00-marker`
- Template ID: `T00_BASELINE_MARKER`
- Mode: `synthetic_calibration`
- Instruction: `unknown`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 0 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `None` |
| `latency_cycles` | `1` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `0` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `t0` | `t1` | 0 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t00-marker` at `results/common/experiments/t00-marker/trace.json`.
