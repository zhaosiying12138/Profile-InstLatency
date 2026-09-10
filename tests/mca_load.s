# LoadLatency=4: warmed vle32 then dependent vadd
    vsetivli x0, 8, e32, m1, ta, ma
    vle32.v v8, (a0)
    vadd.vv v9, v8, v4
