# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vmseq_vv/experiments/t10-vmseq-vv-m2-n2/trace.json`
- Experiment ID: `t10-vmseq-vv-m2-n2`
- Template ID: `T10_INDEPENDENT_STREAM_THROUGHPUT`
- Mode: `real_platform_profile`
- Instruction: `vmseq_vv`
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
