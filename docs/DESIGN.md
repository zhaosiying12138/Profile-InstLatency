# YuShuXin-V2：先验 + 未知参数 + gem5 实现 + 差分 profile 重设计

> 版本 v2（2026-09-10）。取代 Profile-InstLatency 仓库中 `config/rvv_timing_model.yaml`（v1 合成真值）与 T00–T40 实验体系。
> 本文档是完整的设计基线：(A) 先验已知；(B) 未知参数全集与合理设定值（= 将注入 gem5 的"地面真值"）；(C) LLVM 侧旋钮全集；(D) gem5 实现方案（tick 级精确一致）；(E) 差分实验矩阵（每个未知参数 ← 恢复它的实验）。

---

## 0. v1 为什么不合理（动机，来自对旧工程的分析）

对旧仓库 `results/` 的交叉验证结论：

1. **真实平台数据是 gem5 默认配置的伪影**。gem5 v24.1.0.3 MinorCPU 默认 FU 池中，所有向量 OpClass（SimdAdd/SimdMult/SimdDiv/SimdCmp/…）都路由到**同一个** `MinorDefaultFloatSimdFU`（opLat=6, srcRegsRelativeLats=[2], issueLat=1）。因此旧实测"vadd=vmul=vdivu=4 周期、全部全流水、全部单资源"恰为 6−2=4 的退化结果；vdivu 走 SimdDiv 也在同一 FU，除法与加法无异。**旧 LLVM 模型（Latency=4, Release=LMUL）建模的是 gem5 的默认参数，不是任何处理器。**
2. **双管先验与平台矛盾**：单一 FloatSimdFU → T20 全部判 serial → 一切归 VPipe0，VPipe0/VPipe1 只是镜像对称的字典序规范。
3. **合成 cmodel 与真实 gem5 公式不一致**：合成 T11 造 Δ=N·L（analyzer Δ/N 反推），真实 gem5 是 Δ=(N−1)·L+(R−1) 尾项；T10 合成 N·R vs 真实 N·R−1。合成校准 PASS 不验证真实推断公式。
4. **可识别性缺陷**：不可链指令（vmseq/vcpop/viota/vslideup/vrgather）无 T11，只能靠 T12 上界；vcpop m4 又有取指边界扰动 → 大面积 non_identifiable。
5. **v1 真值表自身问题**：如 vdivu latency 12+6λ 与 release 4+2λ 不相等（半流水的除法器，物理上不成立——非流水除法应 R≡L）；vadd 延迟 2+0λ 与 vmseq 2+0λ 数值撞车，可区分性差；无 WAR/WAW/跨管前递/写回口等维度。

v2 的原则：**设定值本身要物理自洽、彼此可区分；每个未知参数至少有一个专差分实验能唯一恢复它；gem5 行为必须与设定 tick 级一致并由此构造自动校验。**

---

## A. 先验已知（不 profile，作为假设钉死；仍要求实验"无矛盾"证据）

| # | 先验 | 用途/落点 |
|---|---|---|
| P1 | 按序发射、按序提交、无 ROB | LLVM `MicroOpBufferSize = 0` |
| P2 | 无向量寄存器重命名 | ⇒ WAR/WAW 反依赖是真实停顿，必须测定（v1 完全没测） |
| P3 | 每周期最多发射 2 条微操作（标量管 1 + 向量管 1，或两条不同向量管） | LLVM `IssueWidth = 2`（仍用 E8 正面证实且证伪 ≥3） |
| P4 | 两条向量执行管线 VPipe0/VPipe1，各 1 微操作/周期 | LLVM `ProcResource×2` |
| P5 | **除法非流水**（占用整个管线直到完成）；**其余指令全流水** | 决定 R 的形态约束 |
| P6 | 指令延迟 = 固定开销 + 可变开销，可变部分 ∝ LMUL（λ∈{1,2,4}），SEW=e32，VLEN=256 | L = L_base + L_k·λ；R 同理 |
| P7 | 时间戳 marker 零开销（纯标号，锚定下一条指令 PC） | 方法论前提，T00 验证 |
| P8 | 标量 ALU：L=1, R=1（IntFU 语义：opLat=3−srcLat=2 之类由实现校准为有效 1） | 配对/对照指令 |
| P9 | gem5 v24.1.0.3 RiscvMinorCPU、1GHz、带 cache；llvm-mc/ld.lld 工具链 | 环境 |

## B. 未知参数全集 + v2 地面真值（"我们的设定"，profile 的恢复目标）

### B.1 参数空间（设计者旋钮，不必与 LLVM 一一对应）

**机器级（全局）**
| 旋钮 | 含义 | v2 设定 |
|---|---|---|
| G1 `issue_width` | 每周期发射微操作数 | 2 |
| G2 `n_vector_pipes` | 向量管线数 | 2（VPipe0, VPipe1） |
| G3 `xlat` | 跨管线消费额外延迟（无跨管前递，需经写回+读寄存器堆） | +2 |
| G4 `vec_to_gpr_lat` | 向量结果→标量读 额外延迟 | +1 |
| G5 `load_hit_lat` | 向量 load 命中延迟（vle32，cache 热） | 4 |
| G6 `vl_beats` | VLSU 每寄存器节拍数 | 1（load R=λ·1） |

**每指令类（8 类，λ = LMUL ∈ {1,2,4}）**
| 旋钮 | 含义 | 形式 |
|---|---|---|
| K1 `L = L_base + L_k·λ` | 同管线 RAW 延迟（结果就绪，可前递） | 线性 |
| K2 `R = R_base + R_k·λ` | 宏指令发射间隔（资源占用；非流水类 R≡L） | 线性 |
| K3 `pipe ∈ {VP0, VP1, ANY}` | 管线归属；ANY=两条皆可（对应 ProcResGroup） | 枚举 |
| K4 `pipelined` | 是否全流水 | 布尔（v2: 仅 vdivu=false） |
| K5 `waw_extra` | WAW 同目的寄存器额外间距（写在 L 之上：间距 = L + waw_extra） | 常数 |
| K6 `read_lat` | 源寄存器读出时刻（发射后第 read_lat 周期读完）→ 决定 WAR 释放 | 常数 |
| K7 `nmops` | LLVM 微操作数计法 | 全部 1（宏建模，LMUL 计入 R） |

### B.2 v2 地面真值表（完整列出；profile 必须恰好恢复这些数）

L/R 括号内为 λ=1/2/4 时的值。

| 指令 | gem5 OpClass(预期) | 管线 | 流水 | L_base, L_k | R_base, R_k | waw_extra | read_lat |
|---|---|---|---|---|---|---|---|
| `vadd.vv` | SimdAdd | VP0 | 是 | 2, 1 → L=3/4/6 | 0, 1 → R=1/2/4 | 1 | 1 |
| `vmul.vv` | SimdMult | **ANY** | 是 | 3, 1 → L=4/5/7 | 1, 1 → R=2/3/5 | 1 | 1 |
| `vdivu.vv` | SimdDiv | VP1 | **否** | 8, 4 → L=12/16/24 | **R≡L** | 2 | 2 |
| `vmseq.vv` | SimdCmp | VP0 | 是 | 2, 0 → L=2/2/2 | 0, 1 → R=1/2/4 | 1 | 1 |
| `vredsum.vs` | SimdReduceAdd | VP1 | 是 | 4, 2 → L=6/8/12 | 2, 1 → R=3/4/6 | 2 | 1 |
| `vslideup.vx` | SimdMisc(预期) | VP0 | 是 | 2, 2 → L=4/6/10 | 1, 2 → R=3/5/9 | 1 | 1 |
| `vcpop.m` | SimdPredAlu | VP0 | 是 | 3, 0 → L=3/3/3 | 1, 0 → R=1/1/1 | 1 | 1 |
| `viota.m` | SimdPredAlu/SimdCvt(待验证) | VP0 | 是 | 3, 2 → L=5/7/11 | 0, 1 → R=1/2/4 | 1 | 1 |
| (标量 `add`) | IntAlu | 标量管 | 是 | L=1/1/1 | R=1/1/1 | — | — |
| (对照 `vle32.v`) | SimdUnitStrideLoad | VLSU | — | G5: L=4 | G6: R=λ | — | — |

设计说明（为什么这样选值）：
- **可区分性**：8 类的 (L_base, L_k) 两两不同：(2,1)(3,1)(8,4)(2,0)(4,2)(2,2)(3,0)(3,2)；(B,K) 组合亦无两类全同。R 形态覆盖：k=0（vcpop）、base=0（vadd/vmseq/viota）、base=1（vmul/vslideup）、base=2（vredsum）、非流水（vdivu）。L 覆盖 k=0（vmseq/vcpop）与 k∈{1,2,4}。任何两类都至少在 L 或 R 的一维上可分离。
- vcpop 读单个掩码寄存器（VLEN 位）→ 与 λ 无关（k=0 的物理来源）；viota 写 λ 组寄存器 → 随 λ 增长；vdivu 非流水 R≡L。
- vmseq 写掩码 v0：用 vcpop/viota 作消费者链测其 L（跨类 RAW，同时标定 G3/G4）。
- vredsum 读 vd+vs1+vs2 三源（vd 兼累加器），自链形状特殊，单独模板。
- 注意 vmul(ANY) 与 vslideup(VP0) 的 L 同为 4/… 起点（(3,1) vs (2,2) 在 λ=1 时都是 4），但斜率不同（5,7 vs 6,8），λ 扫描可分离——设计上故意留一个"单点撞车、斜率分离"的案例来检验拟合流程。

RAW 有效延迟矩阵（producer 行 → consumer 列所在管线；Δ = L(producer) + 罚项）：
- 同管线（含 vmul 与对方同管时）：+0
- 跨向量管线（VP0↔VP1）：+G3=2
- 向量→标量消费者（vcpop 结果→add）：+G4=1
- load→向量消费者：+0（load 前递，L=4）

WAW 间距（同目的寄存器相继两次写，无其它依赖时最小间隔）：`L(producer) + waw_extra`（vdivu: 12+2=14 @m1 …；vredsum: 8 @m1）。
WAR 释放（写者须等此前读者读完源）：读者发射后 `read_lat` 周期释放（全类 1，除 vdivu 2）。

### B.3 未知参数计数（profile 的恢复目标清单）

全局 6（G1–G6）+ 每类 6（K1–K6，K7 全 1）×8 类 = 54 个未知量；先验 9 条（A 节）。

---

## C. LLVM 侧可调旋钮全集（读自 llvm trunk 源码：`MCSchedule.h`、`TargetSchedule.td`、`RISCVScheduleV.td`；教程：2025 US LLVM Dev Mtg《Scheduling Model in LLVM: Past, Present, and Future》、2017《Writing Great Machine Schedulers》）

### C.1 SchedMachineModel（机器级）
| 旋钮 | 类型/默认 | 语义 | 我们的落点 |
|---|---|---|---|
| IssueWidth | 1 | 每周期发射组内最大微操作数（硬性按序约束） | 2（E8 证实） |
| MicroOpBufferSize | 0 | 0/1=按序；>1=乱序 | 0（P1） |
| LoopMicroOpBufferSize | 0 | 循环缓冲优化目标微操作数 | 不建模 |
| LoadLatency | 4 | load 期望延迟（启发式） | 4（E10） |
| HighLatency | 10 | "高延迟"阈值 | 不建模 |
| MispredictPenalty | 10 | 分支误预测代价 | 不建模 |
| PostRAScheduler | false | 是否跑 RA 后调度 | false |
| CompleteModel | true | 未建模指令报错 | bringup 期 false → true |
| FullInstRWOverlapCheck / UnsupportedFeatures / NoModel / EnableIntervals | — | 校验/特性开关 | 默认 |

### C.2 资源
| 旋钮 | 语义 |
|---|---|
| `ProcResource<NumUnits>` | 资源种类与份数（份数=吞吐） |
| `Super` | 资源包含关系（用子资源即占用父资源） |
| `BufferSize` | −1 缓冲（乱序）；**0 = 按序发射资源**（调度器按 ReleaseAtCycles 计数占用）；1 = 按序延迟资源 |
| `ProcResGroup<[...]>` | 资源组：写取组内任一资源（vmul 的 ANY 管线 → `YuShuXinVAnyPipe`） |

### C.3 每写（WriteRes/SchedWriteRes）
| 旋钮 | 语义 | 我们的落点 |
|---|---|---|
| Latency | 生产者→消费者就绪周期 | L 表 |
| ReleaseAtCycles[] | 资源占用周期（空=1 周期=全流水；0=须可用不消耗） | R 表 |
| AcquireAtCycles[] | 延迟占用资源的起始周期 | **诚实留空**（实验不可分辨） |
| NumMicroOps | 微操作数（计入 IssueWidth） | 1 |
| BeginGroup / EndGroup / SingleIssue | 发射组形态（SingleIssue=两者） | false（E8） |
| RetireOOO | 仅 llvm-mca 按序目标使用 | 不设 |
| Unsupported | 标记不支持的调度类 | — |

### C.4 每读（ReadAdvance/SchedReadAdvance）
`Cycles`（可负，负值=跨域惩罚）、`ValidWrites`（旁路矩阵：只对特定生产者生效）。落点：跨管线罚 G3=2 → 对"消费另一管线的读"给 `ReadAdvance −2`（或等价地把跨管线写延迟抬高，二选一，文档声明）。

### C.5 组合与 RISC-V 机制
`WriteSequence`（延迟可加）、`SchedWriteVariant/SchedReadVariant`（按谓词选择——RISCV 用它做 **per-LMUL/SEW 写**：`WriteVIALUV_M1/M2/M4…` 家族）、`InstRW/ItinRW/SchedAlias`。llvm-mca 附加（非调度器消费）：`RegisterFile`、`RetireControlUnit`、`LoadQueue/StoreQueue`（按序流水视图、发射组模拟）。

### C.6 本练习**不**profile 的（政策/不可观测）：MispredictPenalty、LoopMicroOpBufferSize、BufferSize>1、RegisterFile 系列、RetireControlUnit、AcquireAtCycles（可讨论专门实验，默认留空）。

---

## D. gem5 实现方案（tick 行为与设定精确一致）

### D.1 机制映射（为什么旧数据是 4：opLat−srcLat）
MinorCPU 记分牌：`returnCycle[reg] = issue + opLat`；消费者可提前 `srcRegsRelativeLats` 发射 ⇒ **可观测 RAW 延迟 = opLat − srcLat**。`issueLat` = 同 FU 相继发射间隔（非流水 ⇔ issueLat=opLat）。`cantForwardFromFUIndices` = 指定来源 FU 的结果不得前递（跨管罚）。`extraCommitLat` 推迟记分牌清空（WAW 间距）。`extraAssumedLat` 追加结果可见延迟。

### D.2 两层实现

**层 1（纯 config，零源码改动）——基础可实现形式**
- 自定义 `MinorFU`：把向量 OpClass 拆到多个 FU：
  - `YXVPipe0`：opClasses=[SimdAdd, SimdCmp, SimdPredAlu, SimdMisc…] opLat/sRRL 按"该 FU 内最难类"取值；
  - `YXVPipe1`：opClasses=[SimdDiv, SimdReduceAdd]，vdivu `issueLat=opLat`（非流水）；
  - vmul（ANY）：SimdMult 同时加入两 FU。
- 局限：opLat/issueLat 是 **FU 级常数**——(a) 同 FU 内多类无法异 opLat（只能用 srcRegsRelativeLats 差分有效延迟，但 R 仍同）；(b) **无法表达 L=R_base+R_k·λ**（R 只能=λ·issueLat 或常数）；(c) 非流水除法经微操作拆分后 R_macro=λ·opLat≠L。⇒ 层 1 只能实现 B.2 表的一个退化子集（每类 L_k∈{0, 隐式λ−1}、R∈{常数, kλ}）。

**层 2（小补丁，v2 主方案）——RVV 宏级时序表**
新增 `src/cpu/minor/` 极薄扩展 + RVV 拆分点挂钩：
1. `MinorFUTiming` 增加可选 `opLatExpr`/`issueLatExpr`（TimingExpr），命中 `(mask,match)` 或 OpClass 的 timing 覆盖 FU 级 opLat/issueLat；`FUPipeline` 按微操作读取覆盖值。
2. RVV 宏拆分处（m2/m4 → λ 个微操作）按 **(指令, λ) 查表** 设置每微操作 opLat/issueLat：微操作 k 发射于 k·rλ，rλ=ceil(R/λ) 类拆分（或宏单微操作模式：非流水 vdivu 整宏 1 个微操作、opLat=issueLat=L(λ)，从根上保证 R≡L）。表由 `config/yushuxin_timing_v2.yaml` 生成（脚本 → C++ 表/Python SimObject 参数）。
3. 跨管罚 G3：两向量 FU 互相 `cantForwardFromFUIndices`（此时 RAW 延迟=opLat 全写回 ⇒ 同管 L=opLat−srcLat、跨管=opLat，差值即 G3，配置成 2）。G4：vcpop 的标量写回置 extraAssumedLat=1。WAW：extraCommitLat=waw_extra−1（校准式）。WAR：srcRegsRelativeLats=read_lat。
4. **tick 一致性自动校验（新）**：`scripts/verify_timing_exactness.py` 对每个原语模式（单指令、流、链、WAW、WAR、跨管对、混合）用 B.2 表**解析计算**期望 marker Δ，逐条 assert 与 gem5 实测相等。校验通过 ⇒ "gem5 行为与设定精确一致"成为可回归的断言，而非口头声明（v1 缺失的关键闭环）。

### D.3 落地物
`config/yushuxin_timing_v2.yaml`（B.2 表机读版）、`gem5/configs/yushuxin/fu_pool.py`（层 1）、`gem5-patches/0001-minor-per-timing-oplat-issuelat.patch`（层 2）、`scripts/verify_timing_exactness.py`、汇编仍 llvm-mc(+v,+zvl256b)+ld.lld(−Ttext=0x80000000)。VLEN=256 ⇒ +zvl256b（v1 用 +zvl128b 但 VLEN=256 由参数暴露，保持一致即可）。

---

## E. 差分实验矩阵（每个未知参数 ← 唯一恢复它的实验）

记号：Δ=start/end marker 差；N=重复数；λ∈{1,2,4}；D(x)=对 x 差分（同程序去依赖对照）。所有模板先 E0/E1 过门。

| 实验 | 模板（汇编形态） | 观测 | 闭式反演 | 恢复的参数 |
|---|---|---|---|---|
| E0 marker 基线 | 相邻双 marker | Δ | Δ=0 | P7 |
| E1 可执行性 | vsetvli+初始化+I+marker | 正常退出 | — | 门禁 |
| E2 独立流 N 扫描 | marker; I×N(目的轮转); marker，N∈{2,3,4,6,8,12} | Δ(N) | R=斜率=(Δ_max−Δ_min)/(N_max−N_min)；截距=startup 须与模型一致；**R≡L 且斜率大 ⇒ 非流水** | R(B,K) per (I,λ)、K4 |
| E3 同管 RAW 链 | I 自链×N（vredsum 特判三源形） | Δ(N) | L=斜率；尾项=λ−1+…（模型已知，校验用） | L(B,K) |
| E4 跨类 RAW 矩阵 | producer i → (k fillers) → consumer j，(i,j) 全 64 对×k 扫描；**对照组：consumer 改读独立寄存器**（D） | Δ(i,j,k)−Δ_ctrl(k) | 差值在 k 平坦段 = L(i)+罚(管(i)→管(j))；对角=罚 0 ⇒ 分离 G3、G4 | 跨管罚矩阵、vmseq/vcpop 等"不可自链"类的 L |
| E5 WAW 对 | I v_a; (d fillers); I v_a，d 扫描；对照写异寄存器 | 最小无气泡 d | WAW 间距 = L+waw_extra ⇒ 差分得 waw_extra | K5 |
| E6 WAR 对 | J 读 v_a; (d fillers); I 写 v_a，d 扫描；对照 I 写异寄存器 | 最小无气泡 d | 释放=J 发射后 read_lat ⇒ 差分得 read_lat | K6（P2 的定量化） |
| E7 管线归属混合流 | 流(i) ∥ 流(j) 交错（i,j 全对）；对照：纯流(i)+纯流(j) 分跑相加 | 聚合斜率 | 聚合吞吐=2/周期(和) ⇒ 异管；=Ri+Rj(串) ⇒ 同管；部分重叠 ⇒ ANY | K3 管线划分 + ProcResGroup |
| E8 发射宽探测 | 标量+向量同周期对；向量+向量（异管）对；标量+向量+向量 三联 | 同周期发射计数 | 计数=2 而 3 失败 ⇒ IssueWidth=2；异管向量对可同发 ⇒ 双管实证；SingleIssue=false | G1、P3、P4 |
| E9 λ 扫描 | E2–E6 全部 × λ∈{1,2,4} | 各 (B,K) 点 | 线性拟合 B,K（两参数两点定，三点校验残差=0；**值表两两可区分 ⇒ 唯一解**） | 全部 K1/K2 的 B,K |
| E10 load 命中 | vle32(v 热) → consumer 间距 | 间距 | =G5 | G5、G6 |
| E11 复合可加性 | 混合段+标量排空分隔 | 段 Δ 和 | 预测=实测（回归门禁） | 全模型交叉验证 |

推断器要求：闭式优先（每个 E 有解析式），搜索只做交叉校验；不可识别必须给出"缺哪个差分"而不是空手而归。置信状态：exact_fit / bounded / non_identifiable(+缺失实验名)。

### E→LLVM 字段落点总表
IssueWidth=2←E8；MicroOpBufferSize=0←P1；Latency←E3/E4/E9；ReleaseAtCycles←E2/E9；ProcResource/Group←E7；ReadAdvance(−G3)←E4；LoadLatency←E10；NumMicroOps=1、SingleIssue=false←E8；AcquireAtCycles 留空（诚实声明）；WAW/WAR 为平台事实记录（LLVM 无直接字段，写入 mapping 文档）。

---

## F. 与 v1 的对照（改动清单）

| v1 | v2 |
|---|---|
| gem5 原生时序（默认 FloatSimdFU，全 L=4） | 显式注入 B.2 设定（层 1 config + 层 2 补丁），tick 级校验 |
| 合成 cmodel 公式 ≠ gem5 公式 | 合成后端直接复用同一"解析期望计算器"（E 系闭式），双后端共用公式，消灭 off-by-one |
| 无 WAR/WAW/跨管/写回维度 | E4/E5/E6 + G3/G4/K5/K6 |
| vdivu 半流水（R≠L）不自洽 | 非流水 R≡L，issueLat=opLat 实现并校验 |
| 值表撞车、不可识别大面积 | 值表两两可区分；每个未知量绑定至少一个差分实验；对照组普遍化 |
| T20 全 serial→单资源伪影 | 双 FU 真分派；E7 混合流判管 |
| 质量门禁靠覆盖/重复 | 覆盖/重复 + **解析期望逐点相等**（校验即门禁） |
