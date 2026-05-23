# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/viota_m/experiments/t12-viota-m-m2-k6-vadd-vv/trace.json`
- Experiment ID: `t12-viota-m-m2-k6-vadd-vv`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `real_platform_profile`
- Instruction: `viota_m`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 15 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 15 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
