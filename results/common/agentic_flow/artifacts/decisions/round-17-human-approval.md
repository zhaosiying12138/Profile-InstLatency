# Round 17 Human Approval Decision

Decision: approve the exact 9 current `non_identifiable` real-platform
LLVM-facing risk IDs as known accepted risks for the current artifact set.

The approval is recorded in `results/common/human_approval.json`, which is the
only gate-consumed artifact. The request artifact remains separate and records
that it was fulfilled by the approval artifact.

This approval does not claim exact hardware-derived values for the accepted
rows. It allows AC-16 to pass because coverage, repeatability, marker contract,
conflict status, documented assumptions, and explicit current-hash-bound human
approval are all present.

Bound artifacts:

- `results/common/human_approval.json`: `f85dc41ffdea94249da33fe9dad29b6879de51616463b806cf4c6cd27228f2fd`
- `results/common/real_platform_inventory.json`: `857590b16d9690eaa502f2fb589b8b0e79a20f5b6dba2112c44e02d01c379759`
- `results/common/real_platform_field_status.json`: `079cb94d27e98bdcf9df0ae0595a6e12b101e4c8c5a3d46f7d627dd4c81c1432`
- `results/common/search_model_real_platform.json`: `3d72fd2e87b517e3e7ba3699eb214b8f35874055f3ed51c519aa4671d5f002bd`
- `results/common/experiment_quality.md`: `57c8d84dff3816459fffbbdab3643e3c196bb6adc17b4db2dcc5accada9905ce`
- `results/common/real_platform_risk_acceptance_request.json`: `1605e9af6e64d5a8c77b466c7cd8ddf7ad68fe6fe161821e4fb5054418daa913`

Accepted risk IDs:

- `llvm_field_status:vcpop_m:m1:Latency:non_identifiable`
- `llvm_field_status:vcpop_m:m2:Latency:non_identifiable`
- `llvm_field_status:vcpop_m:m4:Latency:non_identifiable`
- `llvm_field_status:vcpop_m:m4:ReleaseAtCycles:non_identifiable`
- `llvm_field_status:vcpop_m:m4:ProcResource:non_identifiable`
- `llvm_field_status:vcpop_m:m4:NumMicroOps:non_identifiable`
- `llvm_field_status:vcpop_m:m4:SingleIssue:non_identifiable`
- `llvm_field_status:vrgather_vv:m4:Latency:non_identifiable`
- `llvm_field_status:vslideup_vx:m4:Latency:non_identifiable`
