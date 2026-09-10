# e10-loadhit-m2-k2 [E10_LOAD]
.text
.global _start
_start:
    # ---- setup ----
    la x8, __yx_load_data
    li x5, 16
    vsetvli x0, x5, e32, m2, ta, ma
    vmv.v.i v0, 1
    li x6, 6
    li x7, 7
    vle32.v v0, (x8)   # warm
    vle32.v v2, (x8)   # warm
    .balign 64
    # ---- shadow warm-up of the epilogue (never executed) ----
    j 1f
    li a7, 93
    li a0, 0
    ecall
1:
    # TIMESTAMP_MARK start
    .globl __yx_marker_e10_loadhit_m2_k2_start
__yx_marker_e10_loadhit_m2_k2_start:
    vle32.v v4, (x8)   # measured load
    add x21, x6, x7   # filler 0
    add x22, x6, x7   # filler 1
    vadd.vv v6, v4, v0   # consumer
    # TIMESTAMP_MARK end
    .globl __yx_marker_e10_loadhit_m2_k2_end
__yx_marker_e10_loadhit_m2_k2_end:
    # ---- exit ----
    li a7, 93
    li a0, 0
    ecall
    .section .data
    .balign 64
__yx_load_data:
    .word 1
    .word 2
    .word 3
    .word 4
    .word 5
    .word 6
    .word 7
    .word 8
    .word 9
    .word 10
    .word 11
    .word 12
    .word 13
    .word 14
    .word 15
    .word 16
    .word 17
    .word 18
    .word 19
    .word 20
    .word 21
    .word 22
    .word 23
    .word 24
    .word 25
    .word 26
    .word 27
    .word 28
    .word 29
    .word 30
    .word 31
    .word 32
    .word 33
    .word 34
    .word 35
    .word 36
    .word 37
    .word 38
    .word 39
    .word 40
    .word 41
    .word 42
    .word 43
    .word 44
    .word 45
    .word 46
    .word 47
    .word 48
    .word 49
    .word 50
    .word 51
    .word 52
    .word 53
    .word 54
    .word 55
    .word 56
    .word 57
    .word 58
    .word 59
    .word 60
    .word 61
    .word 62
    .word 63
    .word 64
