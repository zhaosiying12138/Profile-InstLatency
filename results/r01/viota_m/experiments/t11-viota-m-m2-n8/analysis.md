# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/viota_m/experiments/t11-viota-m-m2-n8/trace.json`
- Experiment ID: `t11-viota-m-m2-n8`
- Template ID: `T11_SELF_RAW_CHAIN`
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
