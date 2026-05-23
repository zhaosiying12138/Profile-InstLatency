# Experiment Analysis

Status: analyzed synthetic trace evidence.

- Trace: `results/r01/common/experiments/t00-marker/trace.json`
- Experiment ID: `t00-marker`
- Template ID: `T00_BASELINE_MARKER`
- Mode: `real_platform_profile`
- Instruction: `unknown`
- LMUL: `m1`
- Marker baseline cycles: 0
- Marker count: 2
- Primary corrected delta: 0 cycles

## Marker Deltas

| From | To | Corrected delta cycles |
| --- | --- | ---: |
| `t0` | `t1` | 0 |

## LLVM-Facing Claims

LLVM-facing timing fields are claimable only through raw marker-delta inference across the relevant template family. Synthetic metadata is reference-only.
