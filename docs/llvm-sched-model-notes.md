# LLVM Schedule Model Notes For RVV Profiling

This note records the LLVM scheduling concepts that Phase 1 aligns to. The
LLVM checkout is read-only; the profiling workflow uses these fields to decide
what data later experiments must infer.

## Processor-Level Fields

`IssueWidth` is the maximum number of scheduled micro-ops in one cycle group.
For the planned in-order, dual-issue model, this is the common processor field
that should eventually distinguish one-wide from two-wide issue behavior.

`MicroOpBufferSize` describes how much buffering LLVM assumes between issue and
scheduling. Values `0` and `1` are used for in-order scheduling styles. Values
greater than `1` mark a model as out-of-order in `MCSchedModel`, which is not
the first profiling target.

## Resources And Writes

`ProcResource` represents a processor resource kind with a fixed number of
units. `ProcResGroup` groups resources so a write can use one member of a set.
For the RVV profiler, these are the LLVM-facing names for execution pipes such
as a single vector pipe or a flexible two-pipe vector group.

`WriteRes` maps an existing `SchedWrite` to a list of processor resources for a
subtarget. `SchedWriteRes` defines a write and its resources together. RISC-V
RVV uses families such as `WriteVIALUV`, `WriteVShiftV`, and `WriteVIDivV`,
then expands them by LMUL and sometimes SEW. The extractor records the intended
family for each selected instruction and the source lines that mention the
family.

## Per-Instruction Fields

`Latency` is LLVM's producer-to-consumer readiness value for a write. The
profiling workflow should infer it from dependent RAW chains or consumer-gap
experiments.

`ReleaseAtCycles` is resource occupancy relative to issue. When it is omitted
or empty, LLVM treats the resource as consumed for a single cycle, which models
a fully pipelined unit even when latency is longer. This makes
`ReleaseAtCycles` the primary field for independent-stream throughput.

`AcquireAtCycles` is the matching delayed-resource acquisition field. Phase 1
records it as a field to watch, but the first model assumes the default empty
list unless later evidence shows a delayed resource claim is needed.

`NumMicroOps`, `SingleIssue`, `BeginGroup`, and `EndGroup` affect issue grouping
and scalar pairing. The initial map treats one micro-op and non-single-issue as
assumptions to be tested by pair-with-scalar experiments.

`ReadAdvance` and `SchedReadAdvance` are consumer-specific adjustments to the
base write latency. They matter when one consumer can read a result earlier or
later than another, so they are profiled only when consumer-gap experiments show
different readiness distances.

## Why Physical Writeback Is Not A Separate Default Field

LLVM's schedule model is centered on issue-time accounting, abstract resources,
and observable readiness. A dependent instruction sees the producer through
`Latency`, while independent throughput sees the occupied resource through
`ReleaseAtCycles`. A physical writeback stage is therefore not represented as a
separate default field.

If a real processor exposes a distinct writeback bottleneck, it must be modeled
indirectly: for example as an additional `ProcResource`, a longer
`ReleaseAtCycles`, a different `Latency`, or a targeted `ReadAdvance`. Without
such an explicit model choice, marker experiments can estimate readiness and
occupancy but cannot uniquely split execution latency from physical writeback
latency.
