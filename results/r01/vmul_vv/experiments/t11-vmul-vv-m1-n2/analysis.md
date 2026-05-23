# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vmul_vv/experiments/t11-vmul-vv-m1-n2/trace.json`
- Experiment ID: `t11-vmul-vv-m1-n2`
- Template ID: `T11_SELF_RAW_CHAIN`
- Mode: `real_platform_profile`
- Instruction: `vmul_vv`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 4 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 4 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
