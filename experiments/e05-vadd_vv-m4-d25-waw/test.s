# e05-vadd_vv-m4-d25-waw [E5_WAW]
.text
.global _start
_start:
    # ---- setup ----
    li x5, 32
    vsetvli x0, x5, e32, m4, ta, ma
    vmv.v.i v0, 1
    vmv.v.i v4, 2
    vmv.v.i v8, 3
    vmv.v.i v12, 4
    vmv.v.i v16, 5
    vmv.v.i v20, 6
    vmv.v.i v24, 7
    vmv.v.i v28, 1
    li x6, 6
    li x7, 7
    li x8, 8
    li x9, 9
    li x10, 10
    li x11, 11
    li x12, 12
    li x13, 13
    li x14, 14
    li x15, 15
    li x16, 16
    li x17, 17
    li x18, 18
    li x19, 19
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
    .balign 64
    # ---- shadow warm-up of the epilogue (never executed) ----
    j 1f
    li a7, 93
    li a0, 0
    ecall
1:
    # TIMESTAMP_MARK start
    .globl __yx_marker_e05_vadd_vv_m4_d25_waw_start
__yx_marker_e05_vadd_vv_m4_d25_waw_start:
    vadd.vv v8, v0, v4   # write1 -> v8
    add x21, x6, x7   # filler 0
    add x22, x6, x7   # filler 1
    add x23, x6, x7   # filler 2
    add x24, x6, x7   # filler 3
    add x25, x6, x7   # filler 4
    add x26, x6, x7   # filler 5
    add x27, x6, x7   # filler 6
    add x28, x6, x7   # filler 7
    add x21, x6, x7   # filler 8
    add x22, x6, x7   # filler 9
    add x23, x6, x7   # filler 10
    add x24, x6, x7   # filler 11
    add x25, x6, x7   # filler 12
    add x26, x6, x7   # filler 13
    add x27, x6, x7   # filler 14
    add x28, x6, x7   # filler 15
    add x21, x6, x7   # filler 16
    add x22, x6, x7   # filler 17
    add x23, x6, x7   # filler 18
    add x24, x6, x7   # filler 19
    add x25, x6, x7   # filler 20
    add x26, x6, x7   # filler 21
    add x27, x6, x7   # filler 22
    add x28, x6, x7   # filler 23
    add x21, x6, x7   # filler 24
    vadd.vv v8, v16, v20   # write2 -> v8
    # TIMESTAMP_MARK end
    .globl __yx_marker_e05_vadd_vv_m4_d25_waw_end
__yx_marker_e05_vadd_vv_m4_d25_waw_end:
    # ---- exit ----
    li a7, 93
    li a0, 0
    ecall
