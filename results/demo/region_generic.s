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
