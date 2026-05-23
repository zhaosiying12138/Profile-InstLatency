# Worker G3-A Notes

## Scope

- Owned file: `scripts/gen_asm.py`
- Generated artifacts: `experiments/generated/**`
- Notes artifact: `results/common/agentic_flow/artifacts/worker_outputs/worker-g3-a.md`

## BitLesson

- Selector command: `bitlesson-selector --task "Worker G3-A: extend scripts/gen_asm.py T20 pair-count sweeps and vcpop_m m4 diagnostics without touching search/analyze artifacts" --paths "scripts/gen_asm.py,experiments/generated,results/common/agentic_flow/artifacts/worker_outputs/worker-g3-a.md" --bitlesson-file .humanize/bitlesson.md`
- Result: `LESSON_IDS: NONE`
- Rationale: `.humanize/bitlesson.md` has no lesson entries.

## Generated Templates

- T20 pair-count sweep now emits `T20_PAIRWISE_PIPE_CLASSIFICATION` IDs with `n2`, `n3`, `n4`, and `n6` where the longer count fits the no-reuse destination policy.
- Example full-count pair: `t20-vadd-vv-vsll-vv-m1-n2`, `t20-vadd-vv-vsll-vv-m1-n3`, `t20-vadd-vv-vsll-vv-m1-n4`, `t20-vadd-vv-vsll-vv-m1-n6`.
- Example LMUL m4 reuse pair: `t20-vadd-vv-vsll-vv-m4-n2`, `t20-vadd-vv-vsll-vv-m4-n3`, `t20-vadd-vv-vsll-vv-m4-n4`.
- `vcpop_m` LMUL m4 T10 rotated scalar destination IDs remain `t10-vcpop-m-m4-n2`, `t10-vcpop-m-m4-n4`, `t10-vcpop-m-m4-n6`, `t10-vcpop-m-m4-n8`, `t10-vcpop-m-m4-n12`.
- `vcpop_m` LMUL m4 fixed scalar destination IDs added: `t10-vcpop-m-m4-scalar-fixed-n2`, `t10-vcpop-m-m4-scalar-fixed-n4`, `t10-vcpop-m-m4-scalar-fixed-n6`, `t10-vcpop-m-m4-scalar-fixed-n8`, `t10-vcpop-m-m4-scalar-fixed-n12`.
- Non-chainable T11 suite entries are no longer emitted; `vcpop_m` LMUL m4 has zero `T11_SELF_RAW_CHAIN` entries in `suite_manifest.yaml`.

## Metadata Fields

- T20 body metadata adds `pair_count`, `instruction_pair`, `destinations`, per-instance `source_a`, `source_b`, and per-instance `destination_reused`.
- T20 `destination_allocation` records `vector_destination_count`, `scalar_destination_count`, `available_vector_output_groups`, `available_scalar_outputs`, `vector_register_reuse`, and `scalar_register_reuse`.
- T10 scalar-result metadata adds `destination_policy` and `scalar_dest_policy`; fixed scalar destinations set `register_reuse: true`.
- T11 metadata adds `true_raw_chain`, `scalar_raw_chain`, and `latency_evidence`.
- T12 metadata adds `producer_result_kind`, `consumer_kind`, `consumer_reads_producer`, `raw_path`, and `gap_sweep`.

## Commands

- `python3 -m py_compile scripts/gen_asm.py`
- `python3 scripts/gen_asm.py one --template T10_INDEPENDENT_STREAM_THROUGHPUT --instr vcpop_m --lmul m4 --iterations 4 --scalar-dest-policy fixed --output-root /tmp/profile-inst-latency-gen-check`
- `python3 scripts/gen_asm.py one --template T20_PAIRWISE_PIPE_CLASSIFICATION --instr vadd_vv --other-instr vsll_vv --lmul m4 --iterations 4 --output-root /tmp/profile-inst-latency-gen-check`
- `python3 scripts/gen_asm.py suite`
