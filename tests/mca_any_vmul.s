# ANY-pipe throughput probe: 6 independent vmul.vv (M1) + 2 independent vadd.vv
    vsetivli x0, 8, e32, m1, ta, ma
    vmul.vv v8,  v4, v5
    vmul.vv v9,  v4, v5
    vmul.vv v10, v4, v5
    vmul.vv v11, v4, v5
    vmul.vv v12, v4, v5
    vmul.vv v13, v4, v5
    vadd.vv v14, v4, v5
    vadd.vv v15, v4, v5
