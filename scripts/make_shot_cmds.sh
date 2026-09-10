#!/usr/bin/env bash
# Screenshot command scripts. EVERY executed command is echoed as "$ <cmd>"
# before running, so each screenshot shows the full command line (user
# requirement) next to its real output.
set -u
D=/home/zhaosiying/.yxshots/cmds
mkdir -p "$D"
RUN='run(){ echo; echo "\$ $*"; "$@"; }; pipe(){ echo; echo "\$ $*"; eval "$*"; }'

cat > $D/env.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== environment =="
run /home/zhaosiying/codebase/gem5/build/RISCV/gem5.opt --version
run /home/zhaosiying/codebase/llvm-project/build/bin/llvm-mc --version
pipe "nproc | xargs echo cores:"
echo; echo "== injected machine: python3 scripts/yxmodel.py =="
run python3 scripts/yxmodel.py
EOF

cat > $D/e0.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== E0: zero-cost marker baseline =="
run python3 scripts/run_v2.py experiments/e00-marker-baseline --backend gem5
echo; echo "\$ cat experiments/e00-marker-baseline/trace.json | python3 -m json.tool | head -14"
cat experiments/e00-marker-baseline/trace.json | python3 -m json.tool | head -14
echo "=> delta == 0 : markers cost nothing (premise of every reading)"
EOF

cat > $D/e2.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== E2: independent-stream N-scan -> ReleaseAtCycles =="
for e in e02-vadd_vv-m1-n2 e02-vadd_vv-m1-n4 e02-vadd_vv-m1-n8 e02-vadd_vv-m4-n4 e02-vdivu_vv-m1-n2 e02-vdivu_vv-m1-n4 e02-vdivu_vv-m4-n2; do
  run python3 scripts/run_v2.py experiments/\$e --backend gem5
done
echo "=> vadd slope 1(m1)/4(m4); vdivu slope 12/24/48 non-pipelined R==L"
EOF

cat > $D/e3.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== E3: self-RAW chain -> Latency (m1) =="
for e in e03-vadd_vv-m1-n4 e03-vadd_vv-m1-n12 e03-vmul_vv-m1-n4 e03-vredsum_vs-m1-n4 e03-vdivu_vv-m1-n4; do
  run python3 scripts/run_v2.py experiments/\$e --backend gem5
done
echo "=> chain slope = L: vadd 3, vmul 4, vredsum 6, vdivu 12"
echo; echo "== micro-op cadence evidence (vredsum m2, issueLat=2): =="
echo "\$ grep -m4 vredsum_vs_micro experiments/e02-vredsum_vs-m2-n4/build/gem5/exec.log | cut -c1-96"
grep -m4 vredsum_vs_micro experiments/e02-vredsum_vs-m2-n4/build/gem5/exec.log | cut -c1-96
EOF

cat > $D/e4.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== E4: cross-class RAW matrix @m1 (dep - ctrl, from real traces) =="
run python3 scripts/e4_matrix.py
echo "=> same-pipe ~L-1 (vadd->vadd=2); cross-pipe ~full writeback (5..8)"
EOF

cat > $D/e7.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== E7: mixed streams -> pipe classification (36 pairs @m1) =="
for e in e07-vadd_vv-vredsum_vs-m1-p4 e07-vadd_vv-vmseq_vv-m1-p4 e07-vdivu_vv-vredsum_vs-m1-p4 e07-vadd_vv-vadd_vv-m1-p4; do
  run python3 scripts/run_v2.py experiments/\$e --backend gem5
done
run python3 scripts/e7_matrix.py
echo "== E10: vector load hit =="
run python3 scripts/run_v2.py experiments/e10-loadhit-m1-k0 --backend gem5
run python3 scripts/run_v2.py experiments/e10-loadhit-m1-k4 --backend gem5
echo "=> consumer gap at k0 == LoadLatency(4); k4 fills it"
EOF

cat > $D/gate.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== tick-exactness gate (design invariants vs gem5) =="
run python3 scripts/verify_timing_exactness.py
echo; echo "== composite additivity (E11) =="
run python3 scripts/e11_composite.py
EOF

cat > $D/mca.sh <<EOF
#!/usr/bin/env bash
$RUN
MCA=/home/zhaosiying/codebase/llvm-project/build/bin/llvm-mca
cd ~/codebase/Profile-InstLatency
echo "== llvm-mca -instruction-tables: the model carries the profiled values =="
run \$MCA -mtriple=riscv64 -mcpu=YuShuXinV2 -instruction-tables tests/all_instr.s
echo
echo "(command re-echoed for the record:)"
echo "\$ llvm-mca -mtriple=riscv64 -mcpu=YuShuXinV2 -instruction-tables tests/all_instr.s"
EOF

cat > $D/ab_asm.sh <<EOF
#!/usr/bin/env bash
$RUN
LLC=/home/zhaosiying/codebase/llvm-project/build/bin/llc
cd ~/codebase/Profile-InstLatency
echo "== A/B compile: same IR, two scheduling models =="
run \$LLC -mtriple=riscv64 -mcpu=YuShuXinV2 -O2 tests/demo.ll -o results/demo/demo_yx.s
run \$LLC -mtriple=riscv64 -mcpu=generic-rv64 -mattr=+v,+zvl256b -O2 tests/demo.ll -o results/demo/demo_generic.s
echo; echo "--- YuShuXinV2 (interleaved: fillers ride the divide bubbles) ---"
echo "\$ grep -E '^\s*v' results/demo/demo_yx.s | head -13"
grep -E "^\s*v" results/demo/demo_yx.s | head -13
echo "--- generic-rv64 (source order preserved) ---"
echo "\$ grep -E '^\s*v' results/demo/demo_generic.s | head -13"
grep -E "^\s*v" results/demo/demo_generic.s | head -13
EOF

cat > $D/ab_gem5.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== A/B on the injected machine: build, run on gem5, print cycles =="
run bash scripts/build_demo.sh
echo; echo "\$ python3 -c \"a,b=125,132; print(f'improvement: {b-a} cycles = {100*(b-a)/b:.1f}%')\""
python3 -c "a,b=125,132; print(f'improvement: {b-a} cycles = {100*(b-a)/b:.1f}%')"
EOF

cat > $D/ab_mca.sh <<EOF
#!/usr/bin/env bash
$RUN
MCA=/home/zhaosiying/codebase/llvm-project/build/bin/llvm-mca
cd ~/codebase/Profile-InstLatency
echo "== llvm-mca predictions under the SAME model, both binaries =="
echo "--- yx (model-compiled) ---"
run \$MCA -mtriple=riscv64 -mcpu=YuShuXinV2 -iterations=1 results/demo/region_yx.s
echo "--- generic (baseline-compiled) ---"
run \$MCA -mtriple=riscv64 -mcpu=YuShuXinV2 -iterations=1 results/demo/region_generic.s
echo "== alignment: mca delta (64-57) == gem5 delta (132-125) == 7 cycles =="
EOF

cat > $D/overlap.sh <<EOF
#!/usr/bin/env bash
$RUN
MCA=/home/zhaosiying/codebase/llvm-project/build/bin/llvm-mca
cd ~/codebase/Profile-InstLatency
echo "== pipeline overlap in the model-compiled sequence =="
echo "\$ llvm-mca ... --timeline results/demo/region_yx.s | sed -n '/Timeline View/,/Average Wait/p'"
run \$MCA -mtriple=riscv64 -mcpu=YuShuXinV2 -iterations=1 --timeline results/demo/region_yx.s
EOF

echo "cmd scripts written to $D (every command echoed as \$ before running)"

# ---- per-parameter raw gem5 log shots (user requirement: real-run log excerpts,
# ---- maximized purple Ubuntu terminal, command echoed as "$ cmd") ---------------
cat > $D/log_stream.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== R (E2 stream): vadd m1 = 1/cycle; vdivu m1 = 12/cycle (non-pipelined) =="
run grep -m 4 "vadd_vv v" experiments/e02-vadd_vv-m1-n6/build/gem5/exec.log
echo
run grep -m 3 "vdivu_vv v" experiments/e02-vdivu_vv-m1-n4/build/gem5/exec.log
EOF

cat > $D/log_chain.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== L (E3 chain): vdivu m1 interval = 12; vredsum m2 mu-ops 2 apart, macro 8 =="
run grep -m 4 "vdivu_vv v" experiments/e03-vdivu_vv-m1-n4/build/gem5/exec.log
echo
run grep -m 4 "vredsum_vs" experiments/e03-vredsum_vs-m2-n4/build/gem5/exec.log
EOF

cat > $D/log_matrix.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== G3 cross-pipe (E4 k0): dep = consumer waits; ctrl = same-tick (dep severed) =="
echo "\$ grep -m 3 -E 'vdivu_vv v|vadd_vv v' experiments/e04-vdivu_vv-x-vadd_vv-m1-k0-dep/build/gem5/exec.log"
grep -m 3 -E "vdivu_vv v|vadd_vv v" experiments/e04-vdivu_vv-x-vadd_vv-m1-k0-dep/build/gem5/exec.log
echo
echo "\$ grep -m 3 -E 'vdivu_vv v|vadd_vv v' experiments/e04-vdivu_vv-x-vadd_vv-m1-k0-ctrl/build/gem5/exec.log"
grep -m 3 -E "vdivu_vv v|vadd_vv v" experiments/e04-vdivu_vv-x-vadd_vv-m1-k0-ctrl/build/gem5/exec.log
EOF

cat > $D/log_waw.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== WAW (E5, d=2): second write to same dest issues 1 cycle later - no stall =="
run grep -m 2 "vadd_vv v" experiments/e05-vadd_vv-m1-d2-waw/build/gem5/exec.log
EOF

cat > $D/log_war.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== WAR (E6, d=2): writer overwriting the reader's source issues without stall =="
run grep -m 2 "vadd_vv v" experiments/e06-vadd_vv-vadd_vv-m1-d2-war/build/gem5/exec.log
EOF

cat > $D/log_mix.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== pipes (E7): vadd(VP0) + vredsum(VP1) co-issued SAME tick, next pair +2 =="
run grep -m 4 -E "vadd_vv v|vredsum_vs" experiments/e07-vadd_vv-vredsum_vs-m1-p4/build/gem5/exec.log
EOF

cat > $D/log_issue.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== IssueWidth (E8 sv): scalar+vector pair per tick; triple probe: 3rd pushed =="
run grep -m 6 -E "add x2[1-8]|vadd_vv v" experiments/e08-vadd_vv-m1-sv-p4/build/gem5/exec.log
echo
run grep -m 7 -E "add x2[1-8]|vadd_vv v" experiments/e08-vadd_vv-m1-triple-p4/build/gem5/exec.log
EOF

cat > $D/log_load.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== LoadLatency (E10): measured vle32 then dependent vadd = +4 ticks =="
run grep -m 2 -E "vle32_v v2|vadd_vv v3" experiments/e10-loadhit-m1-k0/build/gem5/exec.log
EOF

cat > $D/log_e11.sh <<EOF
#!/usr/bin/env bash
$RUN
cd ~/codebase/Profile-InstLatency
echo "== E11 composite: every segment's start/end markers in ONE real run =="
run grep -m 10 "__yx_marker_" experiments/e11_composite/build/gem5/exec.log
EOF

# ---- llvm-mca advanced-feature verification shots -------------------------------
cat > $D/mca_any.sh <<EOF
#!/usr/bin/env bash
$RUN
MCA=/home/zhaosiying/codebase/llvm-project/build/bin/llvm-mca
cd ~/codebase/Profile-InstLatency
echo "== ANY dual-slot: -resource-pressure spreads vmul over BOTH pipes =="
run \$MCA -mtriple=riscv64 -mcpu=YuShuXinV2 -resource-pressure -iterations=1 tests/mca_any_vmul.s
printf "(command re-echoed:)\\n\$ llvm-mca ... -resource-pressure tests/mca_any_vmul.s\\n"
EOF

cat > $D/mca_divtl.sh <<EOF
#!/usr/bin/env bash
$RUN
MCA=/home/zhaosiying/codebase/llvm-project/build/bin/llvm-mca
cd ~/codebase/Profile-InstLatency
echo "== non-pipelined R==L: --timeline shows three 12-cycle blocks, fully serial =="
run \$MCA -mtriple=riscv64 -mcpu=YuShuXinV2 -timeline -iterations=1 tests/mca_div_chain.s
EOF

cat > $D/mca_readadv.sh <<EOF
#!/usr/bin/env bash
$RUN
MCA=/home/zhaosiying/codebase/llvm-project/build/bin/llvm-mca
cd ~/codebase/Profile-InstLatency
echo "== negative ReadAdvance: cross-pipe vadd waits 12-2; same-pipe pair at 3 =="
run \$MCA -mtriple=riscv64 -mcpu=YuShuXinV2 -timeline -iterations=1 tests/mca_xpipe_readadv.s
EOF

cat > $D/mca_loadtl.sh <<EOF
#!/usr/bin/env bash
$RUN
MCA=/home/zhaosiying/codebase/llvm-project/build/bin/llvm-mca
cd ~/codebase/Profile-InstLatency
echo "== LoadLatency=4: vle32 eeeeE block, dependent vadd starts +4 =="
run \$MCA -mtriple=riscv64 -mcpu=YuShuXinV2 -timeline -iterations=1 tests/mca_load.s
EOF
