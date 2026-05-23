# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/common/experiments/t01-vmseq-vv-m2/trace.json`
- Experiment ID: `t01-vmseq-vv-m2`
- Template ID: `T01_DECODE_EXEC_KILLCHECK`
- Mode: `real_platform_profile`
- Instruction: `vmseq_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 3
- Primary corrected delta: 5 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `before` | `after` | 5 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
