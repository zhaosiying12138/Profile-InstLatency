# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vmseq_vv/experiments/t12-vmseq-vv-m4-k16-vcpop-m/trace.json`
- Experiment ID: `t12-vmseq-vv-m4-k16-vcpop-m`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `real_platform_profile`
- Instruction: `vmseq_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 72 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 72 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
