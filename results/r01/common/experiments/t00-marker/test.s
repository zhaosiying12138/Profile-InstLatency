# Generated RVV profiling experiment.
# experiment_id: t00-marker
# template_id: T00_BASELINE_MARKER
# vector_shape: e32,none
# markers: t0=__rvv_profile_marker_t00_marker_t0, t1=__rvv_profile_marker_t00_marker_t1
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

    # No vsetvli is needed for the marker-only baseline.

    # Adjacent markers define the baseline marker delta.
    # marker t0: zero-cost timestamp point at the next instruction PC.
    .globl __rvv_profile_marker_t00_marker_t0
    __rvv_profile_marker_t00_marker_t0:
    .Lrvv_profile_marker_t00_marker_t0:
    # marker t1: zero-cost timestamp point at the next instruction PC.
    .globl __rvv_profile_marker_t00_marker_t1
    __rvv_profile_marker_t00_marker_t1:
    .Lrvv_profile_marker_t00_marker_t1:

    # Terminate through the conventional Linux exit syscall for runners that
    # execute the assembled program directly.
    li a0, 0
    li a7, 93
    ecall
