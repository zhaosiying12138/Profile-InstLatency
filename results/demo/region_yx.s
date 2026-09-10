    vsetivli	zero, 8, e32, mf2, ta, ma
    vdivu.vv	v10, v9, v8
    vdivu.vv	v10, v10, v9
    vdivu.vv	v10, v10, v9
    vmul.vv	v8, v8, v9
    vmul.vv	v11, v8, v9
    vadd.vv	v8, v8, v11
    vmul.vv	v11, v11, v9
    vadd.vv	v8, v8, v11
    vdivu.vv	v9, v10, v9
    vadd.vv	v10, v8, v11
    vsetvli	zero, zero, e32, mf2, tu, ma
    vslideup.vi	v10, v8, 1
    vsetvli	a2, zero, e32, mf2, ta, ma
