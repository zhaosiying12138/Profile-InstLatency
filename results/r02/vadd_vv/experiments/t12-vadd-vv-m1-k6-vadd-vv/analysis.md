# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vadd_vv/experiments/t12-vadd-vv-m1-k6-vadd-vv/trace.json`
- Experiment ID: `t12-vadd-vv-m1-k6-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `real_platform_profile`
- Instruction: `vadd_vv`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 7 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 7 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
