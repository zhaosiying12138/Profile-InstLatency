vsetvli x0, t0, e32, m1, ta, ma
vadd.vv v2, v1, v0
vmul.vv v4, v3, v0
vdivu.vv v6, v5, v0
vmseq.vv v8, v7, v0
vredsum.vs v10, v9, v0
vslideup.vx v12, v11, t1
vcpop.m a0, v0
viota.m v14, v0
vsetvli x0, t0, e32, m2, ta, ma
vadd.vv v2, v1, v0
vmul.vv v4, v3, v0
vdivu.vv v6, v5, v0
vmseq.vv v8, v7, v0
vredsum.vs v10, v9, v0
vslideup.vx v12, v11, t1
viota.m v14, v0
vsetvli x0, t0, e32, m4, ta, ma
vadd.vv v2, v1, v0
vmul.vv v4, v3, v0
vdivu.vv v6, v5, v0
vmseq.vv v8, v7, v0
vredsum.vs v10, v9, v0
vslideup.vx v12, v11, t1
viota.m v14, v0
