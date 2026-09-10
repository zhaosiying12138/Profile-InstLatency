# wrapped demo: /home/zhaosiying/codebase/Profile-InstLatency/results/demo/demo_generic.s
.text
.global _start
_start:
    # ---- setup ----
    li x5, 8
    vmv.v.i v8, 3
    vmv.v.i v9, 5
    la x10, __yx_out
    li x6, 6
    li x7, 7
    li x8, 8
    li x9, 9
    .balign 64
    j 1f
    li a7, 93
    li a0, 0
    ecall
1:
    .globl __yx_marker_ab_region_start
__yx_marker_ab_region_start:
    vsetivli	zero, 8, e32, mf2, ta, ma
    vdivu.vv	v10, v9, v8
    vdivu.vv	v10, v10, v9
    vdivu.vv	v10, v10, v9
    vdivu.vv	v10, v10, v9
    vmul.vv	v8, v8, v9
    vmul.vv	v11, v8, v9
    vmul.vv	v9, v11, v9
    vadd.vv	v8, v8, v11
    vadd.vv	v8, v8, v9
    vadd.vv	v11, v8, v9
    vsetvli	a2, zero, e32, mf2, ta, ma
    vsetivli	zero, 8, e32, mf2, tu, ma
    vslideup.vi	v11, v8, 1
    vsetvli	a0, zero, e32, mf2, ta, ma
    .globl __yx_marker_ab_region_end
__yx_marker_ab_region_end:
    # ---- exit ----
    li a7, 93
    li a0, 0
    ecall
.section .data
.balign 64
__yx_out:
    .space 256
