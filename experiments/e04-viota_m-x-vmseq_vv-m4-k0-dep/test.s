# e04-viota_m-x-vmseq_vv-m4-k0-dep [E4_XRAW]
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
    .globl __yx_marker_e04_viota_m_x_vmseq_vv_m4_k0_dep_start
__yx_marker_e04_viota_m_x_vmseq_vv_m4_k0_dep_start:
    viota.m v8, v0   # producer
    vmseq.vv v12, v8, v4   # consumer vmseq_vv
    # TIMESTAMP_MARK end
    .globl __yx_marker_e04_viota_m_x_vmseq_vv_m4_k0_dep_end
__yx_marker_e04_viota_m_x_vmseq_vv_m4_k0_dep_end:
    # ---- exit ----
    li a7, 93
    li a0, 0
    ecall
