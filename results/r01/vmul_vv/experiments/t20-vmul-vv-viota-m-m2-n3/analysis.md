# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vmul_vv/experiments/t20-vmul-vv-viota-m-m2-n3/trace.json`
- Experiment ID: `t20-vmul-vv-viota-m-m2-n3`
- Template ID: `T20_PAIRWISE_PIPE_CLASSIFICATION`
- Mode: `real_platform_profile`
- Instruction: `vmul_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 11 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 11 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
