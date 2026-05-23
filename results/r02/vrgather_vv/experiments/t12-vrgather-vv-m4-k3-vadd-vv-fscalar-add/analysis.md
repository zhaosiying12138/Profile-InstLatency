# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r02/vrgather_vv/experiments/t12-vrgather-vv-m4-k3-vadd-vv-fscalar-add/trace.json`
- Experiment ID: `t12-vrgather-vv-m4-k3-vadd-vv-fscalar-add`
- Template ID: `T12_CONSUMER_RAW_GAP`
- Mode: `real_platform_profile`
- Instruction: `vrgather_vv`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 24 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 24 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
