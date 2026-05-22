# Worker B Output

LESSON_IDS: NONE

## Scope

Owned files for Phase 1 read-only LLVM schedule extraction:

- `scripts/llvm_sched_extract.py`
- `docs/llvm-sched-model-notes.md`
- `results/common/llvm_field_map.yaml`
- `results/common/agentic_flow/artifacts/worker_outputs/worker-b.md`

## Notes

- Read `.humanize/bitlesson.md`; it contains only the template and no lesson entries.
- Did not run the unsafe external bitlesson selector.
- Did not edit `.humanize/rlcr/**` or `docs/plan.md`.

## Commands Run

- `python3 scripts/llvm_sched_extract.py --output results/common/llvm_field_map.yaml`
  - Result: exit 0; wrote 10 instruction records.
- `python3 -m py_compile scripts/llvm_sched_extract.py`
  - Result: exit 0.
- `python3 scripts/llvm_sched_extract.py --llvm-root /no/such/llvm-project --output results/common/should-not-exist.yaml`
  - Result: exit 2 with an actionable missing-checkout error; no output file was created.
- `grep -nE "^(  (vadd_vv|vsll_vv|vmul_vv|vdivu_vv|vmseq_vv|vcpop_m|viota_m|vslideup_vx|vrgather_vv|vredsum_vs):|    sched_write_family:|    discovery_status:)" results/common/llvm_field_map.yaml`
  - Result: all 10 instruction IDs are present and all have `discovery_status: found`.

## Risks

- The extractor is a bounded text extractor, not a full TableGen evaluator. It records source evidence and subtarget examples deterministically, but it does not expand every generated TableGen record.
- Other workers have unrelated untracked files in the worktree; only Worker B owned files should be staged or committed.
