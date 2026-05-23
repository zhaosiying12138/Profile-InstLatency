# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vmseq_vv/experiments/t30-vmseq-vv-t12-m4-k9/trace.json`
- Experiment ID: `t30-vmseq-vv-t12-m4-k9`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vmseq_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 44 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 44 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
