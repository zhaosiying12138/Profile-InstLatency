# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vmseq_vv/experiments/t21-vmseq-vv-m4-n4/trace.json`
- Experiment ID: `t21-vmseq-vv-m4-n4`
- Template ID: `T21_PAIR_WITH_SCALAR`
- Mode: `real_platform_profile`
- Instruction: `vmseq_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 32 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 32 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
