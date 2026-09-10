# e05-vmseq_vv-m2-d9-waw [E5_WAW]
.text
.global _start
_start:
    # ---- setup ----
    li x5, 16
    vsetvli x0, x5, e32, m2, ta, ma
    vmv.v.i v0, 1
    vmv.v.i v2, 2
    vmv.v.i v4, 3
    vmv.v.i v6, 4
    vmv.v.i v8, 5
    vmv.v.i v10, 6
    vmv.v.i v12, 7
    vmv.v.i v14, 1
    vmv.v.i v16, 2
    vmv.v.i v18, 3
    vmv.v.i v20, 4
    vmv.v.i v22, 5
    vmv.v.i v24, 6
    vmv.v.i v26, 7
    vmv.v.i v28, 1
    vmv.v.i v30, 2
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
    .globl __yx_marker_e05_vmseq_vv_m2_d9_waw_start
__yx_marker_e05_vmseq_vv_m2_d9_waw_start:
    vmseq.vv v4, v0, v2   # write1 -> v4
    add x21, x6, x7   # filler 0
    add x22, x6, x7   # filler 1
    add x23, x6, x7   # filler 2
    add x24, x6, x7   # filler 3
    add x25, x6, x7   # filler 4
    add x26, x6, x7   # filler 5
    add x27, x6, x7   # filler 6
    add x28, x6, x7   # filler 7
    add x21, x6, x7   # filler 8
    vmseq.vv v4, v8, v10   # write2 -> v4
    # TIMESTAMP_MARK end
    .globl __yx_marker_e05_vmseq_vv_m2_d9_waw_end
__yx_marker_e05_vmseq_vv_m2_d9_waw_end:
    # ---- exit ----
    li a7, 93
    li a0, 0
    ecall
