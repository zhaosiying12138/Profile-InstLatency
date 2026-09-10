# e02-vcpop_m-m1-n12 [E2_STREAM]
.text
.global _start
_start:
    # ---- setup ----
    li x5, 8
    vsetvli x0, x5, e32, m1, ta, ma
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
    .globl __yx_marker_e02_vcpop_m_m1_n12_start
__yx_marker_e02_vcpop_m_m1_n12_start:
    vcpop.m x10, v0   # stream 0
    vcpop.m x10, v0   # stream 1
    vcpop.m x10, v0   # stream 2
    vcpop.m x10, v0   # stream 3
    vcpop.m x10, v0   # stream 4
    vcpop.m x10, v0   # stream 5
    vcpop.m x10, v0   # stream 6
    vcpop.m x10, v0   # stream 7
    vcpop.m x10, v0   # stream 8
    vcpop.m x10, v0   # stream 9
    vcpop.m x10, v0   # stream 10
    vcpop.m x10, v0   # stream 11
    # TIMESTAMP_MARK end
    .globl __yx_marker_e02_vcpop_m_m1_n12_end
__yx_marker_e02_vcpop_m_m1_n12_end:
    # ---- exit ----
    li a7, 93
    li a0, 0
    ecall
