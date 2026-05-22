// PRELIMINARY DRAFT ONLY.
// Source: profile_inst_latency results/common scaffolding.
// Do not copy this into LLVM until synthetic calibration passes and mapping
// evidence identifies each emitted field.

def YuShuXinModel : SchedMachineModel {
  let IssueWidth = 2;
  let MicroOpBufferSize = 0;
  let LoadLatency = 0;
}

def YuShuXinVPipe0 : ProcResource<1>;
def YuShuXinVPipe1 : ProcResource<1>;
def YuShuXinAnyVPipe : ProcResGroup<[YuShuXinVPipe0, YuShuXinVPipe1]>;

// Placeholder resource classes. Latency and ReleaseAtCycles values below are
// draft sentinels and must be replaced only from calibrated profile evidence.
def YuShuXinWriteVIALUV : SchedWriteRes<[YuShuXinAnyVPipe]> {
  let Latency = 0;
  let ReleaseAtCycles = [0];
}

def YuShuXinWriteVShiftV : SchedWriteRes<[YuShuXinAnyVPipe]> {
  let Latency = 0;
  let ReleaseAtCycles = [0];
}

def YuShuXinWriteVIMulV : SchedWriteRes<[YuShuXinAnyVPipe]> {
  let Latency = 0;
  let ReleaseAtCycles = [0];
}

def YuShuXinWriteVIDivV : SchedWriteRes<[YuShuXinVPipe1]> {
  let Latency = 0;
  let ReleaseAtCycles = [0];
}

def YuShuXinWriteVICmpV : SchedWriteRes<[YuShuXinAnyVPipe]> {
  let Latency = 0;
  let ReleaseAtCycles = [0];
}

def YuShuXinWriteVMPopV : SchedWriteRes<[YuShuXinVPipe0]> {
  let Latency = 0;
  let ReleaseAtCycles = [0];
}

def YuShuXinWriteVIotaV : SchedWriteRes<[YuShuXinVPipe0]> {
  let Latency = 0;
  let ReleaseAtCycles = [0];
}

def YuShuXinWriteVSlideUpX : SchedWriteRes<[YuShuXinVPipe0]> {
  let Latency = 0;
  let ReleaseAtCycles = [0];
}

def YuShuXinWriteVRGatherVV : SchedWriteRes<[YuShuXinVPipe1]> {
  let Latency = 0;
  let ReleaseAtCycles = [0];
}

def YuShuXinWriteVIRedV_From : SchedWriteRes<[YuShuXinVPipe1]> {
  let Latency = 0;
  let ReleaseAtCycles = [0];
}
