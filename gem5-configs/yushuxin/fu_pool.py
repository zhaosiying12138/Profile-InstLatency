# YuShuXin-V2.1 gem5 MinorCPU FU pool (generated from config/yushuxin_timing_v2.yaml).
# OpClass assignments verified against gem5 v24.1.0.3 decoder.isa:
#   vadd=SimdAdd vmul=SimdMult vdivu=SimdDiv vmseq=SimdCmp
#   vredsum=SimdReduceAdd vslideup=SimdAlu(0x0e) viota=SimdAlu(0x14) vcpop=SimdMisc
# viota vs vslideup share SimdAlu: split by ExtMachInst mask/match on funct6[31:26].
from m5.objects.BaseMinorCPU import (
    MinorFU, MinorFUTiming, MinorOpClassSet, MinorFUPool, minorMakeOpClassSet,
)

def _timing(desc, op_classes, src_lat, extra_commit=0, mask=0, match=0):
    return MinorFUTiming(
        description=desc,
        opClasses=minorMakeOpClassSet(op_classes),
        srcRegsRelativeLats=[src_lat],
        extraCommitLat=extra_commit,
        mask=mask,
        match=match,
    )

MASK_FUNCT6 = 0xFC000000   # bits [31:26]
VIOTA_MATCH   = 0x14 << 26
VSLIDEUP_MATCH = 0x0E << 26

# ---- VP0 ALU (mu = 1, opLat = 6) ------------------------------------------
# vadd L=3 (srcLat 3), vmseq L=2 (srcLat 4), viota L=5 (srcLat 1), vmul L=4 (srcLat 2)
YX_VP0_ALU = MinorFU(
    opClasses=minorMakeOpClassSet(["SimdAdd", "SimdCmp", "SimdAlu", "SimdMult",
                                   "SimdMisc"]),
    opLat=6,
    issueLat=1,
    timings=[
        _timing("vadd",  ["SimdAdd"],  3),
        _timing("vmseq", ["SimdCmp"],  4),
        _timing("viota", ["SimdAlu"],  1, 0, MASK_FUNCT6, VIOTA_MATCH),
        _timing("vmul-vp0", ["SimdMult"], 2),
        _timing("vcpop", ["SimdMisc"], 3),   # also serves vmv.v.i (SimdMisc) in setup
    ],
)

# ---- VP0 PERM (mu = 2, opLat = 6): vslideup L=4 (srcLat 2) -----------------
YX_VP0_PERM = MinorFU(
    opClasses=minorMakeOpClassSet(["SimdAlu"]),
    opLat=6,
    issueLat=2,
    timings=[
        _timing("vslideup", ["SimdAlu"], 2, 0, MASK_FUNCT6, VSLIDEUP_MATCH),
    ],
)

# ---- VP1 ALU (mu = 1, opLat = 6): vmul mirror (ANY pipe) -------------------
YX_VP1_ALU = MinorFU(
    opClasses=minorMakeOpClassSet(["SimdMult"]),
    opLat=6,
    issueLat=1,
    timings=[_timing("vmul-vp1", ["SimdMult"], 2)],
)

# ---- VP1 PERM (mu = 2, opLat = 8): vredsum L=6 (srcLat 2) ------------------
YX_VP1_PERM = MinorFU(
    opClasses=minorMakeOpClassSet(["SimdReduceAdd"]),
    opLat=8,
    issueLat=2,
    timings=[_timing("vredsum", ["SimdReduceAdd"], 2)],
)

# ---- VP1 DIV (non-pipelined, mu == opLat == 12): vdivu ---------------------
YX_VP1_DIV = MinorFU(
    opClasses=minorMakeOpClassSet(["SimdDiv"]),
    opLat=12,
    issueLat=12,
    timings=[_timing("vdivu", ["SimdDiv"], 2)],
)

# ---- scalar / config --------------------------------------------------------
YXIntFU = MinorFU(
    opClasses=minorMakeOpClassSet(["IntAlu", "SimdConfig", "SimdFloatExt"]),
    opLat=3,
    issueLat=1,
    timings=[MinorFUTiming(description="Int", srcRegsRelativeLats=[2])],
)
# VLSU: unit-stride vector loads/stores + scalar mem. L1-hit latency 4,
# one beat (one register group) per cycle.
YXMemFU = MinorFU(
    opClasses=minorMakeOpClassSet(["SimdUnitStrideLoad", "SimdUnitStrideStore",
                                   "SimdUnitStrideMaskLoad", "SimdUnitStrideMaskStore",
                                   "MemRead", "MemWrite"]),
    opLat=4,
    issueLat=1,
    timings=[MinorFUTiming(description="VLSU", srcRegsRelativeLats=[1])],
)

# Pool order fixes cross-pipe indices in se_yushuxin.py:
# 0=VP0_ALU 1=VP0_PERM 2=VP1_ALU 3=VP1_PERM 4=VP1_DIV 5=Int 6=Mem
YXPoolUnits = [YX_VP0_ALU, YX_VP0_PERM, YX_VP1_ALU, YX_VP1_PERM, YX_VP1_DIV, YXIntFU, YXMemFU]
