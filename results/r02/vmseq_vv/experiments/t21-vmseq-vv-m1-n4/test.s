# Generated RVV profiling experiment.
# experiment_id: t21-vmseq-vv-m1-n4
# template_id: T21_PAIR_WITH_SCALAR
# vector_shape: e32,m1
# markers: start=__rvv_profile_marker_t21_vmseq_vv_m1_n4_start, end=__rvv_profile_marker_t21_vmseq_vv_m1_n4_end
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

    # Scalar pairing probe. Each vector instruction is followed by an add.
    # marker start: zero-cost timestamp point at the next instruction PC.
    .globl __rvv_profile_marker_t21_vmseq_vv_m1_n4_start
    __rvv_profile_marker_t21_vmseq_vv_m1_n4_start:
    .Lrvv_profile_marker_t21_vmseq_vv_m1_n4_start:
    vmseq.vv v2, v0, v1
    add x20, x21, x22
    vmseq.vv v3, v0, v1
    add x23, x24, x25
    vmseq.vv v4, v0, v1
    add x26, x27, x28
    vmseq.vv v5, v0, v1
    add x29, x30, x31
    # marker end: zero-cost timestamp point at the next instruction PC.
    .globl __rvv_profile_marker_t21_vmseq_vv_m1_n4_end
    __rvv_profile_marker_t21_vmseq_vv_m1_n4_end:
    .Lrvv_profile_marker_t21_vmseq_vv_m1_n4_end:

    # Terminate through the conventional Linux exit syscall for runners that
    # execute the assembled program directly.
    li a0, 0
    li a7, 93
    ecall
