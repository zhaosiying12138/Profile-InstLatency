#!/usr/bin/env bash
# End-to-end A/B demo: same IR compiled with YuShuXinV2 vs generic-rv64,
# marker-wrapped, measured on gem5, predicted by llvm-mca.
# Usage: bash scripts/build_demo.sh   (run from repo root)
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LLVM=/home/zhaosiying/codebase/llvm-project/build/bin
GEM5=/home/zhaosiying/codebase/gem5/build/RISCV/gem5.opt
CFG=/home/zhaosiying/codebase/gem5/configs/yushuxin/se_yushuxin.py
OUT=$ROOT/results/demo
mkdir -p $OUT

# 1) compile twice (identical flags except the scheduling model)
$LLVM/llc -mtriple=riscv64 -mcpu=YuShuXinV2  -O2 $ROOT/tests/demo.ll -o $OUT/demo_yx.s
$LLVM/llc -mtriple=riscv64 -mcpu=generic-rv64 -mattr=+v,+zvl256b -O2 $ROOT/tests/demo.ll -o $OUT/demo_generic.s

# 2) wrap each into a runnable _start program with markers around the region
python3 $ROOT/scripts/wrap_demo.py $OUT/demo_yx.s     $OUT/run_yx.s
python3 $ROOT/scripts/wrap_demo.py $OUT/demo_generic.s $OUT/run_generic.s

# 3) assemble+link+run on gem5
for v in yx generic; do
  $LLVM/llvm-mc -triple=riscv64 -mattr=+v,+zvl256b -filetype=obj \
      -o $OUT/run_$v.o $OUT/run_$v.s
  $LLVM/ld.lld -m elf64lriscv --no-relax -Ttext=0x80000000 -o $OUT/run_$v.elf $OUT/run_$v.o
  $GEM5 --outdir $OUT/gem5_$v --debug-flags=Exec --debug-file=exec.log \
        $CFG --cmd $OUT/run_$v.elf >/dev/null 2>&1
  python3 - $OUT <<PY
import sys; sys.path.insert(0, "$ROOT/scripts")
from run_v2 import resolve_markers, parse_exec_cycles
marks = resolve_markers("$OUT/run_$v.elf")
want = {pc: None for n, pc in marks.items() if "region" in n}
cyc = parse_exec_cycles("$OUT/gem5_$v/exec.log", want)
st = marks.get("__yx_marker_ab_region_start"); en = marks.get("__yx_marker_ab_region_end")
cs = cyc.get(st); ce = cyc.get(en)
if cs is not None and ce is not None:
    print(f"GEM5_CYCLES_$v={ce-cs}")
PY
done

# 4) llvm-mca predictions under the YuShuXinV2 model (both binaries)
for v in yx generic; do
  echo "--- mca $v ---"
  $LLVM/llvm-mca -mtriple=riscv64 -mcpu=YuShuXinV2 -iterations=1 \
      $OUT/region_$v.s 2>/dev/null | grep -E "Total Cycles|IPC|Block RThroughput" | head -3
done
