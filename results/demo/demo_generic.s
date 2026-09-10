	.attribute	4, 16
	.attribute	5, "rv64i2p1_f2p2_d2p2_v1p0_zicsr2p0_zve32f1p0_zve32x1p0_zve64d1p0_zve64f1p0_zve64x1p0_zvl128b1p0_zvl256b1p0_zvl32b1p0_zvl64b1p0"
	.file	"demo.ll"
	.text
	.globl	demo                            # -- Begin function demo
	.p2align	2
	.type	demo,@function
	.variant_cc	demo
demo:                                   # @demo
	.cfi_startproc
# %bb.0:                                # %entry
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
	vse32.v	v10, (a0)
	vsetivli	zero, 8, e32, mf2, tu, ma
	vslideup.vi	v11, v8, 1
	vsetvli	a0, zero, e32, mf2, ta, ma
	vse32.v	v9, (a1)
	vse32.v	v11, (a3)
	ret
.Lfunc_end0:
	.size	demo, .Lfunc_end0-demo
	.cfi_endproc
                                        # -- End function
	.section	".note.GNU-stack","",@progbits
