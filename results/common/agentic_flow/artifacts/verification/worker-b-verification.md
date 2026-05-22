# Verification: Worker B Backfill

Worker: B
Round: 0
Status: backfilled from `artifacts/worker_outputs/worker-b.md`

## Recorded Commands

```bash
python3 scripts/llvm_sched_extract.py --output results/common/llvm_field_map.yaml
python3 -m py_compile scripts/llvm_sched_extract.py
python3 scripts/llvm_sched_extract.py --llvm-root /no/such/llvm-project --output results/common/should-not-exist.yaml
grep -nE "^(  (vadd_vv|vsll_vv|vmul_vv|vdivu_vv|vmseq_vv|vcpop_m|viota_m|vslideup_vx|vrgather_vv|vredsum_vs):|    sched_write_family:|    discovery_status:)" results/common/llvm_field_map.yaml
```

## Caveat

These commands are preserved from Worker B's report and were not rerun by
Worker F3.
