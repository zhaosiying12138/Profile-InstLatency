# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vmul_vv/experiments/t10-vmul-vv-m2-n12/trace.json`
- Experiment ID: `t10-vmul-vv-m2-n12`
- Template ID: `T10_INDEPENDENT_STREAM_THROUGHPUT`
- Mode: `real_platform_profile`
- Instruction: `vmul_vv`
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
