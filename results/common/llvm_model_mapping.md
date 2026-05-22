# YuShuXin LLVM Model Mapping

Status: generated_from_profile_evidence

The TableGen draft is generated from `results/<instruction>/profile.yaml`. Latency, ReleaseAtCycles, and resource fields below come from synthetic trace evidence; unclaimed fields remain comments in the draft.

## Instruction/LMUL Mapping

| Instruction | ASM | LMUL | SchedWrite def | Resource | Latency | ReleaseAtCycles | Evidence |
| --- | --- | --- | --- | --- | ---: | ---: | --- |
| `vadd_vv` | `vadd.vv` | `m1` | `YuShuXinWriteVIALUV_M1` | `YuShuXinAnyVPipe` | 2 | 1 | `t30-vadd-vv-t12-m1-k0 @ results/vadd_vv/experiments/t30-vadd-vv-t12-m1-k0/trace.json` |
| `vadd_vv` | `vadd.vv` | `m2` | `YuShuXinWriteVIALUV_M2` | `YuShuXinAnyVPipe` | 2 | 1 | `t30-vadd-vv-t12-m2-k0 @ results/vadd_vv/experiments/t30-vadd-vv-t12-m2-k0/trace.json` |
| `vadd_vv` | `vadd.vv` | `m4` | `YuShuXinWriteVIALUV_M4` | `YuShuXinAnyVPipe` | 2 | 1 | `t30-vadd-vv-t12-m4-k0 @ results/vadd_vv/experiments/t30-vadd-vv-t12-m4-k0/trace.json` |
| `vcpop_m` | `vcpop.m` | `m1` | `YuShuXinWriteVMPopV_M1` | `YuShuXinVPipe0` | 4 | 1 | `t30-vcpop-m-t12-m1-k0 @ results/vcpop_m/experiments/t30-vcpop-m-t12-m1-k0/trace.json` |
| `vcpop_m` | `vcpop.m` | `m2` | `YuShuXinWriteVMPopV_M2` | `YuShuXinVPipe0` | 5 | 1 | `t30-vcpop-m-t12-m2-k0 @ results/vcpop_m/experiments/t30-vcpop-m-t12-m2-k0/trace.json` |
| `vcpop_m` | `vcpop.m` | `m4` | `YuShuXinWriteVMPopV_M4` | `YuShuXinVPipe0` | 7 | 1 | `t30-vcpop-m-t12-m4-k0 @ results/vcpop_m/experiments/t30-vcpop-m-t12-m4-k0/trace.json` |
| `vdivu_vv` | `vdivu.vv` | `m1` | `YuShuXinWriteVIDivV_M1` | `YuShuXinVPipe1` | 18 | 6 | `t30-vdivu-vv-t12-m1-k0 @ results/vdivu_vv/experiments/t30-vdivu-vv-t12-m1-k0/trace.json` |
| `vdivu_vv` | `vdivu.vv` | `m2` | `YuShuXinWriteVIDivV_M2` | `YuShuXinVPipe1` | 24 | 8 | `t30-vdivu-vv-t12-m2-k0 @ results/vdivu_vv/experiments/t30-vdivu-vv-t12-m2-k0/trace.json` |
| `vdivu_vv` | `vdivu.vv` | `m4` | `YuShuXinWriteVIDivV_M4` | `YuShuXinVPipe1` | 36 | 12 | `t30-vdivu-vv-t12-m4-k0 @ results/vdivu_vv/experiments/t30-vdivu-vv-t12-m4-k0/trace.json` |
| `viota_m` | `viota.m` | `m1` | `YuShuXinWriteVIotaV_M1` | `YuShuXinVPipe0` | 6 | 2 | `t30-viota-m-t12-m1-k0 @ results/viota_m/experiments/t30-viota-m-t12-m1-k0/trace.json` |
| `viota_m` | `viota.m` | `m2` | `YuShuXinWriteVIotaV_M2` | `YuShuXinVPipe0` | 8 | 3 | `t30-viota-m-t12-m2-k0 @ results/viota_m/experiments/t30-viota-m-t12-m2-k0/trace.json` |
| `viota_m` | `viota.m` | `m4` | `YuShuXinWriteVIotaV_M4` | `YuShuXinVPipe0` | 12 | 5 | `t30-viota-m-t12-m4-k0 @ results/viota_m/experiments/t30-viota-m-t12-m4-k0/trace.json` |
| `vmseq_vv` | `vmseq.vv` | `m1` | `YuShuXinWriteVICmpV_M1` | `YuShuXinAnyVPipe` | 2 | 1 | `t30-vmseq-vv-t12-m1-k0 @ results/vmseq_vv/experiments/t30-vmseq-vv-t12-m1-k0/trace.json` |
| `vmseq_vv` | `vmseq.vv` | `m2` | `YuShuXinWriteVICmpV_M2` | `YuShuXinAnyVPipe` | 2 | 1 | `t30-vmseq-vv-t12-m2-k0 @ results/vmseq_vv/experiments/t30-vmseq-vv-t12-m2-k0/trace.json` |
| `vmseq_vv` | `vmseq.vv` | `m4` | `YuShuXinWriteVICmpV_M4` | `YuShuXinAnyVPipe` | 2 | 1 | `t30-vmseq-vv-t12-m4-k0 @ results/vmseq_vv/experiments/t30-vmseq-vv-t12-m4-k0/trace.json` |
| `vmul_vv` | `vmul.vv` | `m1` | `YuShuXinWriteVIMulV_M1` | `YuShuXinAnyVPipe` | 6 | 2 | `t30-vmul-vv-t12-m1-k0 @ results/vmul_vv/experiments/t30-vmul-vv-t12-m1-k0/trace.json` |
| `vmul_vv` | `vmul.vv` | `m2` | `YuShuXinWriteVIMulV_M2` | `YuShuXinAnyVPipe` | 7 | 3 | `t30-vmul-vv-t12-m2-k0 @ results/vmul_vv/experiments/t30-vmul-vv-t12-m2-k0/trace.json` |
| `vmul_vv` | `vmul.vv` | `m4` | `YuShuXinWriteVIMulV_M4` | `YuShuXinAnyVPipe` | 9 | 5 | `t30-vmul-vv-t12-m4-k0 @ results/vmul_vv/experiments/t30-vmul-vv-t12-m4-k0/trace.json` |
| `vredsum_vs` | `vredsum.vs` | `m1` | `YuShuXinWriteVIRedV_From_M1` | `YuShuXinVPipe1` | 9 | 2 | `t30-vredsum-vs-t12-m1-k0 @ results/vredsum_vs/experiments/t30-vredsum-vs-t12-m1-k0/trace.json` |
| `vredsum_vs` | `vredsum.vs` | `m2` | `YuShuXinWriteVIRedV_From_M2` | `YuShuXinVPipe1` | 12 | 3 | `t30-vredsum-vs-t12-m2-k0 @ results/vredsum_vs/experiments/t30-vredsum-vs-t12-m2-k0/trace.json` |
| `vredsum_vs` | `vredsum.vs` | `m4` | `YuShuXinWriteVIRedV_From_M4` | `YuShuXinVPipe1` | 18 | 5 | `t30-vredsum-vs-t12-m4-k0 @ results/vredsum_vs/experiments/t30-vredsum-vs-t12-m4-k0/trace.json` |
| `vrgather_vv` | `vrgather.vv` | `m1` | `YuShuXinWriteVRGatherVV_M1` | `YuShuXinVPipe1` | 7 | 2 | `t30-vrgather-vv-t12-m1-k0 @ results/vrgather_vv/experiments/t30-vrgather-vv-t12-m1-k0/trace.json` |
| `vrgather_vv` | `vrgather.vv` | `m2` | `YuShuXinWriteVRGatherVV_M2` | `YuShuXinVPipe1` | 9 | 3 | `t30-vrgather-vv-t12-m2-k0 @ results/vrgather_vv/experiments/t30-vrgather-vv-t12-m2-k0/trace.json` |
| `vrgather_vv` | `vrgather.vv` | `m4` | `YuShuXinWriteVRGatherVV_M4` | `YuShuXinVPipe1` | 13 | 5 | `t30-vrgather-vv-t12-m4-k0 @ results/vrgather_vv/experiments/t30-vrgather-vv-t12-m4-k0/trace.json` |
| `vslideup_vx` | `vslideup.vx` | `m1` | `YuShuXinWriteVSlideUpX_M1` | `YuShuXinVPipe0` | 4 | 1 | `t30-vslideup-vx-t12-m1-k0 @ results/vslideup_vx/experiments/t30-vslideup-vx-t12-m1-k0/trace.json` |
| `vslideup_vx` | `vslideup.vx` | `m2` | `YuShuXinWriteVSlideUpX_M2` | `YuShuXinVPipe0` | 5 | 1 | `t30-vslideup-vx-t12-m2-k0 @ results/vslideup_vx/experiments/t30-vslideup-vx-t12-m2-k0/trace.json` |
| `vslideup_vx` | `vslideup.vx` | `m4` | `YuShuXinWriteVSlideUpX_M4` | `YuShuXinVPipe0` | 7 | 1 | `t30-vslideup-vx-t12-m4-k0 @ results/vslideup_vx/experiments/t30-vslideup-vx-t12-m4-k0/trace.json` |
| `vsll_vv` | `vsll.vv` | `m1` | `YuShuXinWriteVShiftV_M1` | `YuShuXinAnyVPipe` | 4 | 2 | `t30-vsll-vv-t12-m1-k0 @ results/vsll_vv/experiments/t30-vsll-vv-t12-m1-k0/trace.json` |
| `vsll_vv` | `vsll.vv` | `m2` | `YuShuXinWriteVShiftV_M2` | `YuShuXinAnyVPipe` | 5 | 3 | `t30-vsll-vv-t12-m2-k0 @ results/vsll_vv/experiments/t30-vsll-vv-t12-m2-k0/trace.json` |
| `vsll_vv` | `vsll.vv` | `m4` | `YuShuXinWriteVShiftV_M4` | `YuShuXinAnyVPipe` | 7 | 5 | `t30-vsll-vv-t12-m4-k0 @ results/vsll_vv/experiments/t30-vsll-vv-t12-m4-k0/trace.json` |

## Non-Claims

- `NumMicroOps` is not emitted unless a profile marks it as claimed.
- `SingleIssue` is not emitted unless a profile marks it as claimed.
- `ReadAdvance` and physical writeback latency are not generated from current synthetic evidence.
- The draft uses per-LMUL write definitions so LMUL-dependent latency/release values are not collapsed into placeholders.
