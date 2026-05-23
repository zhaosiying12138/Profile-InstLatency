# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/vredsum_vs/experiments/t11-vredsum-vs-m4-n12/trace.json`
- Experiment ID: `t11-vredsum-vs-m4-n12`
- Template ID: `T11_SELF_RAW_CHAIN`
- Mode: `real_platform_profile`
- Instruction: `vredsum_vs`
- LMUL: `m4`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 80 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `start` | `end` | 80 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
