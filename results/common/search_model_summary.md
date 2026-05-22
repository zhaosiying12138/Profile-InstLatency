# Timing Parameter Search

Status: profile_parameter_search
Formula form: `base_plus_lmul_times_k`

## Inputs

- `results/vadd_vv/profile.yaml`
- `results/vcpop_m/profile.yaml`
- `results/vdivu_vv/profile.yaml`
- `results/viota_m/profile.yaml`
- `results/vmseq_vv/profile.yaml`
- `results/vmul_vv/profile.yaml`
- `results/vredsum_vs/profile.yaml`
- `results/vrgather_vv/profile.yaml`
- `results/vslideup_vx/profile.yaml`
- `results/vsll_vv/profile.yaml`

## Candidates

| Instruction | Field | Status | Formula | Residual |
| --- | --- | --- | --- | ---: |
| `vadd_vv` | `latency` | exact_fit | `2 + 0 * LMUL` | 0 |
| `vadd_vv` | `release` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vadd_vv` | `pipe_affinity` | exact_fit | `any` | 0 |
| `vadd_vv` | `resource_group` | exact_fit | `YuShuXinAnyVPipe` | 0 |
| `vcpop_m` | `latency` | exact_fit | `3 + 1 * LMUL` | 0 |
| `vcpop_m` | `release` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vcpop_m` | `pipe_affinity` | exact_fit | `pipe0` | 0 |
| `vcpop_m` | `resource_group` | exact_fit | `YuShuXinVPipe0` | 0 |
| `vdivu_vv` | `latency` | exact_fit | `12 + 6 * LMUL` | 0 |
| `vdivu_vv` | `release` | exact_fit | `4 + 2 * LMUL` | 0 |
| `vdivu_vv` | `pipe_affinity` | exact_fit | `pipe1` | 0 |
| `vdivu_vv` | `resource_group` | exact_fit | `YuShuXinVPipe1` | 0 |
| `viota_m` | `latency` | exact_fit | `4 + 2 * LMUL` | 0 |
| `viota_m` | `release` | exact_fit | `1 + 1 * LMUL` | 0 |
| `viota_m` | `pipe_affinity` | exact_fit | `pipe0` | 0 |
| `viota_m` | `resource_group` | exact_fit | `YuShuXinVPipe0` | 0 |
| `vmseq_vv` | `latency` | exact_fit | `2 + 0 * LMUL` | 0 |
| `vmseq_vv` | `release` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vmseq_vv` | `pipe_affinity` | exact_fit | `any` | 0 |
| `vmseq_vv` | `resource_group` | exact_fit | `YuShuXinAnyVPipe` | 0 |
| `vmul_vv` | `latency` | exact_fit | `5 + 1 * LMUL` | 0 |
| `vmul_vv` | `release` | exact_fit | `1 + 1 * LMUL` | 0 |
| `vmul_vv` | `pipe_affinity` | exact_fit | `any` | 0 |
| `vmul_vv` | `resource_group` | exact_fit | `YuShuXinAnyVPipe` | 0 |
| `vredsum_vs` | `latency` | exact_fit | `6 + 3 * LMUL` | 0 |
| `vredsum_vs` | `release` | exact_fit | `1 + 1 * LMUL` | 0 |
| `vredsum_vs` | `pipe_affinity` | exact_fit | `pipe1` | 0 |
| `vredsum_vs` | `resource_group` | exact_fit | `YuShuXinVPipe1` | 0 |
| `vrgather_vv` | `latency` | exact_fit | `5 + 2 * LMUL` | 0 |
| `vrgather_vv` | `release` | exact_fit | `1 + 1 * LMUL` | 0 |
| `vrgather_vv` | `pipe_affinity` | exact_fit | `pipe1` | 0 |
| `vrgather_vv` | `resource_group` | exact_fit | `YuShuXinVPipe1` | 0 |
| `vslideup_vx` | `latency` | exact_fit | `3 + 1 * LMUL` | 0 |
| `vslideup_vx` | `release` | exact_fit | `1 + 0 * LMUL` | 0 |
| `vslideup_vx` | `pipe_affinity` | exact_fit | `pipe0` | 0 |
| `vslideup_vx` | `resource_group` | exact_fit | `YuShuXinVPipe0` | 0 |
| `vsll_vv` | `latency` | exact_fit | `3 + 1 * LMUL` | 0 |
| `vsll_vv` | `release` | exact_fit | `1 + 1 * LMUL` | 0 |
| `vsll_vv` | `pipe_affinity` | exact_fit | `any` | 0 |
| `vsll_vv` | `resource_group` | exact_fit | `YuShuXinAnyVPipe` | 0 |
