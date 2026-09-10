//===-- RISCVSchedYuShuXinV2.td - YuShuXinV2 Scheduling Defs -*- tablegen -*-=//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//
//
// YuShuXinV2 is a fictitious in-order dual-issue RV64 processor used as the
// profiling target of the Profile-InstLatency v2 study. Every value below was
// REVERSE-ENGINEERED from gem5 MinorCPU cycle-level traces (marker-delta
// differential experiments E0-E11), not copied from any real core.
//
//   IssueWidth = 2, MicroOpBufferSize = 1 (in-order, 1-entry lookahead,
//   no ROB, no renaming)
//   Two 1-wide vector pipes; the divider is NOT pipelined (R == L)
//   Latency/ReleaseAtCycles are linear in LMUL: base + k*LMUL
//   (profiled at SEW=e32, LMUL m1/m2/m4; fractional LMULs round up to 1 and
//    non-e32 SEWs reuse the same linear form as documented extrapolations)
//
//===----------------------------------------------------------------------===//

// LMUL factor for the linear forms (fractional LMULs round up to 1).
class YXV2Lmul<string mx> {
  int f = !cond(!eq(mx, "M1"): 1, !eq(mx, "M2"): 2, !eq(mx, "M4"): 4, !eq(mx, "M8"): 8,
                true: 1);
}
class YXV2Lat<int b, int k, string mx> { int val = !add(b, !mul(k, YXV2Lmul<mx>.f)); }

def YuShuXinV2Model : SchedMachineModel {
  let IssueWidth = 2;
  let MicroOpBufferSize = 1;   // in-order with 1-entry lookahead: the scheduler may
                              // consider the next ready op past a stalled head
  let LoadLatency = 4;            // vle32.v L1-hit latency (E10)
  let HighLatency = 10;
  let MispredictPenalty = 10;
  let PostRAScheduler = false;
  let CompleteModel = false;
}

let SchedModel = YuShuXinV2Model in {

// Two 1-wide vector pipes (E7 pairwise-mix classification).
def YXV2VPipe0 : ProcResource<1>;
def YXV2VPipe1 : ProcResource<1>;
def YXV2AnyVPipe : ProcResGroup<[YXV2VPipe0, YXV2VPipe1]>;   // vmul.vv (E7)
// Scalar fallback units so llc can lower ordinary code next to RVV.
def YXV2IntPipe : ProcResource<1>;
def YXV2MemPipe : ProcResource<1>;

defm : UnsupportedSchedSFB;
defm : UnsupportedSchedA;
defm : UnsupportedSchedF;
defm : UnsupportedSchedZfa;
defm : UnsupportedSchedZabha;
defm : UnsupportedSchedZba;
defm : UnsupportedSchedZbb;
defm : UnsupportedSchedZbc;
defm : UnsupportedSchedZbkb;
defm : UnsupportedSchedZbkx;
defm : UnsupportedSchedZbs;
defm : UnsupportedSchedZvbb;
defm : UnsupportedSchedZvbc;
defm : UnsupportedSchedZvkb;
defm : UnsupportedSchedZvkg;
defm : UnsupportedSchedZvkned;
defm : UnsupportedSchedZvknhaOrZvknhb;
defm : UnsupportedSchedZvksed;
defm : UnsupportedSchedZvksh;
defm : UnsupportedSchedXsf;

// ---------------------------------------------------------------- scalar ---
def : WriteRes<WriteIALU, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteIALU32, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteShiftImm, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteShiftReg, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteIMul, [YXV2IntPipe]> { let Latency = 3; }
def : WriteRes<WriteIDiv, [YXV2IntPipe]> { let Latency = 12; let ReleaseAtCycles = [12]; }
def : WriteRes<WriteIDiv32, [YXV2IntPipe]> { let Latency = 12; let ReleaseAtCycles = [12]; }
def : WriteRes<WriteIRem, [YXV2IntPipe]> { let Latency = 12; let ReleaseAtCycles = [12]; }
def : WriteRes<WriteIRem32, [YXV2IntPipe]> { let Latency = 12; let ReleaseAtCycles = [12]; }
def : WriteRes<WriteIMul32, [YXV2IntPipe]> { let Latency = 3; }
def : WriteRes<WriteShiftImm32, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteShiftReg32, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteJmp, [YXV2IntPipe]>  { let Latency = 1; }
def : WriteRes<WriteJal, [YXV2IntPipe]>  { let Latency = 1; }
def : WriteRes<WriteJalr, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteNop, []> { let Latency = 0; }
def : WriteRes<WriteLDW, [YXV2MemPipe]> { let Latency = 4; }
def : WriteRes<WriteLDD, [YXV2MemPipe]> { let Latency = 4; }
def : WriteRes<WriteLDH, [YXV2MemPipe]> { let Latency = 4; }
def : WriteRes<WriteLDB, [YXV2MemPipe]> { let Latency = 4; }
def : WriteRes<WriteSTW, [YXV2MemPipe]> { let Latency = 1; }
def : WriteRes<WriteSTD, [YXV2MemPipe]> { let Latency = 1; }
def : WriteRes<WriteSTH, [YXV2MemPipe]> { let Latency = 1; }
def : WriteRes<WriteSTB, [YXV2MemPipe]> { let Latency = 1; }
def : WriteRes<WriteCSR, [YXV2IntPipe]> { let Latency = 1; }
// Vector configuration (vsetvli*) — setup-only in our experiments, modeled 1/1.
def : WriteRes<WriteVSETVLI, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteVSETIVLI, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteVSETVL, [YXV2IntPipe]> { let Latency = 1; }

// Reads used by modeled writes must carry a (possibly zero) ReadAdvance entry.
def : ReadAdvance<ReadVIALUV_WorstCase, 0>;
def : ReadAdvance<ReadVICmpV_WorstCase, 0>;
def : ReadAdvance<ReadVIDivV_WorstCase, 0>;
def : ReadAdvance<ReadVSETVLI, 0>;
def : ReadAdvance<ReadVSETVL, 0>;
def : ReadAdvance<ReadJmp, 0>;
def : ReadAdvance<ReadJalr, 0>;
def : ReadAdvance<ReadCSR, 0>;
def : ReadAdvance<ReadMemBase, 0>;
def : ReadAdvance<ReadStoreData, 0>;
def : ReadAdvance<ReadIALU32, 0>;
def : ReadAdvance<ReadShiftImm32, 0>;
def : ReadAdvance<ReadShiftReg32, 0>;
def : ReadAdvance<ReadIMul32, 0>;
def : ReadAdvance<ReadIDiv32, 0>;
def : ReadAdvance<ReadIRem, 0>;
def : ReadAdvance<ReadIRem32, 0>;
def : ReadAdvance<ReadShiftImm, 0>;
def : ReadAdvance<ReadShiftReg, 0>;
def : ReadAdvance<ReadIDiv, 0>;
def : ReadAdvance<ReadIMul, 0>;
// ReadIALU pays +1 when reading a vcpop.m GPR result through the RF (G4, E4).
def : ReadAdvance<ReadIALU, -1, [WriteVMPopV_M1, WriteVMPopV_M2, WriteVMPopV_M4]>;

// ------------------------------------------------------------ vector pipes
// vadd.vv   : VP0  L = 2 + 1*LMUL (3/4/6/10 at M1/M2/M4/M8), R = 1*LMUL
foreach mx = SchedMxList in {
  let Latency = YXV2Lat<2, 1, mx>.val,          // MEASURED: L=3/4/6 (E3 chain), R=1/2/4 (E2)
      ReleaseAtCycles = [YXV2Lat<0, 1, mx>.val] in
    defm : LMULWriteResMX<"WriteVIALUV", [YXV2VPipe0], mx, !eq(mx, "M8")>;
}
// vmul.vv : either pipe (ProcResGroup). MEASURED (E3 chains / E2 streams):
//   L = 4/5/7, R = 1/1/2 (ANY group yields 2/cycle -> ceil(LMUL/2) emergent).
def : WriteRes<WriteVIMulV_M1, [YXV2AnyVPipe]> { let Latency = 4; let ReleaseAtCycles = [1]; }
def : WriteRes<WriteVIMulV_M2, [YXV2AnyVPipe]> { let Latency = 5; let ReleaseAtCycles = [1]; }
def : WriteRes<WriteVIMulV_M4, [YXV2AnyVPipe]> { let Latency = 7; let ReleaseAtCycles = [2]; }
def : WriteRes<WriteVIMulV_M8, [YXV2AnyVPipe]> { let Latency = 9; let ReleaseAtCycles = [4]; }
// vdivu.vv  : VP1, NOT pipelined: R == L == 8 + 4*LMUL (12/16/24/40).
foreach mx = SchedMxList in {
  foreach sew = SchedSEWSet<mx>.val in {
    let Latency = YXV2Lat<0, 12, mx>.val,       // v2.1: non-pipelined L=R=12*lambda
        ReleaseAtCycles = [YXV2Lat<0, 12, mx>.val] in
      defm : LMULSEWWriteResMXSEW<"WriteVIDivV", [YXV2VPipe1], mx, sew,
                                  !and(!eq(mx, "M8"), !eq(sew, 64))>;
  }
}
// vmseq.vv : VP0. MEASURED L=5/6/8 (E4; the vmask_mv companion carries the
// mask write), R=4/5/7 (E2; companion cadence dominates).
def : WriteRes<WriteVICmpV_M1, [YXV2VPipe0]> { let Latency = 5; let ReleaseAtCycles = [4]; }
def : WriteRes<WriteVICmpV_M2, [YXV2VPipe0]> { let Latency = 6; let ReleaseAtCycles = [5]; }
def : WriteRes<WriteVICmpV_M4, [YXV2VPipe0]> { let Latency = 8; let ReleaseAtCycles = [7]; }
def : WriteRes<WriteVICmpV_M8, [YXV2VPipe0]> { let Latency = 11; let ReleaseAtCycles = [11]; }
def : WriteRes<WriteVICmpV_MF2, [YXV2VPipe0]> { let Latency = 4; let ReleaseAtCycles = [3]; }
def : WriteRes<WriteVICmpV_MF4, [YXV2VPipe0]> { let Latency = 3; let ReleaseAtCycles = [2]; }
def : WriteRes<WriteVICmpV_MF8, [YXV2VPipe0]> { let Latency = 3; let ReleaseAtCycles = [1]; }
// vredsum.vs: VP1. L = 4 + 2*LMUL, R = 2 + 1*LMUL.
foreach mx = SchedMxList in {
  foreach sew = SchedSEWSet<mx>.val in {
    let Latency = YXV2Lat<4, 2, mx>.val,        // v2.1: L = 4+2*LMUL (6/8/12)
        ReleaseAtCycles = [YXV2Lat<0, 2, mx>.val] in
      defm : LMULSEWWriteResMXSEW<"WriteVIRedV_From", [YXV2VPipe1], mx, sew,
                                  !and(!eq(mx, "M8"), !eq(sew, 64))>;
  }
}
// vslideup.vx: VP0. MEASURED L=4/6/10, R=4/7/18 (E2; non-affine cadence from
// mu=2 perm pipe + companion effects; LLVM takes per-LMUL values).
def : WriteRes<WriteVSlideUpX_M1, [YXV2VPipe0]> { let Latency = 4; let ReleaseAtCycles = [4]; }
def : WriteRes<WriteVSlideUpX_M2, [YXV2VPipe0]> { let Latency = 6; let ReleaseAtCycles = [7]; }
def : WriteRes<WriteVSlideUpX_M4, [YXV2VPipe0]> { let Latency = 10; let ReleaseAtCycles = [18]; }
// vslideup.vi (immediate form): same perm-pipe numbers as the .vx form.
def : WriteRes<WriteVSlideI_M1, [YXV2VPipe0]> { let Latency = 4; let ReleaseAtCycles = [4]; }
def : WriteRes<WriteVSlideI_M2, [YXV2VPipe0]> { let Latency = 6; let ReleaseAtCycles = [7]; }
def : WriteRes<WriteVSlideI_M4, [YXV2VPipe0]> { let Latency = 10; let ReleaseAtCycles = [18]; }
def : WriteRes<WriteVSlideI_M8, [YXV2VPipe0]> { let Latency = 18; let ReleaseAtCycles = [34]; }
def : WriteRes<WriteVSlideI_MF2, [YXV2VPipe0]> { let Latency = 3; let ReleaseAtCycles = [2]; }
def : WriteRes<WriteVSlideI_MF4, [YXV2VPipe0]> { let Latency = 2; let ReleaseAtCycles = [1]; }
def : WriteRes<WriteVSlideI_MF8, [YXV2VPipe0]> { let Latency = 2; let ReleaseAtCycles = [1]; }
def : WriteRes<WriteVSlideI_WorstCase, [YXV2VPipe0]> { let Latency = 18; let ReleaseAtCycles = [34]; }

// vcpop.m   : VP0, mask op is LMUL-independent: L = 3, R = 1.
foreach mx = SchedMxList in {
  let Latency = 3, ReleaseAtCycles = [1] in
    defm : LMULWriteResMX<"WriteVMPopV", [YXV2VPipe0], mx, !eq(mx, "M8")>;
}
// viota.m   : VP0. L = 4 + 1*LMUL (5/6/8, MEASURED). Stream cadence is
// FRACTIONAL from mu-op co-issue: R = 1 / 5/4 / 5/2 at M1/M2/M4 (E2 deltas
// N+N/4 and 2.5*N). ReleaseAtCycles are integer-only, so we land the
// conservative integer lambda (1/2/4); the bounded integer report was 1/2/3.
foreach mx = SchedMxList in {
  let Latency = YXV2Lat<4, 1, mx>.val,          // MEASURED L=5/6/8
      ReleaseAtCycles = [YXV2Lat<0, 1, mx>.val] in
    defm : LMULWriteResMX<"WriteVIotaV", [YXV2VPipe0], mx, !eq(mx, "M8")>;
}
// vle32.v   : L1-hit L = 4 (E10), VLSU one beat per register group: R = LMUL.
foreach mx = SchedMxList in {
  let Latency = 4, ReleaseAtCycles = [YXV2Lat<0, 1, mx>.val] in
    defm : LMULWriteResMX<"WriteVLDE", [YXV2MemPipe], mx, !eq(mx, "M8")>;
}

// ------------------------------------ Cross-pipe penalty (G3 = +2, E4 matrix)
// No bypass between VPipe0 and VPipe1: a consumer on the other pipe reads the
// producer's result through the register file two cycles later. LLVM encodes
// producer-specific latency adjustments as negative ReadAdvance entries.
// vmul.vv (AnyVPipe) is excluded: its producing pipe is not statically known.
def : ReadAdvance<ReadVIALUV_M1, -2, [WriteVIDivV_M1_E32, WriteVIRedV_From_M1_E32]>;
def : ReadAdvance<ReadVIALUV_M2, -2, [WriteVIDivV_M2_E32, WriteVIRedV_From_M2_E32]>;
def : ReadAdvance<ReadVIALUV_M4, -2, [WriteVIDivV_M4_E32, WriteVIRedV_From_M4_E32]>;
def : ReadAdvance<ReadVIALUV_M8, -2, [WriteVIDivV_M8_E32, WriteVIRedV_From_M8_E32]>;
def : ReadAdvance<ReadVICmpV_M1, -2, [WriteVIDivV_M1_E32, WriteVIRedV_From_M1_E32]>;
def : ReadAdvance<ReadVICmpV_M2, -2, [WriteVIDivV_M2_E32, WriteVIRedV_From_M2_E32]>;
def : ReadAdvance<ReadVICmpV_M4, -2, [WriteVIDivV_M4_E32, WriteVIRedV_From_M4_E32]>;
def : ReadAdvance<ReadVICmpV_M8, -2, [WriteVIDivV_M8_E32, WriteVIRedV_From_M8_E32]>;
def : ReadAdvance<ReadVIDivV_M1_E32, -2, [WriteVIALUV_M1, WriteVICmpV_M1, WriteVMPopV_M1, WriteVIotaV_M1, WriteVSlideUpX_M1]>;
def : ReadAdvance<ReadVIDivV_M2_E32, -2, [WriteVIALUV_M2, WriteVICmpV_M2, WriteVMPopV_M2, WriteVIotaV_M2, WriteVSlideUpX_M2]>;
def : ReadAdvance<ReadVIDivV_M4_E32, -2, [WriteVIALUV_M4, WriteVICmpV_M4, WriteVMPopV_M4, WriteVIotaV_M4, WriteVSlideUpX_M4]>;
def : ReadAdvance<ReadVIDivV_M8_E32, -2, [WriteVIALUV_M8, WriteVICmpV_M8, WriteVMPopV_M8, WriteVIotaV_M8, WriteVSlideUpX_M8]>;
def : ReadAdvance<ReadVIRedV, -2, [WriteVIALUV_M1, WriteVICmpV_M1, WriteVMPopV_M1, WriteVIotaV_M1, WriteVSlideUpX_M1,
                                   WriteVIALUV_M2, WriteVICmpV_M2, WriteVMPopV_M2, WriteVIotaV_M2, WriteVSlideUpX_M2,
                                   WriteVIALUV_M4, WriteVICmpV_M4, WriteVMPopV_M4, WriteVIotaV_M4, WriteVSlideUpX_M4,
                                   WriteVIALUV_M8, WriteVICmpV_M8, WriteVMPopV_M8, WriteVIotaV_M8, WriteVSlideUpX_M8,
                                   WriteVIALUV_MF2, WriteVICmpV_MF2, WriteVMPopV_MF2, WriteVIotaV_MF2, WriteVSlideUpX_MF2,
                                   WriteVIALUV_MF4, WriteVICmpV_MF4, WriteVMPopV_MF4, WriteVIotaV_MF4, WriteVSlideUpX_MF4,
                                   WriteVIALUV_MF8, WriteVICmpV_MF8, WriteVMPopV_MF8, WriteVIotaV_MF8, WriteVSlideUpX_MF8]>;



// Fractional-LMUL and non-e32 variants of the modeled families: the same
// cross-pipe -2 applies (the bypass does not depend on SEW/LMUL granularity).
foreach mx = ["M1", "M2", "M4", "M8"] in {
  foreach sew = SchedSEWSet<mx>.val in {
    if !ne(sew, 32) then {
      def : ReadAdvance<!cast<SchedRead>("ReadVIDivV_" # mx # "_E" # sew), -2,
                         [!cast<SchedWrite>("WriteVIALUV_" # mx),
                          !cast<SchedWrite>("WriteVICmpV_" # mx),
                          !cast<SchedWrite>("WriteVMPopV_" # mx),
                          !cast<SchedWrite>("WriteVIotaV_" # mx),
                          !cast<SchedWrite>("WriteVSlideUpX_" # mx)]>;
    }
  }
}
foreach mx = ["MF8", "MF4", "MF2"] in {
  foreach sew = SchedSEWSet<mx>.val in {
    def : ReadAdvance<!cast<SchedRead>("ReadVIDivV_" # mx # "_E" # sew), -2,
                       [!cast<SchedWrite>("WriteVIALUV_" # mx),
                        !cast<SchedWrite>("WriteVICmpV_" # mx),
                        !cast<SchedWrite>("WriteVMPopV_" # mx),
                        !cast<SchedWrite>("WriteVIotaV_" # mx),
                        !cast<SchedWrite>("WriteVSlideUpX_" # mx)]>;
  }
}
def : ReadAdvance<ReadVIALUV_MF2, -2, [WriteVIDivV_MF2_E8, WriteVIDivV_MF2_E16, WriteVIDivV_MF2_E32,
                                          WriteVIRedV_From_MF2_E8, WriteVIRedV_From_MF2_E16, WriteVIRedV_From_MF2_E32]>;
def : ReadAdvance<ReadVIALUV_MF4, -2, [WriteVIDivV_MF4_E8, WriteVIDivV_MF4_E16,
                                          WriteVIRedV_From_MF4_E8, WriteVIRedV_From_MF4_E16]>;
def : ReadAdvance<ReadVIALUV_MF8, -2, [WriteVIDivV_MF8_E8, WriteVIRedV_From_MF8_E8]>;
def : ReadAdvance<ReadVICmpV_MF2, -2, [WriteVIDivV_MF2_E8, WriteVIDivV_MF2_E16, WriteVIDivV_MF2_E32,
                                         WriteVIRedV_From_MF2_E8, WriteVIRedV_From_MF2_E16, WriteVIRedV_From_MF2_E32]>;
def : ReadAdvance<ReadVICmpV_MF4, -2, [WriteVIDivV_MF4_E8, WriteVIDivV_MF4_E16,
                                         WriteVIRedV_From_MF4_E8, WriteVIRedV_From_MF4_E16]>;
def : ReadAdvance<ReadVICmpV_MF8, -2, [WriteVIDivV_MF8_E8, WriteVIRedV_From_MF8_E8]>;

def : WriteRes<WriteVIMulV_MF2, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteVIMulV_MF4, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteVIMulV_MF8, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteVSlideUpX_M8, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteVSlideUpX_MF2, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteVSlideUpX_MF4, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteVSlideUpX_MF8, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteVICmpV_WorstCase, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteVIMulV_WorstCase, [YXV2IntPipe]> { let Latency = 1; }
def : WriteRes<WriteVSlideUpX_WorstCase, [YXV2IntPipe]> { let Latency = 1; }
// ---- auto-copied from UnsupportedSchedV (write side only: unmodeled families) ----
let Unsupported = true in {
def : WriteRes<WriteRdVLENB, []>;
defm "" : LMULWriteRes<"WriteVSTE", []>;
defm "" : LMULWriteRes<"WriteVLDM", []>;
defm "" : LMULWriteRes<"WriteVSTM", []>;
defm "" : LMULWriteRes<"WriteVLDS8", []>;
defm "" : LMULWriteRes<"WriteVLDS16", []>;
defm "" : LMULWriteRes<"WriteVLDS32", []>;
defm "" : LMULWriteRes<"WriteVLDS64", []>;
defm "" : LMULWriteRes<"WriteVSTS8", []>;
defm "" : LMULWriteRes<"WriteVSTS16", []>;
defm "" : LMULWriteRes<"WriteVSTS32", []>;
defm "" : LMULWriteRes<"WriteVSTS64", []>;
defm "" : LMULWriteRes<"WriteVLDUX8", []>;
defm "" : LMULWriteRes<"WriteVLDUX16", []>;
defm "" : LMULWriteRes<"WriteVLDUX32", []>;
defm "" : LMULWriteRes<"WriteVLDUX64", []>;
defm "" : LMULWriteRes<"WriteVLDOX8", []>;
defm "" : LMULWriteRes<"WriteVLDOX16", []>;
defm "" : LMULWriteRes<"WriteVLDOX32", []>;
defm "" : LMULWriteRes<"WriteVLDOX64", []>;
defm "" : LMULWriteRes<"WriteVSTUX8", []>;
defm "" : LMULWriteRes<"WriteVSTUX16", []>;
defm "" : LMULWriteRes<"WriteVSTUX32", []>;
defm "" : LMULWriteRes<"WriteVSTUX64", []>;
defm "" : LMULWriteRes<"WriteVSTOX8", []>;
defm "" : LMULWriteRes<"WriteVSTOX16", []>;
defm "" : LMULWriteRes<"WriteVSTOX32", []>;
defm "" : LMULWriteRes<"WriteVSTOX64", []>;
defm "" : LMULWriteRes<"WriteVLDFF", []>;
def : WriteRes<WriteVLD1R, []>;
def : WriteRes<WriteVLD2R, []>;
def : WriteRes<WriteVLD4R, []>;
def : WriteRes<WriteVLD8R, []>;
def : WriteRes<WriteVST1R, []>;
def : WriteRes<WriteVST2R, []>;
def : WriteRes<WriteVST4R, []>;
def : WriteRes<WriteVST8R, []>;
foreach nf=2-8 in {
  foreach eew = [8, 16, 32, 64] in {
    defm "" : LMULWriteRes <"WriteVLSEG" # nf # "e" # eew, []>;
    defm "" : LMULWriteRes <"WriteVLSEGFF" # nf # "e" # eew, []>;
    defm "" : LMULWriteRes <"WriteVSSEG" # nf # "e" # eew, []>;
    defm "" : LMULWriteRes <"WriteVLSSEG" # nf # "e" # eew, []>;
    defm "" : LMULWriteRes <"WriteVSSSEG" # nf # "e" # eew, []>;
    defm "" : LMULWriteRes <"WriteVLUXSEG" # nf # "e" # eew, []>;
    defm "" : LMULWriteRes <"WriteVLOXSEG" # nf # "e" # eew, []>;
    defm "" : LMULWriteRes <"WriteVSUXSEG" # nf # "e" # eew, []>;
    defm "" : LMULWriteRes <"WriteVSOXSEG" # nf # "e" # eew, []>;
  }
}
defm "" : LMULWriteRes<"WriteVIALUX", []>;
defm "" : LMULWriteRes<"WriteVIALUI", []>;
defm "" : LMULWriteResW<"WriteVIWALUV", []>;
defm "" : LMULWriteResW<"WriteVIWALUX", []>;
defm "" : LMULWriteResW<"WriteVIWALUI", []>;
defm "" : LMULWriteRes<"WriteVExtV", []>;
defm "" : LMULWriteRes<"WriteVICALUV", []>;
defm "" : LMULWriteRes<"WriteVICALUX", []>;
defm "" : LMULWriteRes<"WriteVICALUI", []>;
defm "" : LMULWriteRes<"WriteVICALUMV", []>;
defm "" : LMULWriteRes<"WriteVICALUMX", []>;
defm "" : LMULWriteRes<"WriteVICALUMI", []>;
defm "" : LMULWriteRes<"WriteVShiftV", []>;
defm "" : LMULWriteRes<"WriteVShiftX", []>;
defm "" : LMULWriteRes<"WriteVShiftI", []>;
defm "" : LMULWriteResW<"WriteVNShiftV", []>;
defm "" : LMULWriteResW<"WriteVNShiftX", []>;
defm "" : LMULWriteResW<"WriteVNShiftI", []>;
defm "" : LMULWriteRes<"WriteVICmpX", []>;
defm "" : LMULWriteRes<"WriteVICmpI", []>;
defm "" : LMULWriteRes<"WriteVIMinMaxV", []>;
defm "" : LMULWriteRes<"WriteVIMinMaxX", []>;
defm "" : LMULWriteRes<"WriteVIMulX", []>;
defm "" : LMULSEWWriteRes<"WriteVIDivX", []>;
defm "" : LMULWriteResW<"WriteVIWMulV", []>;
defm "" : LMULWriteResW<"WriteVIWMulX", []>;
defm "" : LMULWriteRes<"WriteVIMulAddV", []>;
defm "" : LMULWriteRes<"WriteVIMulAddX", []>;
defm "" : LMULWriteResW<"WriteVIWMulAddV", []>;
defm "" : LMULWriteResW<"WriteVIWMulAddX", []>;
defm "" : LMULWriteRes<"WriteVIMergeV", []>;
defm "" : LMULWriteRes<"WriteVIMergeX", []>;
defm "" : LMULWriteRes<"WriteVIMergeI", []>;
defm "" : LMULWriteRes<"WriteVIMovV", []>;
defm "" : LMULWriteRes<"WriteVIMovX", []>;
defm "" : LMULWriteRes<"WriteVIMovI", []>;
defm "" : LMULWriteRes<"WriteVSALUV", []>;
defm "" : LMULWriteRes<"WriteVSALUX", []>;
defm "" : LMULWriteRes<"WriteVSALUI", []>;
defm "" : LMULWriteRes<"WriteVAALUV", []>;
defm "" : LMULWriteRes<"WriteVAALUX", []>;
defm "" : LMULWriteRes<"WriteVSMulV", []>;
defm "" : LMULWriteRes<"WriteVSMulX", []>;
defm "" : LMULWriteRes<"WriteVSShiftV", []>;
defm "" : LMULWriteRes<"WriteVSShiftX", []>;
defm "" : LMULWriteRes<"WriteVSShiftI", []>;
defm "" : LMULWriteResW<"WriteVNClipV", []>;
defm "" : LMULWriteResW<"WriteVNClipX", []>;
defm "" : LMULWriteResW<"WriteVNClipI", []>;
defm "" : LMULSEWWriteResF<"WriteVFALUV", []>;
defm "" : LMULSEWWriteResF<"WriteVFALUF", []>;
defm "" : LMULSEWWriteResFW<"WriteVFWALUV", []>;
defm "" : LMULSEWWriteResFW<"WriteVFWALUF", []>;
defm "" : LMULSEWWriteResF<"WriteVFMulV", []>;
defm "" : LMULSEWWriteResF<"WriteVFMulF", []>;
defm "" : LMULSEWWriteResF<"WriteVFDivV", []>;
defm "" : LMULSEWWriteResF<"WriteVFDivF", []>;
defm "" : LMULSEWWriteResFW<"WriteVFWMulV", []>;
defm "" : LMULSEWWriteResFW<"WriteVFWMulF", []>;
defm "" : LMULSEWWriteResF<"WriteVFMulAddV", []>;
defm "" : LMULSEWWriteResF<"WriteVFMulAddF", []>;
defm "" : LMULSEWWriteResFW<"WriteVFWMulAddV", []>;
defm "" : LMULSEWWriteResFW<"WriteVFWMulAddF", []>;
defm "" : LMULSEWWriteResF<"WriteVFSqrtV", []>;
defm "" : LMULSEWWriteResF<"WriteVFRecpV", []>;
defm "" : LMULSEWWriteResF<"WriteVFMinMaxV", []>;
defm "" : LMULSEWWriteResF<"WriteVFMinMaxF", []>;
defm "" : LMULSEWWriteResF<"WriteVFSgnjV", []>;
defm "" : LMULSEWWriteResF<"WriteVFSgnjF", []>;
defm "" : LMULWriteRes<"WriteVFCmpV", []>;
defm "" : LMULWriteRes<"WriteVFCmpF", []>;
defm "" : LMULWriteRes<"WriteVFClassV", []>;
defm "" : LMULWriteRes<"WriteVFMergeV", []>;
defm "" : LMULWriteRes<"WriteVFMovV", []>;
defm "" : LMULSEWWriteResF<"WriteVFCvtIToFV", []>;
defm "" : LMULWriteRes<"WriteVFCvtFToIV", []>;
defm "" : LMULSEWWriteResW<"WriteVFWCvtIToFV", []>;
defm "" : LMULWriteResFW<"WriteVFWCvtFToIV", []>;
defm "" : LMULSEWWriteResFW<"WriteVFWCvtFToFV", []>;
defm "" : LMULSEWWriteResFW<"WriteVFNCvtIToFV", []>;
defm "" : LMULWriteResW<"WriteVFNCvtFToIV", []>;
defm "" : LMULSEWWriteResFW<"WriteVFNCvtFToFV", []>;
defm "" : LMULSEWWriteRes<"WriteVIRedMinMaxV_From", []>;
defm "" : LMULSEWWriteResWRed<"WriteVIWRedV_From", []>;
defm "" : LMULSEWWriteResF<"WriteVFRedV_From", []>;
defm "" : LMULSEWWriteResF<"WriteVFRedOV_From", []>;
defm "" : LMULSEWWriteResF<"WriteVFRedMinMaxV_From", []>;
defm "" : LMULSEWWriteResFWRed<"WriteVFWRedV_From", []>;
defm "" : LMULSEWWriteResFWRed<"WriteVFWRedOV_From", []>;
defm "" : LMULWriteRes<"WriteVMALUV", []>;
defm "" : LMULWriteRes<"WriteVMFFSV", []>;
defm "" : LMULWriteRes<"WriteVMSFSV", []>;
defm "" : LMULWriteRes<"WriteVIdxV", []>;
def : WriteRes<WriteVMovSX, []>;
def : WriteRes<WriteVMovXS, []>;
def : WriteRes<WriteVMovSF, []>;
def : WriteRes<WriteVMovFS, []>;
defm "" : LMULWriteRes<"WriteVSlideDownX", []>;
defm "" : LMULWriteRes<"WriteVISlide1X", []>;
defm "" : LMULWriteRes<"WriteVFSlide1F", []>;
defm "" : LMULSEWWriteRes<"WriteVRGatherVV", []>;
defm "" : LMULSEWWriteRes<"WriteVRGatherEI16VV", []>;
defm "" : LMULWriteRes<"WriteVRGatherVX", []>;
defm "" : LMULWriteRes<"WriteVRGatherVI", []>;
defm "" : LMULSEWWriteRes<"WriteVCompressV", []>;
def : WriteRes<WriteVMov1V, []>;
def : WriteRes<WriteVMov2V, []>;
def : WriteRes<WriteVMov4V, []>;
def : WriteRes<WriteVMov8V, []>;
}

// ---- clean zero advances for ALL vector reads (write-side families above stay unsupported) ----
def : ReadAdvance<ReadVLDX, 0>;
def : ReadAdvance<ReadVSTX, 0>;
defm "" : LMULReadAdvance<"ReadVSTEV", 0>;
defm "" : LMULReadAdvance<"ReadVSTM", 0>;
def : ReadAdvance<ReadVLDSX, 0>;
def : ReadAdvance<ReadVSTSX, 0>;
defm "" : LMULReadAdvance<"ReadVSTS8V", 0>;
defm "" : LMULReadAdvance<"ReadVSTS16V", 0>;
defm "" : LMULReadAdvance<"ReadVSTS32V", 0>;
defm "" : LMULReadAdvance<"ReadVSTS64V", 0>;
defm "" : LMULReadAdvance<"ReadVLDUXV", 0>;
defm "" : LMULReadAdvance<"ReadVLDOXV", 0>;
defm "" : LMULReadAdvance<"ReadVSTUXV", 0>;
defm "" : LMULReadAdvance<"ReadVSTUX8", 0>;
defm "" : LMULReadAdvance<"ReadVSTUX16", 0>;
defm "" : LMULReadAdvance<"ReadVSTUX32", 0>;
defm "" : LMULReadAdvance<"ReadVSTUX64", 0>;
defm "" : LMULReadAdvance<"ReadVSTUX8V", 0>;
defm "" : LMULReadAdvance<"ReadVSTUX16V", 0>;
defm "" : LMULReadAdvance<"ReadVSTUX32V", 0>;
defm "" : LMULReadAdvance<"ReadVSTUX64V", 0>;
defm "" : LMULReadAdvance<"ReadVSTOX8", 0>;
defm "" : LMULReadAdvance<"ReadVSTOX16", 0>;
defm "" : LMULReadAdvance<"ReadVSTOX32", 0>;
defm "" : LMULReadAdvance<"ReadVSTOX64", 0>;
defm "" : LMULReadAdvance<"ReadVSTOXV", 0>;
defm "" : LMULReadAdvance<"ReadVSTOX8V", 0>;
defm "" : LMULReadAdvance<"ReadVSTOX16V", 0>;
defm "" : LMULReadAdvance<"ReadVSTOX32V", 0>;
defm "" : LMULReadAdvance<"ReadVSTOX64V", 0>;
// These are already LMUL aware
def : ReadAdvance<ReadVST1R, 0>;
def : ReadAdvance<ReadVST2R, 0>;
def : ReadAdvance<ReadVST4R, 0>;
def : ReadAdvance<ReadVST8R, 0>;

// 11. Vector Integer Arithmetic Instructions
defm "" : LMULReadAdvance<"ReadVIALUX", 0>;
defm "" : LMULReadAdvanceW<"ReadVIWALUV", 0>;
defm "" : LMULReadAdvanceW<"ReadVIWALUX", 0>;
defm "" : LMULReadAdvance<"ReadVExtV", 0>;
defm "" : LMULReadAdvance<"ReadVICALUV", 0>;
defm "" : LMULReadAdvance<"ReadVICALUX", 0>;
defm "" : LMULReadAdvance<"ReadVShiftV", 0>;
defm "" : LMULReadAdvance<"ReadVShiftX", 0>;
defm "" : LMULReadAdvanceW<"ReadVNShiftV", 0>;
defm "" : LMULReadAdvanceW<"ReadVNShiftX", 0>;
defm "" : LMULReadAdvance<"ReadVICmpX", 0>;
defm "" : LMULReadAdvance<"ReadVIMinMaxV", 0>;
defm "" : LMULReadAdvance<"ReadVIMinMaxX", 0>;
defm "" : LMULReadAdvance<"ReadVIMulV", 0>;
defm "" : LMULReadAdvance<"ReadVIMulX", 0>;
defm "" : LMULSEWReadAdvance<"ReadVIDivX", 0>;
defm "" : LMULReadAdvanceW<"ReadVIWMulV", 0>;
defm "" : LMULReadAdvanceW<"ReadVIWMulX", 0>;
defm "" : LMULReadAdvance<"ReadVIMulAddV", 0>;
defm "" : LMULReadAdvance<"ReadVIMulAddX", 0>;
defm "" : LMULReadAdvanceW<"ReadVIWMulAddV", 0>;
defm "" : LMULReadAdvanceW<"ReadVIWMulAddX", 0>;
defm "" : LMULReadAdvance<"ReadVIMergeV", 0>;
defm "" : LMULReadAdvance<"ReadVIMergeX", 0>;
defm "" : LMULReadAdvance<"ReadVIMovV", 0>;
defm "" : LMULReadAdvance<"ReadVIMovX", 0>;

// 12. Vector Fixed-Point Arithmetic Instructions
defm "" : LMULReadAdvance<"ReadVSALUV", 0>;
defm "" : LMULReadAdvance<"ReadVSALUX", 0>;
defm "" : LMULReadAdvance<"ReadVAALUV", 0>;
defm "" : LMULReadAdvance<"ReadVAALUX", 0>;
defm "" : LMULReadAdvance<"ReadVSMulV", 0>;
defm "" : LMULReadAdvance<"ReadVSMulX", 0>;
defm "" : LMULReadAdvance<"ReadVSShiftV", 0>;
defm "" : LMULReadAdvance<"ReadVSShiftX", 0>;
defm "" : LMULReadAdvanceW<"ReadVNClipV", 0>;
defm "" : LMULReadAdvanceW<"ReadVNClipX", 0>;

// 13. Vector Floating-Point Instructions
defm "" : LMULSEWReadAdvanceF<"ReadVFALUV", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFALUF", 0>;
defm "" : LMULSEWReadAdvanceFW<"ReadVFWALUV", 0>;
defm "" : LMULSEWReadAdvanceFW<"ReadVFWALUF", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFMulV", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFMulF", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFDivV", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFDivF", 0>;
defm "" : LMULSEWReadAdvanceFW<"ReadVFWMulV", 0>;
defm "" : LMULSEWReadAdvanceFW<"ReadVFWMulF", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFMulAddV", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFMulAddF", 0>;
defm "" : LMULSEWReadAdvanceFW<"ReadVFWMulAddV", 0>;
defm "" : LMULSEWReadAdvanceFW<"ReadVFWMulAddF", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFSqrtV", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFRecpV", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFMinMaxV", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFMinMaxF", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFSgnjV", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFSgnjF", 0>;
defm "" : LMULReadAdvance<"ReadVFCmpV", 0>;
defm "" : LMULReadAdvance<"ReadVFCmpF", 0>;
defm "" : LMULReadAdvance<"ReadVFClassV", 0>;
defm "" : LMULReadAdvance<"ReadVFMergeV", 0>;
defm "" : LMULReadAdvance<"ReadVFMergeF", 0>;
defm "" : LMULReadAdvance<"ReadVFMovF", 0>;
defm "" : LMULSEWReadAdvanceF<"ReadVFCvtIToFV", 0>;
defm "" : LMULReadAdvance<"ReadVFCvtFToIV", 0>;
defm "" : LMULSEWReadAdvanceW<"ReadVFWCvtIToFV", 0>;
defm "" : LMULReadAdvanceFW<"ReadVFWCvtFToIV", 0>;
defm "" : LMULSEWReadAdvanceFW<"ReadVFWCvtFToFV", 0>;
defm "" : LMULSEWReadAdvanceFW<"ReadVFNCvtIToFV", 0>;
defm "" : LMULReadAdvanceW<"ReadVFNCvtFToIV", 0>;
defm "" : LMULSEWReadAdvanceFW<"ReadVFNCvtFToFV", 0>;

// 14. Vector Reduction Operations
def : ReadAdvance<ReadVIWRedV, 0>;
def : ReadAdvance<ReadVIWRedV0, 0>;
def : ReadAdvance<ReadVFRedV, 0>;
def : ReadAdvance<ReadVFRedV0, 0>;
def : ReadAdvance<ReadVFRedOV, 0>;
def : ReadAdvance<ReadVFRedOV0, 0>;
def : ReadAdvance<ReadVFRedMinMaxV, 0>;
def : ReadAdvance<ReadVFWRedV, 0>;
def : ReadAdvance<ReadVFWRedV0, 0>;
def : ReadAdvance<ReadVFWRedOV, 0>;
def : ReadAdvance<ReadVFWRedOV0, 0>;

// 15. Vector Mask Instructions
defm "" : LMULReadAdvance<"ReadVMALUV", 0>;
defm "" : LMULReadAdvance<"ReadVMPopV", 0>;
defm "" : LMULReadAdvance<"ReadVMFFSV", 0>;
defm "" : LMULReadAdvance<"ReadVMSFSV", 0>;
defm "" : LMULReadAdvance<"ReadVIotaV", 0>;

// 16. Vector Permutation Instructions
def : ReadAdvance<ReadVMovXS, 0>;
def : ReadAdvance<ReadVMovSX_V, 0>;
def : ReadAdvance<ReadVMovSX_X, 0>;
def : ReadAdvance<ReadVMovFS, 0>;
def : ReadAdvance<ReadVMovSF_V, 0>;
def : ReadAdvance<ReadVMovSF_F, 0>;
defm "" : LMULReadAdvance<"ReadVISlideV", 0>;
defm "" : LMULReadAdvance<"ReadVISlideX", 0>;
defm "" : LMULReadAdvance<"ReadVFSlideV", 0>;
defm "" : LMULReadAdvance<"ReadVFSlideF", 0>;
defm "" : LMULSEWReadAdvance<"ReadVRGatherVV_data", 0>;
defm "" : LMULSEWReadAdvance<"ReadVRGatherVV_index", 0>;
defm "" : LMULSEWReadAdvance<"ReadVRGatherEI16VV_data", 0>;
defm "" : LMULSEWReadAdvance<"ReadVRGatherEI16VV_index", 0>;
defm "" : LMULReadAdvance<"ReadVRGatherVX_data", 0>;
defm "" : LMULReadAdvance<"ReadVRGatherVX_index", 0>;
defm "" : LMULReadAdvance<"ReadVRGatherVI_data", 0>;
defm "" : LMULReadAdvance<"ReadVGatherV", 0>;
defm "" : LMULSEWReadAdvance<"ReadVCompressV", 0>;
// These are already LMUL aware
def : ReadAdvance<ReadVMov1V, 0>;
def : ReadAdvance<ReadVMov2V, 0>;
def : ReadAdvance<ReadVMov4V, 0>;
def : ReadAdvance<ReadVMov8V, 0>;

// Others
def : ReadAdvance<ReadVIRedV0, 0>;
def : ReadAdvance<ReadVMask, 0>;
def : ReadAdvance<ReadVPassthru_WorstCase, 0>;
foreach mx = SchedMxList in {
  def : ReadAdvance<!cast<SchedRead>("ReadVPassthru_" # mx), 0>;
  foreach sew = SchedSEWSet<mx>.val in
    def : ReadAdvance<!cast<SchedRead>("ReadVPassthru_" # mx  # "_E" # sew), 0>;
}

} // SchedModel = YuShuXinV2Model
