# Profile-InstLatency v2 — RVV Scheduling-Model Reverse-Engineering on gem5

[中文](#中文) | [English](#english)

---

<a id="english"></a>
## Reverse-engineering an LLVM RISC-V vector scheduling model from cycle-level gem5 profiling

**Pipeline**: minimal priors → designer micro-op parameter space (`config/yushuxin_timing_v2.yaml`) → injection into gem5 v24.1.0.3 MinorCPU via a **pure-config FU pool** (no simulator source patches) → tick-exactness gate (`verify_timing_exactness.py`, design invariants asserted per cycle) → differential experiment suite **E0–E11** (streams / RAW chains / cross-class matrix / WAW / WAR / mixed streams / issue probes) → closed-form inversion (`profile_final.py`) → LLVM `RISCVSchedYuShuXinV2.td` → **llvm-mca closure** (reciprocal throughput == gem5-measured R, per instruction per LMUL) → end-to-end A/B case study.

**Machine under test** (fictitious in-order dual-issue RV64, VLEN=256, SEW=e32, LMUL m1/m2/m4): two 1-wide vector pipes, non-pipelined divider (R≡L), no vector renaming, latency = fixed + LMUL-proportional part. Eight instruction classes (vadd/vmul/vdivu/vmseq/vredsum/vslideup/vcpop/viota).

**Headline results**
- Tick gate `ok=23 bad=0`; E11 composite additivity `5/5 PASS`.
- ~1900 real gem5 traces inverted: R exact for 15/24 cells; the other 9 are **emergent machine behavior** (vmul ANY-pipe dual-slot R=1/1/2, vmseq vmask_mv cadence 4/5/7, vslideup 4/7/18) — profiled and landed as-is.
- 1185 control-paired E5/E6 runs: WAW ≤1 cycle, WAR ≈0 → **fused into ReleaseAtCycles** (documented, not hidden).
- llvm-mca `-instruction-tables` on `-mcpu=YuShuXinV2`: vdivu RThru 12.00 (non-pipelined), vmul 0.50 (dual-slot ProcResGroup), `Dispatch Width: 2`.
- **End-to-end A/B**: same hand-written RVV-intrinsic program, model vs generic-rv64 — order rewrites (fillers ride the 12-cycle divide bubbles), gem5 **125 vs 132 cycles (+5.3%)**, llvm-mca delta **exactly 7 cycles == gem5 delta**; `--timeline` shows dual-pipe overlap. One command: `bash scripts/build_demo.sh`.

**Core source map** (every number in the model traces back to one of these):

| File | Role |
|---|---|
| `config/yushuxin_timing_v2.yaml` | single source of truth: micro-op params (l_micro/μ/src_lat/pipes/non-pipelined) |
| `gem5-configs/yushuxin/fu_pool.py` | the injection: per-(pipe,μ) MinorFUs, per-class `srcRegsRelativeLats`, funct6 mask/match, non-pipelined divider, VLSU |
| `gem5-configs/yushuxin/se_yushuxin.py` | SE sim config; `cantForwardFromFUIndices` wiring = cross-pipe no-bypass |
| `scripts/yxmodel.py` | the ONE formula source shared by synthetic backend / tick gate / analyzer |
| `scripts/gen_asm_v2.py` | experiment generators + differential trio (64B-align & shadow warmup, known-cadence scalar fillers, control twins) |
| `scripts/run_v2.py` | assemble→link→gem5→`llvm-nm` marker PCs→Exec-log tick parsing |
| `scripts/verify_timing_exactness.py` | tick-exactness gate (design invariants only) |
| `scripts/analyze_v2.py` / `profile_final.py` | closed-form inversion; measured-vs-design calibration report |
| `scripts/e11_composite.py` | composite additivity test |
| `tests/demo.ll` + `scripts/build_demo.sh` + `wrap_demo.py` | end-to-end A/B case study |
| `llvm/RISCVSchedYuShuXinV2.td` + `llvm/wiring.diff` | the resulting LLVM scheduling model + registration |

**Reproduce**: Appendix B of the blog; screenshots: `bash scripts/make_all_shots.sh` (unlocked desktop required).

---

<a id="中文"></a>
## 基于 gem5 周期级差分实验反演 LLVM RISC-V 向量调度模型（v2 全量重做）

**流程**：少量先验 → 设计者微操作参数空间（`config/yushuxin_timing_v2.yaml` 单一真值源）→ **纯配置**注入 gem5 v24.1.0.3 MinorCPU（零模拟器源码补丁）→ tick 精确一致性门禁 → **E0–E11 差分实验套件** → 闭式反演 → LLVM `RISCVSchedYuShuXinV2.td` → **llvm-mca 闭合验证** → 端到端 A/B 综合测试。

**被测机器**（假想按序双发射 RV64）：双 1 宽向量管线、非流水除法器（R≡L）、无向量重命名、延迟=固定+∝LMUL；8 个指令类 × LMUL{m1,m2,m4}。

**要点结果**
- 门禁 `ok=23 bad=0`；E11 复合可加性 `5/5 PASS`；
- 约 1900 条真实 trace 反演：15/24 项 R 精确命中设计值，其余 9 项为**涌现行为**（vmul 双槽 ANY、vmseq 的 vmask_mv 节奏、vslideup 非仿生序列）——按实测原样落表；
- 1185 对 E5/E6 配对实测：WAW≤1 拍、WAR≈0 → **融合进 ReleaseAtCycles**（如实记录的融合证据）；
- llvm-mca：vdivu 12.00（非流水）、vmul 0.50（双槽 ProcResGroup）、Dispatch Width 2；
- **端到端 A/B**：同一手写 RVV intrinsic 程序，`llc -mcpu=YuShuXinV2` vs `generic-rv64`——顺序重排可见（填充进 12 拍除法气泡），gem5 实测 **125 vs 132 周期（+5.3%）**，llvm-mca 用同一模型预测差值**恰为 7 拍、与实测精确对齐**，`--timeline` 可视化双管 overlap。一条命令：`bash scripts/build_demo.sh`。

**核心源码地图**（模型里每个数字都能追到其中一行）：

| 文件 | 角色 |
|---|---|
| `config/yushuxin_timing_v2.yaml` | 单一真值表：微操作参数（l_micro / μ / src_lat / 管线 / 非流水） |
| `gem5-configs/yushuxin/fu_pool.py` | 时序注入：按 (管线,μ) 分 FU、按类 `srcRegsRelativeLats`、funct6 mask/match、非流水除法器、VLSU |
| `gem5-configs/yushuxin/se_yushuxin.py` | SE 仿真配置；`cantForwardFromFUIndices` 接线 = 跨管无旁路 |
| `scripts/yxmodel.py` | 唯一公式源（合成后端 / tick 门禁 / 分析器三方共用） |
| `scripts/gen_asm_v2.py` | 实验生成器 + 差分三件套（64B 对齐与影子预热、已知节奏标量填充、对照孪生） |
| `scripts/run_v2.py` | 汇编→链接→gem5→`llvm-nm` 解析 marker PC→Exec 日志 tick 解析 |
| `scripts/verify_timing_exactness.py` | tick 门禁（只断言设计直接承诺的不变量） |
| `scripts/analyze_v2.py` / `profile_final.py` | 闭式反演；实测 vs 设计校准报告 |
| `scripts/e11_composite.py` | 复合可加性实验 |
| `tests/demo.ll` + `scripts/build_demo.sh` + `wrap_demo.py` | 端到端 A/B 综合测试 |
| `llvm/RISCVSchedYuShuXinV2.td` + `llvm/wiring.diff` | LLVM 调度模型与注册接线 |

**复现**：博客附录 B；真机截图需解锁桌面后 `bash scripts/make_all_shots.sh`。
