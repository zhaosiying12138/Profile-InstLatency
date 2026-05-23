# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vmul_vv/experiments/t30-vmul-vv-t11-m4-n6/trace.json`
- Experiment ID: `t30-vmul-vv-t11-m4-n6`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vmul_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 23 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 23 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
