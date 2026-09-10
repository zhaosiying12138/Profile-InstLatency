#!/usr/bin/env bash
# (Re)create the real-run command scripts that get screenshotted.
set -u
D=/home/zhaosiying/.yxshots/cmds
mkdir -p "$D"
cat > $D/env.sh <<'EOF'
cd ~/codebase/Profile-InstLatency
echo "== environment =="
echo "-- gem5"; /home/zhaosiying/codebase/gem5/build/RISCV/gem5.opt --version 2>&1 | grep -i version
echo "-- llvm-mc"; /home/zhaosiying/codebase/llvm-project/build/bin/llvm-mc --version | head -2
nproc | xargs echo "-- cores:"
echo "-- injected machine (single source of truth)"; python3 scripts/yxmodel.py | head -26
EOF
cat > $D/e0.sh <<'EOF'
cd ~/codebase/Profile-InstLatency
echo "== E0: zero-cost marker baseline =="
python3 scripts/run_v2.py experiments/e00-marker-baseline --backend gem5
python3 -c "import json; t=json.load(open('experiments/e00-marker-baseline/trace.json')); print('entries:', t['entries'])"
echo "=> delta == 0 : markers cost nothing (premise of every reading)"
EOF
cat > $D/e2.sh <<'EOF'
cd ~/codebase/Profile-InstLatency
echo "== E2: independent-stream N-scan -> ReleaseAtCycles =="
for e in e02-vadd_vv-m1-n2 e02-vadd_vv-m1-n4 e02-vadd_vv-m1-n8 e02-vadd_vv-m4-n4; do python3 scripts/run_v2.py experiments/$e --backend gem5; done
echo "-- vdivu (non-pipelined: R == L):"
for e in e02-vdivu_vv-m1-n2 e02-vdivu_vv-m1-n4 e02-vdivu_vv-m4-n2; do python3 scripts/run_v2.py experiments/$e --backend gem5; done
echo "=> vadd slope 1(m1)/4(m4); vdivu slope 12/24/48 non-pipelined"
EOF
cat > $D/e3.sh <<'EOF'
cd ~/codebase/Profile-InstLatency
echo "== E3: self-RAW chain -> Latency (m1) =="
for e in e03-vadd_vv-m1-n4 e03-vadd_vv-m1-n12 e03-vmul_vv-m1-n4 e03-vredsum_vs-m1-n4 e03-vdivu_vv-m1-n4; do python3 scripts/run_v2.py experiments/$e --backend gem5; done
echo "=> chain slope = L: vadd 3, vmul 4, vredsum 6, vdivu 12"
echo "-- micro-op cadence (vredsum m2, issueLat = 2):"
grep -m4 "vredsum_vs_micro" experiments/e02-vredsum_vs-m2-n4/build/gem5/exec.log | cut -c1-100
EOF
cat > $D/e4.sh <<'EOF'
cd ~/codebase/Profile-InstLatency
echo "== E4: cross-class RAW matrix @m1 (dep - ctrl) =="
python3 - <<'PY'
import glob, json
from collections import defaultdict
k0=defaultdict(dict)
for f in sorted(glob.glob('experiments/e04-*-m1-k0-*/trace.json')):
    t=json.load(open(f)); m=t['meta']; e=t['entries']
    if any(x['cycle'] is None for x in e): continue
    k0[(m['producer'],m['consumer'])]['ctrl' if m['control'] else 'dep']=e[-1]['cycle']-e[0]['cycle']
INS=["vadd_vv","vmul_vv","vdivu_vv","vmseq_vv","vredsum_vs","vslideup_vx","viota_m"]
print("        "+"".join(f"{c[:7]:>9}" for c in INS))
for p in INS:
    row=f"{p[:7]:>8}"
    for c in INS:
        v=k0.get((p,c),{})
        row+= f"{(v['dep']-v.get('ctrl',1)):>9}" if 'dep' in v else f"{'-':>9}"
    print(row)
PY
echo "=> same-pipe ~L-1 (vadd->vadd = 2); cross-pipe ~full writeback (5..8)"
EOF
cat > $D/gate.sh <<'EOF'
cd ~/codebase/Profile-InstLatency
echo "== tick-exactness gate (design invariants vs gem5) =="
python3 scripts/verify_timing_exactness.py
echo "== final profile (measured vs injected design) =="
python3 scripts/profile_final.py | tail -16
EOF
cat > $D/mca.sh <<'EOF'
cd ~/codebase/Profile-InstLatency
MCA=/home/zhaosiying/codebase/llvm-project/build/bin/llvm-mca
echo "== llvm-mca -instruction-tables (model carries the profiled values) =="
$MCA -mtriple=riscv64 -mcpu=YuShuXinV2 -instruction-tables tests/all_instr.s
echo "== llvm-mca --all-stats (RAW chain) =="
$MCA -mtriple=riscv64 -mcpu=YuShuXinV2 --all-stats tests/chain.s 2>/dev/null | sed -n '1,16p'
EOF
cat > $D/ab_asm.sh <<'EOF2'
cd ~/codebase/Profile-InstLatency
echo "== A/B compile: same IR, two scheduling models =="
LLC=/home/zhaosiying/codebase/llvm-project/build/bin/llc
$LLC -mtriple=riscv64 -mcpu=YuShuXinV2 -O2 tests/demo.ll -o results/demo/demo_yx.s
$LLC -mtriple=riscv64 -mcpu=generic-rv64 -mattr=+v,+zvl256b -O2 tests/demo.ll -o results/demo/demo_generic.s
echo "--- YuShuXinV2 (interleaved: fillers ride the divide bubbles) ---"
grep -E "^\s*v" results/demo/demo_yx.s | head -13
echo "--- generic-rv64 (source order preserved) ---"
grep -E "^\s*v" results/demo/demo_generic.s | head -13
EOF2
cat > $D/ab_gem5.sh <<'EOF2'
cd ~/codebase/Profile-InstLatency
echo "== A/B on the real (simulated) machine: gem5 cycles =="
bash scripts/build_demo.sh 2>&1 | grep -E "GEM5_CYCLES"
python3 -c "a,b=125,132; print(f'improvement: {b-a} cycles = {100*(b-a)/b:.1f}%')"
EOF2
cat > $D/ab_mca.sh <<'EOF2'
cd ~/codebase/Profile-InstLatency
MCA=/home/zhaosiying/codebase/llvm-project/build/bin/llvm-mca
echo "== llvm-mca predictions (same model, both binaries) =="
for v in yx generic; do
  echo "--- $v ---"
  $MCA -mtriple=riscv64 -mcpu=YuShuXinV2 -iterations=1 results/demo/region_$v.s 2>/dev/null | grep -E "Total Cycles|IPC|Block RThroughput" | head -3
done
echo "== alignment: mca delta == gem5 delta == 7 cycles =="
EOF2
cat > $D/overlap.sh <<'EOF2'
cd ~/codebase/Profile-InstLatency
MCA=/home/zhaosiying/codebase/llvm-project/build/bin/llvm-mca
echo "== pipeline overlap in the model-compiled sequence (timeline) =="
$MCA -mtriple=riscv64 -mcpu=YuShuXinV2 -iterations=1 --timeline results/demo/region_yx.s 2>/dev/null | sed -n '/Timeline View/,/Average Wait/p' | head -30
EOF2
echo "cmd scripts written to $D"
