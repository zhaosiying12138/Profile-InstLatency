# YuShuXin-V2.1 syscall-emulation config: RiscvMinorCPU with the custom FU pool,
# VLEN=256/ELEN=64, 1 GHz, classic caches.
#   gem5.opt --debug-flags=Exec --debug-file=exec.log \
#       configs/yushuxin/se_yushuxin.py --cmd <elf>
import argparse
import m5
from m5.objects import (
    RiscvMinorCPU, System, SrcClockDomain, VoltageDomain, Root, Cache,
    SystemXBar, SimpleMemory, MinorFUPool, Process, AddrRange,
)
import sys
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from fu_pool import YXPoolUnits


def cache(size, assoc=8):
    return Cache(size=size, assoc=assoc, tag_latency=1, data_latency=1,
                 response_latency=1, mshrs=8, tgts_per_mshr=16)


parser = argparse.ArgumentParser()
parser.add_argument("--cmd", required=True, help="elf to run")
args = parser.parse_args()

system = System()
system.clk_domain = SrcClockDomain(clock="1GHz",
                                   voltage_domain=VoltageDomain(voltage="1V"))
system.mem_mode = "timing"
system.mem_ranges = [AddrRange("512MiB")]

cpu = RiscvMinorCPU(cpu_id=0, numThreads=1)

units = list(YXPoolUnits)
# Cross-pipe forwarding bans (pool order: 0=VP0_ALU 1=VP0_PERM 2=VP1_ALU
# 3=VP1_PERM 4=VP1_DIV 5=Int): a consumer on one vector pipe waits for the
# full writeback of producers from the other pipe (no cross-pipe bypass).
units[0].cantForwardFromFUIndices = [2, 3, 4]
units[1].cantForwardFromFUIndices = [2, 3, 4]
units[2].cantForwardFromFUIndices = [0, 1]
units[3].cantForwardFromFUIndices = [0, 1]
units[4].cantForwardFromFUIndices = [0, 1]
units[5].cantForwardFromFUIndices = [0, 1, 3, 4]   # scalar <- vector RF wait
cpu.executeFuncUnits = MinorFUPool(funcUnits=units)

cpu.createThreads()
cpu.createInterruptController()

# Vector geometry: VLEN=256 / ELEN=64 are the RiscvISA defaults in v24.1.

system.cpu = cpu
system.icache = cache("32KiB")
system.dcache = cache("32KiB")
system.membus = SystemXBar()
system.cpu.icache_port = system.icache.cpu_side
system.cpu.dcache_port = system.dcache.cpu_side
system.icache.mem_side = system.membus.cpu_side_ports
system.dcache.mem_side = system.membus.cpu_side_ports
system.system_port = system.membus.cpu_side_ports
# SimpleMemory hangs directly off the coherent bus (MemCtrl expects a
# MemInterface in v24.1; a flat-latency backing store is all we need).
system.memory = SimpleMemory(range=system.mem_ranges[0], latency="30ns")
system.memory.port = system.membus.mem_side_ports

from m5.objects import SEWorkload
system.workload = SEWorkload.init_compatible(args.cmd)
process = Process()
process.cmd = [args.cmd]
system.cpu.workload = process

root = Root(full_system=False, system=system)
m5.instantiate()
exit_code = m5.simulate()
print(f"Finished simulating: {exit_code.getCause()}")
sys.exit(exit_code.getCode())
