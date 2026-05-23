# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vmul_vv/experiments/t20-vmul-vv-vredsum-vs-m4-n2/trace.json`
- Experiment ID: `t20-vmul-vv-vredsum-vs-m4-n2`
- Template ID: `T20_PAIRWISE_PIPE_CLASSIFICATION`
- Mode: `real_platform_profile`
- Instruction: `vmul_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 15 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 15 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
