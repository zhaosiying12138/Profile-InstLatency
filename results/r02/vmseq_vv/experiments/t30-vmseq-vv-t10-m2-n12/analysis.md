# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vmseq_vv/experiments/t30-vmseq-vv-t10-m2-n12/trace.json`
- Experiment ID: `t30-vmseq-vv-t10-m2-n12`
- Template ID: `T30_LMUL_SCALING`
- Mode: `real_platform_profile`
- Instruction: `vmseq_vv`
- LMUL: `m2`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 71 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 71 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
