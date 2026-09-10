# Non-pipelined divider: 3-deep RAW chain, each L=R=12 (M1)
    vsetivli x0, 8, e32, m1, ta, ma
    vdivu.vv v8, v4, v5
    vdivu.vv v8, v8, v5
    vdivu.vv v8, v8, v5
