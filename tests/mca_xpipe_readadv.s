# Cross-pipe no-bypass (negative ReadAdvance): vdivu(VP1) -> vadd(VP0) waits
# Latency 12 - 2 = 10; then a same-pipe vadd -> vadd pair at Latency 3.
    vsetivli x0, 8, e32, m1, ta, ma
    vdivu.vv v8, v4, v5
    vadd.vv  v9, v8, v5
    vadd.vv  v10, v9, v5
