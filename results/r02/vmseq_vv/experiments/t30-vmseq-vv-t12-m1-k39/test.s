# Generated RVV profiling experiment.
# experiment_id: t30-vmseq-vv-t12-m1-k39
# template_id: T30_LMUL_SCALING
# vector_shape: e32,m1
# markers: start=__rvv_profile_marker_t30_vmseq_vv_t12_m1_k39_start, end=__rvv_profile_marker_t30_vmseq_vv_t12_m1_k39_end
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

    # Producer-consumer gap probe. Fillers are independent of the producer result.
    # marker start: zero-cost timestamp point at the next instruction PC.
    .globl __rvv_profile_marker_t30_vmseq_vv_t12_m1_k39_start
    __rvv_profile_marker_t30_vmseq_vv_t12_m1_k39_start:
    .Lrvv_profile_marker_t30_vmseq_vv_t12_m1_k39_start:
    vmseq.vv v2, v0, v1
    vadd.vv v4, v0, v1  # independent filler 0
    vadd.vv v5, v0, v1  # independent filler 1
    vadd.vv v6, v0, v1  # independent filler 2
    vadd.vv v7, v0, v1  # independent filler 3
    vadd.vv v8, v0, v1  # independent filler 4
    vadd.vv v9, v0, v1  # independent filler 5
    vadd.vv v10, v0, v1  # independent filler 6
    vadd.vv v11, v0, v1  # independent filler 7
    vadd.vv v12, v0, v1  # independent filler 8
    vadd.vv v13, v0, v1  # independent filler 9
    vadd.vv v14, v0, v1  # independent filler 10
    vadd.vv v15, v0, v1  # independent filler 11
    vadd.vv v16, v0, v1  # independent filler 12
    vadd.vv v17, v0, v1  # independent filler 13
    vadd.vv v18, v0, v1  # independent filler 14
    vadd.vv v19, v0, v1  # independent filler 15
    vadd.vv v20, v0, v1  # independent filler 16
    vadd.vv v21, v0, v1  # independent filler 17
    vadd.vv v22, v0, v1  # independent filler 18
    vadd.vv v23, v0, v1  # independent filler 19
    vadd.vv v24, v0, v1  # independent filler 20
    vadd.vv v25, v0, v1  # independent filler 21
    vadd.vv v26, v0, v1  # independent filler 22
    vadd.vv v27, v0, v1  # independent filler 23
    vadd.vv v28, v0, v1  # independent filler 24
    vadd.vv v29, v0, v1  # independent filler 25
    vadd.vv v30, v0, v1  # independent filler 26
    vadd.vv v31, v0, v1  # independent filler 27
    vadd.vv v2, v0, v1  # independent filler 28
    vadd.vv v3, v0, v1  # independent filler 29
    vadd.vv v4, v0, v1  # independent filler 30
    vadd.vv v5, v0, v1  # independent filler 31
    vadd.vv v6, v0, v1  # independent filler 32
    vadd.vv v7, v0, v1  # independent filler 33
    vadd.vv v8, v0, v1  # independent filler 34
    vadd.vv v9, v0, v1  # independent filler 35
    vadd.vv v10, v0, v1  # independent filler 36
    vadd.vv v11, v0, v1  # independent filler 37
    vadd.vv v12, v0, v1  # independent filler 38
    vcpop.m x11, v2
    # marker end: zero-cost timestamp point at the next instruction PC.
    .globl __rvv_profile_marker_t30_vmseq_vv_t12_m1_k39_end
    __rvv_profile_marker_t30_vmseq_vv_t12_m1_k39_end:
    .Lrvv_profile_marker_t30_vmseq_vv_t12_m1_k39_end:

    # Terminate through the conventional Linux exit syscall for runners that
    # execute the assembled program directly.
    li a0, 0
    li a7, 93
    ecall
