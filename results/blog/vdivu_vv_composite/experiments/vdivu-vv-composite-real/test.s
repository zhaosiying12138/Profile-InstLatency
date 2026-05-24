# Blog-only real gem5 experiment for explaining LLVM scheduling fields.
# The marker labels are lowered by scripts/run_experiment.py into zero-cost
# symbol labels; no marker instruction occupies an issue slot.

    .section .text
    .globl _start
_start:
    li x5, 64
    li x20, 20
    li x21, 21
    li x22, 22
    li x23, 23
    li x24, 24
    li x25, 25

    # m1 source and destination setup.
    vsetvli x0, x5, e32, m1, ta, ma
    vmv.v.i v0, 12
    vmv.v.i v1, 3
    vmv.v.i v2, 5
    vmv.v.i v3, 6
    vmv.v.i v4, 7
    vmv.v.i v5, 8
    vmv.v.i v6, 9
    vmv.v.i v7, 10
    vmv.v.i v8, 11
    vmv.v.i v9, 12
    vmv.v.i v10, 13
    vmv.v.i v11, 14
    vmv.v.i v12, 15
    vmv.v.i v13, 1
    vmv.v.i v14, 2
    vmv.v.i v15, 3

    TIMESTAMP_MARK overall_start

    # Segment 1: two independent fillers are not enough to fully cover the
    # vdivu -> vadd dependence. One idle issue cycle remains before the consumer.
    TIMESTAMP_MARK m1_gap2_start
    vdivu.vv v8, v0, v1
    vadd.vv v9, v0, v1
    vadd.vv v10, v0, v1
    vadd.vv v11, v8, v1
    TIMESTAMP_MARK m1_gap2_end
    addi x0, x0, 0
    # Drain previous vector side effects before the next illustrative segment.
    .rept 40
    addi x0, x0, 0
    .endr

    # Segment 2: m1 independent vdivu stream. The steady issue distance is
    # the release/occupancy value when the destination rotates.
    TIMESTAMP_MARK m1_ind_start
    vdivu.vv v12, v0, v1
    vdivu.vv v13, v0, v1
    vdivu.vv v14, v0, v1
    vdivu.vv v15, v0, v1
    TIMESTAMP_MARK m1_ind_end
    addi x0, x0, 0
    .rept 40
    addi x0, x0, 0
    .endr

    # Segment 3: m1 self RAW chain. Reusing v20 as source and destination makes
    # each following divide wait until the previous result is ready.
    TIMESTAMP_MARK m1_raw_start
    vdivu.vv v20, v0, v1
    vdivu.vv v20, v20, v1
    vdivu.vv v20, v20, v1
    TIMESTAMP_MARK m1_raw_end
    addi x0, x0, 0
    .rept 40
    addi x0, x0, 0
    .endr

    # m2 stream: register groups are aligned on even-numbered vector registers.
    vsetvli x0, x5, e32, m2, ta, ma
    vmv.v.i v4, 12
    vmv.v.i v6, 3
    TIMESTAMP_MARK m2_ind_start
    vdivu.vv v8, v4, v6
    vdivu.vv v10, v4, v6
    vdivu.vv v12, v4, v6
    TIMESTAMP_MARK m2_ind_end
    addi x0, x0, 0
    .rept 40
    addi x0, x0, 0
    .endr

    # m4 stream: register groups are aligned on multiples of four.
    vsetvli x0, x5, e32, m4, ta, ma
    vmv.v.i v16, 12
    vmv.v.i v20, 3
    TIMESTAMP_MARK m4_ind_start
    vdivu.vv v24, v16, v20
    vdivu.vv v28, v16, v20
    TIMESTAMP_MARK m4_ind_end
    addi x0, x0, 0

    TIMESTAMP_MARK overall_end
    li a0, 0
    li a7, 93
    ecall
