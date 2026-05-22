# Worker C Output

LESSON_IDS: NONE

## Scope

Implemented Phase 2-5 assembly experiment generation scaffolding inside the assigned Worker C paths.

## Changed Files

- `scripts/gen_asm.py`
- `templates/rvv_program.s.tpl`
- `experiments/generated/t00-marker/experiment.yaml`
- `experiments/generated/t00-marker/test.s`
- `experiments/generated/t01-vadd-vv-m1/experiment.yaml`
- `experiments/generated/t01-vadd-vv-m1/test.s`
- `experiments/generated/suite_manifest.yaml`
- `results/common/agentic_flow/artifacts/worker_outputs/worker-c.md`

## Implementation Notes

- Generator is Python stdlib-only and deterministic.
- Supported template IDs: `T00_BASELINE_MARKER`, `T01_DECODE_EXEC_KILLCHECK`, `T10_INDEPENDENT_STREAM_THROUGHPUT`, `T11_SELF_RAW_CHAIN`, `T12_CONSUMER_RAW_GAP`, `T20_PAIRWISE_PIPE_CLASSIFICATION`, `T21_PAIR_WITH_SCALAR`, `T30_LMUL_SCALING`.
- Supported instruction IDs: `vadd_vv`, `vsll_vv`, `vmul_vv`, `vdivu_vv`, `vmseq_vv`, `vcpop_m`, `viota_m`, `vslideup_vx`, `vrgather_vv`, `vredsum_vs`.
- Supported vector shape is fixed `e32` with LMUL values `m1`, `m2`, and `m4`.
- Generated assembly uses runner-facing `TIMESTAMP_MARK <label>` pseudo lines and does not require a real assembler for generation tests.
- Metadata records marker labels, parameters, instruction metadata, and a reproduction command.
- Suite manifest generation is available with `python3 scripts/gen_asm.py suite --manifest-only`.

## Commands Run

- `python3 scripts/gen_asm.py --help`
  - Result: passed after implementation.
- `python3 scripts/gen_asm.py one --template T00_BASELINE_MARKER`
  - Result: generated `experiments/generated/t00-marker/`.
- `python3 scripts/gen_asm.py one --template T01_DECODE_EXEC_KILLCHECK --instr vadd_vv --lmul m1`
  - Result: generated `experiments/generated/t01-vadd-vv-m1/`.
- `python3 scripts/gen_asm.py suite --manifest-only`
  - Result: generated `experiments/generated/suite_manifest.yaml` with 376 entries.
- `python3 scripts/gen_asm.py one --template T10_INDEPENDENT_STREAM_THROUGHPUT --instr vsll_vv --lmul m2 --output-root experiments/generated/_verify`
  - Result: passed; temporary verification output removed.
- `python3 scripts/gen_asm.py one --template T11_SELF_RAW_CHAIN --instr vmul_vv --lmul m4 --output-root experiments/generated/_verify`
  - Result: passed; temporary verification output removed.
- `python3 scripts/gen_asm.py one --template T12_CONSUMER_RAW_GAP --instr vmseq_vv --lmul m1 --filler-count 2 --output-root experiments/generated/_verify`
  - Result: passed; temporary verification output removed.
- `python3 scripts/gen_asm.py one --template T20_PAIRWISE_PIPE_CLASSIFICATION --instr vdivu_vv --other-instr vcpop_m --lmul m4 --output-root experiments/generated/_verify`
  - Result: passed; temporary verification output removed.
- `python3 scripts/gen_asm.py one --template T21_PAIR_WITH_SCALAR --instr vslideup_vx --lmul m2 --output-root experiments/generated/_verify`
  - Result: passed; temporary verification output removed.
- `python3 scripts/gen_asm.py one --template T30_LMUL_SCALING --shape T12_CONSUMER_RAW_GAP --instr vrgather_vv --lmul m4 --filler-count 2 --output-root experiments/generated/_verify`
  - Result: passed; temporary verification output removed.
- `python3 -m py_compile scripts/gen_asm.py`
  - Result: passed; generated `__pycache__` removed.

## Risks

- `TIMESTAMP_MARK` is intentionally a pseudo line; generated assembly remains runner/scaffolding input until marker lowering or simulator support exists.
- `T11_SELF_RAW_CHAIN` marks non-chainable instructions in metadata and comments; true dependency probes for those instructions should use `T12_CONSUMER_RAW_GAP`.
- For high LMUL pairwise tests, the generator caps default pair iterations where unique destination groups are limited by the RVV register file.
