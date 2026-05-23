# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vadd_vv/experiments/t20-vadd-vv-vrgather-vv-m2-n3/trace.json`
- Experiment ID: `t20-vadd-vv-vrgather-vv-m2-n3`
- Template ID: `T20_PAIRWISE_PIPE_CLASSIFICATION`
- Mode: `real_platform_profile`
- Instruction: `vadd_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 23 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 23 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
