# e11_composite
.text
.global _start
_start:
    # ---- setup ----
    li x5, 8
    vsetvli x0, x5, e32, m1, ta, ma
    li x6, 6
    li x7, 7
    li t2, 2
    vmv.v.i v0, 1
    vmv.v.i v1, 2
    vmv.v.i v2, 3
    vmv.v.i v4, 4
    add x21, x6, x7   # drain
    add x22, x6, x7   # drain
    add x23, x6, x7   # drain
    add x24, x6, x7   # drain
    add x25, x6, x7   # drain
    add x26, x6, x7   # drain
    .globl __yx_marker_e11_composite_stream_vadd_m1_start
__yx_marker_e11_composite_stream_vadd_m1_start:
    vadd.vv v2, v0, v1
    vadd.vv v3, v0, v1
    vadd.vv v4, v0, v1
    vadd.vv v5, v0, v1
    vadd.vv v6, v0, v1
    vadd.vv v7, v0, v1
    .globl __yx_marker_e11_composite_stream_vadd_m1_end
__yx_marker_e11_composite_stream_vadd_m1_end:
    add x21, x6, x7   # drain
    add x22, x6, x7   # drain
    add x23, x6, x7   # drain
    add x24, x6, x7   # drain
    add x25, x6, x7   # drain
    add x26, x6, x7   # drain
    .globl __yx_marker_e11_composite_chain_vdivu_m1_start
__yx_marker_e11_composite_chain_vdivu_m1_start:
    vdivu.vv v2, v0, v1
    vdivu.vv v2, v2, v1
    vdivu.vv v2, v2, v1
    .globl __yx_marker_e11_composite_chain_vdivu_m1_end
__yx_marker_e11_composite_chain_vdivu_m1_end:
    add x21, x6, x7   # drain
    add x22, x6, x7   # drain
    add x23, x6, x7   # drain
    add x24, x6, x7   # drain
    add x25, x6, x7   # drain
    add x26, x6, x7   # drain
    li x5, 16
    vsetvli x0, x5, e32, m2, ta, ma
    .globl __yx_marker_e11_composite_stream_vredsum_m2_start
__yx_marker_e11_composite_stream_vredsum_m2_start:
    vredsum.vs v4, v0, v2
    vredsum.vs v6, v0, v2
    vredsum.vs v8, v0, v2
    .globl __yx_marker_e11_composite_stream_vredsum_m2_end
__yx_marker_e11_composite_stream_vredsum_m2_end:
    li x5, 8
    vsetvli x0, x5, e32, m1, ta, ma
    add x21, x6, x7   # drain
    add x22, x6, x7   # drain
    add x23, x6, x7   # drain
    add x24, x6, x7   # drain
    add x25, x6, x7   # drain
    add x26, x6, x7   # drain
    .globl __yx_marker_e11_composite_xraw_vslideup_to_vadd_m1_start
__yx_marker_e11_composite_xraw_vslideup_to_vadd_m1_start:
    vslideup.vx v2, v4, x6
    vadd.vv v6, v2, v0
    .globl __yx_marker_e11_composite_xraw_vslideup_to_vadd_m1_end
__yx_marker_e11_composite_xraw_vslideup_to_vadd_m1_end:
    add x21, x6, x7   # drain
    add x22, x6, x7   # drain
    add x23, x6, x7   # drain
    add x24, x6, x7   # drain
    add x25, x6, x7   # drain
    add x26, x6, x7   # drain
    .globl __yx_marker_e11_composite_mix_vadd_vredsum_m1_start
__yx_marker_e11_composite_mix_vadd_vredsum_m1_start:
    vadd.vv v10, v0, v1
    vredsum.vs v12, v0, v2
    vadd.vv v14, v0, v1
    vredsum.vs v16, v0, v2
    .globl __yx_marker_e11_composite_mix_vadd_vredsum_m1_end
__yx_marker_e11_composite_mix_vadd_vredsum_m1_end:
    li a7, 93
    li a0, 0
    ecall
