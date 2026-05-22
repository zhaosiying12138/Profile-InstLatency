# Generated RVV profiling experiment.
# experiment_id: t10-viota-m-m4-n4
# template_id: T10_INDEPENDENT_STREAM_THROUGHPUT
# vector_shape: e32,m4
# markers: start=__rvv_profile_marker_t10_viota_m_m4_n4_start, end=__rvv_profile_marker_t10_viota_m_m4_n4_end
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

    # Fixed first-version vector shape: SEW=e32, LMUL=m4.
    vsetvli x0, x5, e32, m4, ta, ma

    # Initialize aligned vector groups. Values are simple and non-zero
    # where divisor/index operands might otherwise create simulator noise.
    vmv.v.i v0, 1
    vmv.v.i v4, 2
    vmv.v.i v8, 3
    vmv.v.i v12, 4
    vmv.v.i v16, 5
    vmv.v.i v20, 6
    vmv.v.i v24, 7
    vmv.v.i v28, 1

    # Establish a reusable all-true mask input for mask instructions.
    vmseq.vi v0, v0, 1

    # Independent stream: sources are read-only and destinations rotate.
    # marker start: zero-cost timestamp point at the next instruction PC.
    .globl __rvv_profile_marker_t10_viota_m_m4_n4_start
    __rvv_profile_marker_t10_viota_m_m4_n4_start:
    .Lrvv_profile_marker_t10_viota_m_m4_n4_start:
    viota.m v8, v0
    viota.m v12, v0
    viota.m v16, v0
    viota.m v20, v0
    # marker end: zero-cost timestamp point at the next instruction PC.
    .globl __rvv_profile_marker_t10_viota_m_m4_n4_end
    __rvv_profile_marker_t10_viota_m_m4_n4_end:
    .Lrvv_profile_marker_t10_viota_m_m4_n4_end:

    # Terminate through the conventional Linux exit syscall for runners that
    # execute the assembled program directly.
    li a0, 0
    li a7, 93
    ecall
