# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/vmseq_vv/experiments/t12-vmseq-vv-m2-k0-vcpop-m/trace.json`
- Experiment ID: `t12-vmseq-vv-m2-k0-vcpop-m`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `synthetic_calibration`
- Instruction: `vmseq_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 2 cycles

## Synthetic Metadata

| Field | Value |
| --- | --- |
| `timing_model` | `config/rvv_timing_model.yaml` |
| `pipe` | `any` |
| `latency_cycles` | `2` |
| `release_cycles` | `1` |
| `measured_delta_cycles` | `2` |

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 2 |

## LLVM-Facing Claims

For synthetic calibration, configured latency, release, and pipe come from `t12-vmseq-vv-m2-k0-vcpop-m` at `results/vmseq_vv/experiments/t12-vmseq-vv-m2-k0-vcpop-m/trace.json`.
