# Generated RVV experiment scaffold.
# experiment_id: t20-vrgather-vv-vredsum-vs-m4-n3
# template_id: T20_PAIRWISE_PIPE_CLASSIFICATION
# vector_shape: e32,m4
# markers: start, end
#
# TIMESTAMP_MARK is a runner/simulator pseudo line. These files document the
# intended experiment shape and are not required to assemble before the marker
# path exists.

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

    # Pairwise pipe classification. A and B share read-only sources.
    TIMESTAMP_MARK start
    vrgather.vv v8, v0, v4
    vredsum.vs v12, v0, v4
    vrgather.vv v16, v0, v4
    vredsum.vs v20, v0, v4
    vrgather.vv v24, v0, v4
    vredsum.vs v28, v0, v4
    TIMESTAMP_MARK end

    # Terminate through the conventional Linux exit syscall when a runner
    # chooses to assemble this after marker lowering is implemented.
    li a0, 0
    li a7, 93
    ecall
