# Profile-InstLatency v2 — RVV Scheduling-Model Reverse-Engineering on gem5

[中文](#中文) | [English](#english)

---

<a id="english"></a>
## Reverse-engineering an LLVM RISC-V vector scheduling model from cycle-level gem5 profiling

**Pipeline**: minimal priors → designer micro-op parameter space (`config/yushuxin_timing_v2.yaml`) → injection into gem5 v24.1.0.3 MinorCPU via a **pure-config FU pool** (no simulator source patches) → tick-exactness gate (`verify_timing_exactness.py`, design invariants asserted per cycle) → differential experiment suite **E0–E11** (streams / RAW chains / cross-class matrix / WAW / WAR / mixed streams / issue probes) → closed-form inversion (`profile_final.py`) → LLVM `RISCVSchedYuShuXinV2.td` → **llvm-mca closure** (reciprocal throughput == gem5-measured R, per instruction per LMUL).

**Machine under test** (fictitious in-order dual-issue RV64, VLEN=256, SEW=e32, LMUL m1/m2/m4): two 1-wide vector pipes, non-pipelined divider (R≡L), no vector renaming, latency = fixed + LMUL-proportional part. Eight instruction classes (vadd/vmul/vdivu/vmseq/vredsum/vslideup/vcpop/viota).

**Headline results**
- Tick gate: `ok=23 bad=0` — E0 marker delta 0, m1 chain slopes == max(opLat−srcLat, μ), vdivu R≡L=12/24/48, μ=2 micro-op cadence verified from exec.log timestamps.
- ~740 real gem5 traces inverted: R recovered exactly for 15/24 cells, remaining 9 are **emergent machine behavior** (vmul ANY-pipe dual-slot R=1/1/2, vmseq vmask_mv cadence 4/5/7, vslideup 4/7/18) — profiled and landed in the .td as-is.
- llvm-mca `-instruction-tables` on `-mcpu=YuShuXinV2`: vdivu RThru 12.00 (non-pipelined), vmul 0.50 (dual-slot ProcResGroup), `Dispatch Width: 2`; `--all-stats --timeline` reproduces chain latencies.
- Cross-pipe no-bypass penalty encoded as negative `ReadAdvance` (producer-specific); non-identifiable fields (AcquireAtCycles, execute/writeback split) deliberately left blank — see docs/DESIGN.md chapter 6.

**Layout**: `config/` ground truth (single source) · `scripts/` generator/runner/gate/analyzers/screenshot pipeline · `gem5-configs/yushuxin/` FU pool + SE config · `llvm/` schedule model + wiring diff · `tests/` llvm-mca inputs · `results/` measured profile, evidence-matrix inputs, exec.log excerpts · `docs/DESIGN.md` full methodology.

**End-to-end case study** (blog ch.6): the same hand-written RVV intrinsic program (4-deep `vdivu` chain + 7 independent fillers) compiled with `llc -mcpu=YuShuXinV2` vs `-mcpu=generic-rv64`: the profiled model interleaves the fillers into the 12-cycle divide bubbles (visible order change), runs **125 vs 132 cycles on gem5 (+5.3%)**, and llvm-mca — using the very same model — predicts a delta of exactly **7 cycles, matching the gem5 measurement**; `--timeline` shows the dual-pipe overlap. One command: `bash scripts/build_demo.sh`.

**Reproduce**: see Appendix B of the blog / `scripts/make_all_shots.sh` for real-machine screenshots (requires an unlocked desktop).

---

<a id="中文"></a>
## 基于 gem5 周期级差分实验反演 LLVM RISC-V 向量调度模型（v2 全量重做）

**流程**：少量先验 → 设计者微操作参数空间（`config/yushuxin_timing_v2.yaml` 单一真值源）→ **纯配置**注入 gem5 v24.1.0.3 MinorCPU（零模拟器源码补丁）→ tick 精确一致性门禁 → **E0–E11 差分实验套件** → 闭式反演 → LLVM `RISCVSchedYuShuXinV2.td` → **llvm-mca 闭合验证**（RThroughput == gem5 实测 R）。

**被测机器**（假想按序双发射 RV64）：双 1 宽向量管线、非流水除法器（R≡L）、无向量重命名、延迟=固定+∝LMUL；8 个指令类 × LMUL{m1,m2,m4}。

**要点结果**
- 门禁 `ok=23 bad=0`：E0 归零、m1 链斜率=旁路延迟、vdivu R≡L=12/24/48、μop 节拍逐时间戳核验；
- 约 740 条真实 trace 反演：15/24 项 R 精确命中设计值，其余 9 项为**涌现行为**（vmul 双槽 ANY、vmseq 的 vmask_mv 节奏、vslideup 非仿生序列）——按实测原样落表；
- llvm-mca：vdivu 12.00、vmul 0.50、Dispatch Width 2；timeline 复现链延迟；
- 跨管无旁路罚 = 负 ReadAdvance（按生产者限定）；不可识别字段诚实留空（AcquireAtCycles、执行/写回分解——见 docs/DESIGN.md 第六章）。

**目录**：`config/` 真值表 · `scripts/` 全链路脚本（含真机截图流水线）· `gem5-configs/yushuxin/` · `llvm/` 模型+接线 diff · `tests/` mca 输入 · `results/` 测量档案与证据 · `docs/DESIGN.md` 完整方法论。

**端到端综合测试**（博客第六章）：同一份手写 RVV intrinsic 程序（4 深 vdivu 链 + 7 条独立填充），`llc -mcpu=YuShuXinV2` vs `generic-rv64` 双编译：模型版把填充运算排进 12 拍除法气泡（顺序重排可见），gem5 实测 **125 vs 132 周期（+5.3%）**，llvm-mca 用同一模型预测差值 **恰为 7 拍、与实测精确对齐**，`--timeline` 可视化双管 overlap。一条命令：`bash scripts/build_demo.sh`。

**复现**：博客附录 B；真机截图需解锁桌面后 `bash scripts/make_all_shots.sh`。
