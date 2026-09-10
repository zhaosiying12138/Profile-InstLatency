; demo.ll — end-to-end scheduling case study (canonical trunk RVV intrinsic
; form, matching llvm/test/CodeGen/RISCV/rvv/unmasked-tu.ll signatures).
; Shape: 4-deep vdivu RAW chain (12-cycle non-pipelined bubbles) + independent
; vmul/vadd/vredsum/vslideup fillers a knowing scheduler can push into them.

define void @demo(<vscale x 1 x i32> %a, <vscale x 1 x i32> %b, ptr %out, ptr %out2, ptr %out3, ptr %out4) {
entry:
  ; BAD program order: the 4-deep divide chain is consecutive (4 x 12-cycle
  ; bubbles if nothing fills them); all independent fillers come afterwards.
  %d0 = call <vscale x 1 x i32> @llvm.riscv.vdivu.nxv1i32.nxv1i32(<vscale x 1 x i32> undef, <vscale x 1 x i32> %b, <vscale x 1 x i32> %a, i64 8)
  %d1 = call <vscale x 1 x i32> @llvm.riscv.vdivu.nxv1i32.nxv1i32(<vscale x 1 x i32> undef, <vscale x 1 x i32> %d0, <vscale x 1 x i32> %b, i64 8)
  %d2 = call <vscale x 1 x i32> @llvm.riscv.vdivu.nxv1i32.nxv1i32(<vscale x 1 x i32> undef, <vscale x 1 x i32> %d1, <vscale x 1 x i32> %b, i64 8)
  %d3 = call <vscale x 1 x i32> @llvm.riscv.vdivu.nxv1i32.nxv1i32(<vscale x 1 x i32> undef, <vscale x 1 x i32> %d2, <vscale x 1 x i32> %b, i64 8)
  %m0 = call <vscale x 1 x i32> @llvm.riscv.vmul.nxv1i32.nxv1i32(<vscale x 1 x i32> undef, <vscale x 1 x i32> %a, <vscale x 1 x i32> %b, i64 8)
  %m1 = call <vscale x 1 x i32> @llvm.riscv.vmul.nxv1i32.nxv1i32(<vscale x 1 x i32> undef, <vscale x 1 x i32> %m0, <vscale x 1 x i32> %b, i64 8)
  %m2 = call <vscale x 1 x i32> @llvm.riscv.vmul.nxv1i32.nxv1i32(<vscale x 1 x i32> undef, <vscale x 1 x i32> %m1, <vscale x 1 x i32> %b, i64 8)
  %s0 = call <vscale x 1 x i32> @llvm.riscv.vadd.nxv1i32.nxv1i32(<vscale x 1 x i32> undef, <vscale x 1 x i32> %m0, <vscale x 1 x i32> %m1, i64 8)
  %s1 = call <vscale x 1 x i32> @llvm.riscv.vadd.nxv1i32.nxv1i32(<vscale x 1 x i32> undef, <vscale x 1 x i32> %s0, <vscale x 1 x i32> %m2, i64 8)
  %s2 = call <vscale x 1 x i32> @llvm.riscv.vadd.nxv1i32.nxv1i32(<vscale x 1 x i32> undef, <vscale x 1 x i32> %s1, <vscale x 1 x i32> %m2, i64 8)
  %sl = call <vscale x 1 x i32> @llvm.riscv.vslideup.vx.nxv1i32.nxv1i32(<vscale x 1 x i32> %s2, <vscale x 1 x i32> %s1, i64 1, i64 8, i64 0)
  store <vscale x 1 x i32> %d3, ptr %out
  store <vscale x 1 x i32> %m2, ptr %out2
  store <vscale x 1 x i32> %sl, ptr %out4
 ret void
}

declare <vscale x 1 x i32> @llvm.riscv.vdivu.nxv1i32.nxv1i32(<vscale x 1 x i32>, <vscale x 1 x i32>, <vscale x 1 x i32>, i64)
declare <vscale x 1 x i32> @llvm.riscv.vmul.nxv1i32.nxv1i32(<vscale x 1 x i32>, <vscale x 1 x i32>, <vscale x 1 x i32>, i64)
declare <vscale x 1 x i32> @llvm.riscv.vadd.nxv1i32.nxv1i32(<vscale x 1 x i32>, <vscale x 1 x i32>, <vscale x 1 x i32>, i64)
declare <vscale x 1 x i32> @llvm.riscv.vslideup.vx.nxv1i32.nxv1i32(<vscale x 1 x i32>, <vscale x 1 x i32>, i64, i64, i64)
