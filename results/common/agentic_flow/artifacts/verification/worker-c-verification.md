# Verification: Worker C Backfill

Worker: C
Round: 0
Status: backfilled from `artifacts/worker_outputs/worker-c.md`

## Recorded Commands

```bash
python3 scripts/gen_asm.py --help
python3 scripts/gen_asm.py one --template T00_BASELINE_MARKER
python3 scripts/gen_asm.py one --template T01_DECODE_EXEC_KILLCHECK --instr vadd_vv --lmul m1
python3 scripts/gen_asm.py suite --manifest-only
python3 -m py_compile scripts/gen_asm.py
```

The Worker C output records additional temporary generation checks for T10, T11,
T12, T20, T21, and T30 templates.

## Caveat

These commands are preserved from Worker C's report and were not rerun by
Worker F3.
