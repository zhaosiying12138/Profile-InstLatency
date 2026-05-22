# Generated RVV experiment scaffold.
# experiment_id: t00-marker
# template_id: T00_BASELINE_MARKER
# vector_shape: e32,none
# markers: t0, t1
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

    # No vsetvli is needed for the marker-only baseline.

    # Adjacent markers define the baseline marker delta.
    TIMESTAMP_MARK t0
    TIMESTAMP_MARK t1

    # Terminate through the conventional Linux exit syscall when a runner
    # chooses to assemble this after marker lowering is implemented.
    li a0, 0
    li a7, 93
    ecall
