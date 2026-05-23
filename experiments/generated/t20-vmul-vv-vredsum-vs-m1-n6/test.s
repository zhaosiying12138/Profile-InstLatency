# Generated RVV profiling experiment.
# experiment_id: t20-vmul-vv-vredsum-vs-m1-n6
# template_id: T20_PAIRWISE_PIPE_CLASSIFICATION
# vector_shape: e32,m1
# markers: start=__rvv_profile_marker_t20_vmul_vv_vredsum_vs_m1_n6_start, end=__rvv_profile_marker_t20_vmul_vv_vredsum_vs_m1_n6_end
#
# Timestamp markers are emitted as zero-cost labels at the next instruction PC.
# experiment.yaml records the corresponding global symbols and marker semantics.

    .section .text
    .globl _start
_start:
    # Scalar setup used by vector length and scalar-pair probes.
    li x5, 64
    li x6, 1
    li x7, 2
    li x20, 20
    li x21, 21
    li x22, 22
    li x23, 23
    li x24, 24
    li x25, 25
    li x26, 26
    li x27, 27
    li x28, 28
    li x29, 29
    li x30, 30
    li x31, 31

    # Fixed first-version vector shape: SEW=e32, LMUL=m1.
    vsetvli x0, x5, e32, m1, ta, ma

    # Initialize aligned vector groups. Values are simple and non-zero
    # where divisor/index operands might otherwise create simulator noise.
    vmv.v.i v0, 1
    vmv.v.i v1, 2
    vmv.v.i v2, 3
    vmv.v.i v3, 4
    vmv.v.i v4, 5
    vmv.v.i v5, 6
    vmv.v.i v6, 7
    vmv.v.i v7, 1
    vmv.v.i v8, 2
    vmv.v.i v9, 3
    vmv.v.i v10, 4
    vmv.v.i v11, 5
    vmv.v.i v12, 6
    vmv.v.i v13, 7
    vmv.v.i v14, 1
    vmv.v.i v15, 2
    vmv.v.i v16, 3
    vmv.v.i v17, 4
    vmv.v.i v18, 5
    vmv.v.i v19, 6
    vmv.v.i v20, 7
    vmv.v.i v21, 1
    vmv.v.i v22, 2
    vmv.v.i v23, 3
    vmv.v.i v24, 4
    vmv.v.i v25, 5
    vmv.v.i v26, 6
    vmv.v.i v27, 7
    vmv.v.i v28, 1
    vmv.v.i v29, 2
    vmv.v.i v30, 3
    vmv.v.i v31, 4

    # Establish a reusable all-true mask input for mask instructions.
    vmseq.vi v0, v0, 1

    # Pairwise pipe classification. A and B share read-only sources.
    # marker start: zero-cost timestamp point at the next instruction PC.
    .globl __rvv_profile_marker_t20_vmul_vv_vredsum_vs_m1_n6_start
    __rvv_profile_marker_t20_vmul_vv_vredsum_vs_m1_n6_start:
    .Lrvv_profile_marker_t20_vmul_vv_vredsum_vs_m1_n6_start:
    vmul.vv v2, v0, v1
    vredsum.vs v3, v0, v1
    vmul.vv v4, v0, v1
    vredsum.vs v5, v0, v1
    vmul.vv v6, v0, v1
    vredsum.vs v7, v0, v1
    vmul.vv v8, v0, v1
    vredsum.vs v9, v0, v1
    vmul.vv v10, v0, v1
    vredsum.vs v11, v0, v1
    vmul.vv v12, v0, v1
    vredsum.vs v13, v0, v1
    # marker end: zero-cost timestamp point at the next instruction PC.
    .globl __rvv_profile_marker_t20_vmul_vv_vredsum_vs_m1_n6_end
    __rvv_profile_marker_t20_vmul_vv_vredsum_vs_m1_n6_end:
    .Lrvv_profile_marker_t20_vmul_vv_vredsum_vs_m1_n6_end:

    # Terminate through the conventional Linux exit syscall for runners that
    # execute the assembled program directly.
    li a0, 0
    li a7, 93
    ecall
