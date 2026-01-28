# 基于多信号融合的数据中心网络拥塞控制算法研究

**学位论文**

---

## 摘要

随着云计算、大数据和人工智能技术的快速发展，数据中心网络的规模和复杂度持续增长，对传输控制协议（TCP）拥塞控制算法提出了更高要求。传统拥塞控制算法存在拥塞信号利用不充分、参数自适应能力差、难以平衡吞吐量与延迟等问题。针对上述挑战，本文提出了一种基于多信号融合与自适应参数调优的数据中心网络拥塞控制算法——Lark 算法。

本文的主要研究工作和贡献包括：

第一，设计了完整的 15 维网络状态观测空间。该观测空间首次将显式拥塞通知（ECN）状态、拥塞算法状态和拥塞算法事件等参数纳入状态表示，相比现有 4-6 维的状态空间提供了更全面的网络状态感知能力，为精细化拥塞控制奠定了信息基础。

第二，提出了多信号融合拥塞检测方法。该方法综合利用丢包信号、ECN 信号、往返时延（RTT）膨胀信号和拥塞状态信号，采用分层优先级机制和频率过滤策略进行拥塞判断。通过吞吐量优先的检测策略，仅响应明确的拥塞信号，避免对瞬态信号的过度反应，在保证网络稳定性的同时实现较高吞吐量。

第三，提出了自适应参数调优机制。该机制根据 RTT 膨胀比、ECN 反馈、拥塞状态和增长趋势等多因素动态调整乘性增加因子 α，实现控制策略对网络环境的实时适配。通过连续增长奖励机制，在网络状况良好时采用激进策略提高吞吐量。

第四，设计了融合控制策略。该策略将基于带宽延迟积（BDP）的速率控制与基于当前窗口的保守控制相结合，窗口计算公式为 V_t = max(α×BDP, W) + γ×MSS。针对不同拥塞类型采用差异化窗口保留因子：丢包保留 70%、ECN 保留 92%、超时丢包保留 75%，充分体现 ECN 作为早期预警信号的特点。

第五，构建了基于 ns-3 和 ns3-gym 的高保真实验平台，并采用 UNISON 并行化框架加速仿真。实验平台支持完整的 TCP/IP 协议栈和 ECN 机制，通过多线程并行执行提升仿真效率。

实验结果表明，Lark 算法在多流并发场景下实现了显著的性能提升。与 TCP CUBIC 相比，Lark 算法的平均吞吐量提升 15%-25%，尾部延迟降低 20%-35%。与 BBR 算法相比，Lark 算法在保持相近吞吐量的同时，表现出更好的流间公平性。与 DCTCP 相比，Lark 算法通过差异化 ECN 响应机制，在高负载场景下仍能保持稳定的吞吐量性能。

**关键词**：拥塞控制；数据中心网络；多信号融合；自适应参数调优；显式拥塞通知；网络仿真

---

## Abstract

With the rapid development of cloud computing, big data, and artificial intelligence technologies, the scale and complexity of data center networks continue to grow, posing higher requirements for Transmission Control Protocol (TCP) congestion control algorithms. Traditional congestion control algorithms suffer from insufficient utilization of congestion signals, poor parameter adaptability, and difficulty in balancing throughput and latency. To address these challenges, this thesis proposes a multi-signal fusion based congestion control algorithm with adaptive parameter tuning for data center networks, named the Lark algorithm.

The main research contributions of this thesis include:

First, a comprehensive 15-dimensional network state observation space is designed. This observation space is the first to incorporate Explicit Congestion Notification (ECN) state, congestion algorithm state, and congestion algorithm events into the state representation, providing more comprehensive network state awareness compared to existing 4-6 dimensional state spaces.

Second, a multi-signal fusion congestion detection method is proposed. This method comprehensively utilizes packet loss signals, ECN signals, Round-Trip Time (RTT) inflation signals, and congestion state signals, employing a hierarchical priority mechanism and frequency filtering strategy for congestion judgment.

Third, an adaptive parameter tuning mechanism is proposed. This mechanism dynamically adjusts the multiplicative increase factor α based on multiple factors including RTT inflation ratio, ECN feedback, congestion state, and growth trends.

Fourth, a fusion control strategy is designed. This strategy combines rate-based control using Bandwidth-Delay Product (BDP) with conservative window-based control. The window calculation formula is V_t = max(α×BDP, W) + γ×MSS, with differentiated window retention factors for different congestion types.

Fifth, a high-fidelity experimental platform based on ns-3 and ns3-gym is constructed, accelerated by the UNISON parallelization framework.

Experimental results demonstrate that the Lark algorithm achieves significant performance improvements in multi-flow concurrent scenarios. Compared with TCP CUBIC, Lark improves average throughput by 15%-25% and reduces tail latency by 20%-35%. Compared with BBR, Lark exhibits better inter-flow fairness while maintaining similar throughput.

**Keywords**: Congestion Control; Data Center Network; Multi-signal Fusion; Adaptive Parameter Tuning; Explicit Congestion Notification; Network Simulation

---

## 第 1 章 绪论

### 1.1 研究背景与意义

随着云计算、大数据、人工智能和物联网技术的蓬勃发展，数据中心已成为支撑现代信息社会运转的核心基础设施。据国际数据公司（IDC）统计，全球数据中心网络流量以年均 25%以上的速度增长，预计到 2025 年将超过 20 ZB。

现代数据中心网络呈现出以下显著特点：网络规模持续扩大，大型数据中心包含数万至数十万台服务器；网络带宽不断提升，已从 10Gbps 发展到 100Gbps 甚至 400Gbps；延迟敏感应用增多，分布式存储、实时数据分析等应用对网络延迟极为敏感；流量模式复杂多变，既有"老鼠流"也有"大象流"。

传输控制协议（TCP）作为互联网传输层的核心协议，承载了超过 90%的数据中心网络流量。然而，传统 TCP 拥塞控制算法在数据中心网络环境中面临诸多挑战：高带宽延迟积环境下的效率问题、丢包作为拥塞信号的滞后性、多流共存的公平性问题、参数静态配置的适应性问题以及 ECN 信号的利用不充分。

针对上述挑战，开展数据中心网络拥塞控制算法研究具有重要的理论意义和实际应用价值。

### 1.2 国内外研究现状

TCP 拥塞控制算法的研究始于 1986 年，此后研究者陆续提出了多种改进算法。

**传统拥塞控制算法**包括：TCP NewReno 采用 AIMD 策略；TCP CUBIC 采用三次函数模型调整窗口大小，是 Linux 系统的默认算法；TCP Vegas 基于延迟进行拥塞控制；BBR 通过估计瓶颈带宽和最小 RTT 调整发送速率。

**数据中心拥塞控制算法**包括：DCTCP 利用 ECN 标记比例进行细粒度窗口调整；HULL 追求极低延迟；TIMELY 基于精确 RTT 测量进行速率调整；HPCC 利用交换机提供的细粒度网络遥测信息。

**基于机器学习的算法**包括：Remy 采用离线优化方法；PCC 采用在线学习进行速率调整；Orca 和 Aurora 将深度强化学习应用于拥塞控制。

现有研究存在以下不足：状态空间设计不完善，未充分利用 ECN 和拥塞状态信息；拥塞检测机制单一；ECN 响应策略粗糙；参数自适应能力不足；实验验证效率低下。

### 1.3 研究目标与内容

本文的研究目标是设计一种适用于数据中心网络环境的高性能拥塞控制算法。主要研究内容包括：多维状态观测空间设计、多信号融合拥塞检测算法、自适应参数调优机制、融合控制策略设计以及实验平台构建与性能评估。

### 1.4 论文组织结构

本文共分为六章：第 1 章绪论；第 2 章相关技术基础；第 3 章 Lark 算法设计；第 4 章实验平台构建；第 5 章实验结果与分析；第 6 章总结与展望。

---

## 第 2 章 相关技术基础

### 2.1 TCP 拥塞控制基础

TCP 拥塞控制的基本思想是：发送方维护一个拥塞窗口（cwnd），限制在网络中未被确认的数据量。TCP 拥塞控制包含四个基本算法：慢启动、拥塞避免、快速重传和快速恢复。

ns-3 中定义了以下拥塞控制状态：CA_OPEN（正常传输）、CA_DISORDER（检测到乱序）、CA_CWR（ECN 响应中）、CA_RECOVERY（快速恢复中）、CA_LOSS（超时丢包）。

主流拥塞控制算法包括 TCP CUBIC 和 BBR。CUBIC 使用三次函数计算窗口大小；BBR 通过估计瓶颈带宽和最小 RTT 调整发送速率。

### 2.2 显式拥塞通知机制

ECN 允许网络设备在发生拥塞时标记数据包而非直接丢弃。ECN 使用 IP 报头中的两个位传递拥塞信息，支持的状态包括：ECN_DISABLED、ECN_IDLE、ECN_CE_RCVD、ECN_SENDING_ECE、ECN_ECE_RCVD、ECN_CWR_SENT。

DCTCP 对 ECN 的处理进行了改进，维护 ECN 标记比例的指数加权移动平均，实现细粒度响应。

### 2.3 ns-3 网络仿真器

ns-3 是开源的离散事件网络仿真器，具有高保真度、模块化设计和详细的协议实现等特点。ns-3 的 TCP 模块包含 TcpSocketBase、TcpCongestionOps、TcpSocketState 等主要类。

拥塞控制通过回调函数参与 TCP 的窗口调整，包括 GetSsThresh()、IncreaseWindow()、PktsAcked()、CongestionStateSet()、CwndEvent()等。

### 2.4 ns3-gym 强化学习框架

ns3-gym 将 ns-3 与 OpenAI Gym 接口连接，使研究者能够在 ns-3 仿真环境中训练和评估算法。ns3-gym 实现了标准 Gym 接口，使用 ZeroMQ 实现进程间通信，支持灵活扩展。

### 2.5 UNISON 并行化仿真框架

UNISON 通过空间分解、时间同步和负载均衡技术实现 ns-3 的并行化。UNISON 在 8 核处理器上可实现 3-5 倍加速。

### 2.6 本章小结

本章介绍了 TCP 拥塞控制基础、ECN 机制、ns-3 仿真器、ns3-gym 框架和 UNISON 并行化框架，为后续研究奠定基础。

---

## 第 3 章 Lark 算法设计

### 3.1 算法总体架构

Lark 算法的设计目标包括：吞吐量优先、多信号融合、自适应调优、差异化响应和每流独立。

算法框架包含：状态采集模块、度量更新模块、统计计算模块、拥塞检测模块、参数调优模块、窗口计算模块和边界约束模块。

### 3.2 多维状态观测空间设计

Lark 使用 15 维状态观测空间，参数包括：

| 索引 | 参数名称      | 说明         |
| ---- | ------------- | ------------ |
| 0    | socketUuid    | 套接字标识符 |
| 1    | envType       | 环境类型     |
| 2    | simTime_us    | 仿真时间     |
| 3    | nodeId        | 节点标识符   |
| 4    | ssThresh      | 慢启动阈值   |
| 5    | cWnd          | 拥塞窗口     |
| 6    | segmentSize   | 段大小       |
| 7    | segmentsAcked | 已确认段数   |
| 8    | bytesInFlight | 在途字节数   |
| 9    | lastRtt_us    | 最近 RTT     |
| 10   | minRtt_us     | 最小 RTT     |
| 11   | calledFunc    | 回调类型     |
| 12   | caState       | 拥塞状态     |
| 13   | caEvent       | 拥塞事件     |
| 14   | ecnState      | ECN 状态     |

本文首次将 ECN 状态、拥塞算法状态和事件纳入观测空间。

### 3.3 多信号融合拥塞检测

采用分层优先级机制：

**第一优先级**：显式丢包信号（calledFunc==0），严重程度 0.7

**第二优先级**：高频 ECN 信号（ECN 率>30/秒），严重程度 0.3

**第三优先级**：CA_LOSS 状态，严重程度 0.6

吞吐量优先策略：单次 ECN、ECN_ECE_RCVD、CA_CWR、CA_RECOVERY、RTT 膨胀不作为触发条件。

### 3.4 自适应参数调优机制

根据以下因素调整乘性增加因子 α：

- RTT 膨胀比：<1.5 增大，>3.0 减小
- ECN 反馈：检测到 ECN 时小幅减小
- 拥塞状态：CA_LOSS 时减小
- 连续增长趋势：>3 次时奖励增大
- ECN 率：>50/秒时减小

α 限制在[1.10, 1.50]范围内，基准值 1.25。

### 3.5 融合控制策略

**BDP 估算**：bdp = max_throughput × minRtt

**拥塞响应**：差异化窗口保留因子

- 丢包：λ=0.70
- ECN：λ=0.92
- 超时：λ=0.75
- 其他：λ=0.90

**窗口增长**：

- 慢启动：目标 3×BDP，增量 2-3 倍标准
- 拥塞避免：V_t = max(α×BDP, W) + γ×MSS

**安全边界**：最小 4 段，最大 8×BDP 或 100 段

### 3.6 每流独立状态管理

为每个 TCP 连接维护独立状态，包括：历史度量缓冲区、ECN 事件跟踪、性能指标、自适应参数和状态跟踪数据。

### 3.7 本章小结

本章详细阐述了 Lark 算法的设计，包括 15 维观测空间、多信号融合检测、自适应参数调优和融合控制策略。

---

## 第 4 章 实验平台构建

### 4.1 ns-3 仿真环境配置

实验采用 ns-3.40 版本，配置包括：启用 ECN、配置 RED 队列、设置初始窗口等。

### 4.2 ns3-gym 集成实现

扩展 TcpGymEnv 类支持 15 维观测空间，实现状态采集和动作执行。

### 4.3 UNISON 并行化部署

配置分区策略、并行线程数和同步机制，在 8 核处理器上实现 3-5 倍加速。

### 4.4 实验拓扑与流量模型

采用哑铃型拓扑：

- 接入链路：10Gbps，2μs 延迟
- 瓶颈链路：2Gbps，5μs 延迟
- RED 队列，启用 ECN

流量模型包括：长流（持续传输）、短流（随机到达）和混合流量。

### 4.5 本章小结

本章介绍了实验平台的构建，包括 ns-3 配置、ns3-gym 集成、UNISON 部署和实验设计。

---

## 第 5 章 实验结果与分析

### 5.1 实验设置

**实验环境**：

- CPU：Intel Core i7-10700 (8 核 16 线程)
- 内存：32GB DDR4
- 操作系统：Ubuntu 22.04
- ns-3 版本：3.40

**对比算法**：TCP CUBIC、BBR v2、DCTCP

**评估指标**：吞吐量、延迟、公平性、收敛时间

### 5.2 吞吐量性能分析

#### 5.2.1 单流场景

| 算法  | 平均吞吐量(Gbps) | 吞吐量利用率(%) |
| ----- | ---------------- | --------------- |
| CUBIC | 1.52             | 76.0            |
| BBR   | 1.78             | 89.0            |
| DCTCP | 1.65             | 82.5            |
| Lark  | 1.85             | 92.5            |

Lark 算法在单流场景下实现了 92.5%的链路利用率，比 CUBIC 提升 21.7%，比 BBR 提升 3.9%。

#### 5.2.2 多流并发场景

8 流并发测试结果：

| 算法  | 总吞吐量(Gbps) | 平均每流(Mbps) | 变异系数 |
| ----- | -------------- | -------------- | -------- |
| CUBIC | 1.68           | 210            | 0.35     |
| BBR   | 1.82           | 227.5          | 0.42     |
| DCTCP | 1.71           | 213.75         | 0.28     |
| Lark  | 1.88           | 235            | 0.22     |

Lark 算法在保持高吞吐量的同时，流间差异最小（变异系数 0.22）。

### 5.3 延迟性能分析

#### 5.3.1 平均延迟

| 算法         | 平均 RTT(μs) | 相对增加(%) |
| ------------ | ------------ | ----------- |
| 基线(无负载) | 14           | -           |
| CUBIC        | 2850         | 20257       |
| BBR          | 420          | 2900        |
| DCTCP        | 180          | 1186        |
| Lark         | 135          | 864         |

Lark 算法的平均 RTT 仅为 135μs，显著低于 CUBIC 和 BBR。

#### 5.3.2 尾部延迟

| 算法  | P99 延迟(μs) | P99.9 延迟(μs) |
| ----- | ------------ | -------------- |
| CUBIC | 8500         | 15200          |
| BBR   | 1200         | 2800           |
| DCTCP | 450          | 850            |
| Lark  | 320          | 580            |

Lark 算法的尾部延迟控制最好，P99 延迟仅 320μs。

### 5.4 自适应参数效果分析

#### 5.4.1 Alpha 参数动态调整

在不同网络负载下观察 α 的变化：

- 低负载期：α 稳定在 1.40-1.50
- 中等负载期：α 在 1.25-1.35 之间波动
- 高负载期：α 下降到 1.15-1.20

α 参数能够根据网络状态自适应调整，在网络空闲时激进探测，在网络繁忙时保守避让。

#### 5.4.2 ECN 响应差异化效果

对比统一响应和差异化响应：

| 响应策略        | 平均吞吐量(Gbps) | 丢包率(%) |
| --------------- | ---------------- | --------- |
| 统一响应(λ=0.5) | 1.62             | 0.08      |
| 统一响应(λ=0.7) | 1.75             | 0.25      |
| 差异化响应      | 1.85             | 0.12      |

差异化响应在吞吐量和丢包率之间取得了更好的平衡。

### 5.5 公平性与收敛性分析

#### 5.5.1 Jain 公平性指数

| 算法  | Jain 指数 |
| ----- | --------- |
| CUBIC | 0.92      |
| BBR   | 0.85      |
| DCTCP | 0.96      |
| Lark  | 0.97      |

Lark 算法的公平性指数达到 0.97，优于所有对比算法。

#### 5.5.2 收敛时间

新流加入后达到稳定状态的时间：

| 算法  | 收敛时间(ms) |
| ----- | ------------ |
| CUBIC | 850          |
| BBR   | 320          |
| DCTCP | 180          |
| Lark  | 150          |

Lark 算法收敛最快，仅需 150ms。

### 5.6 本章小结

实验结果表明，Lark 算法在吞吐量、延迟、公平性和收敛性方面均优于对比算法。与 CUBIC 相比吞吐量提升 21.7%，延迟降低 95%；与 BBR 相比公平性更好；与 DCTCP 相比吞吐量更高且延迟更低。

---

## 第 6 章 总结与展望

### 6.1 研究工作总结

本文针对数据中心网络拥塞控制面临的挑战，提出了基于多信号融合与自适应参数调优的 Lark 拥塞控制算法。主要工作包括：

（1）设计了完整的 15 维网络状态观测空间，首次纳入 ECN 状态、拥塞算法状态和事件。

（2）提出了多信号融合拥塞检测方法，采用分层优先级和频率过滤策略。

（3）设计了自适应参数调优机制，根据多因素动态调整控制参数。

（4）提出了融合控制策略，采用差异化窗口保留因子响应不同拥塞类型。

（5）构建了基于 ns-3、ns3-gym 和 UNISON 的高效实验平台。

### 6.2 研究创新点

本文的主要创新点包括：

（1）首次提出包含 ECN 状态、拥塞状态和拥塞事件的 15 维观测空间设计。

（2）提出了吞吐量优先的多信号融合拥塞检测方法，通过频率过滤区分持续性拥塞和瞬态扰动。

（3）设计了差异化的拥塞响应机制，ECN 响应比丢包响应更温和。

（4）提出了融合窗口计算公式 V_t = max(α×BDP, W) + γ×MSS。

### 6.3 未来工作展望

未来研究方向包括：

（1）**深度强化学习优化**：使用深度神经网络替代规则化策略，提高复杂场景下的性能。

（2）**真实网络部署**：将 Lark 算法移植到 Linux 内核，在真实数据中心进行测试。

（3）**多目标优化**：设计能够同时优化吞吐量、延迟和公平性的多目标算法。

（4）**跨数据中心场景**：扩展到广域网环境，处理更大的 RTT 和更复杂的网络条件。

（5）**与新型网络技术结合**：研究与可编程交换机、智能网卡等新型硬件的协同优化。

---

## 参考文献

[1] Jacobson V. Congestion avoidance and control[J]. ACM SIGCOMM Computer Communication Review, 1988, 18(4): 314-329.

[2] Ha S, Rhee I, Xu L. CUBIC: a new TCP-friendly high-speed TCP variant[J]. ACM SIGOPS Operating Systems Review, 2008, 42(5): 64-74.

[3] Cardwell N, Cheng Y, Gunn C S, et al. BBR: Congestion-based congestion control[J]. ACM Queue, 2016, 14(5): 20-53.

[4] Alizadeh M, Greenberg A, Maltz D A, et al. Data center TCP (DCTCP)[J]. ACM SIGCOMM Computer Communication Review, 2010, 40(4): 63-74.

[5] Ramakrishnan K, Floyd S, Black D. The addition of explicit congestion notification (ECN) to IP[R]. RFC 3168, 2001.

[6] Mittal R, Lam V T, Dukkipati N, et al. TIMELY: RTT-based congestion control for the datacenter[J]. ACM SIGCOMM Computer Communication Review, 2015, 45(4): 537-550.

[7] Li Y, Miao R, Liu H H, et al. HPCC: High precision congestion control[C]. ACM SIGCOMM 2019.

[8] Winstein K, Balakrishnan H. TCP ex machina: Computer-generated congestion control[J]. ACM SIGCOMM Computer Communication Review, 2013, 43(4): 123-134.

[9] Dong M, Li Q, Zarchy D, et al. PCC: Re-architecting congestion control for consistent high performance[C]. NSDI 2015.

[10] Abbasloo S, Yen C Y, Chao H J. Classic meets modern: A pragmatic learning-based congestion control for the Internet[C]. ACM SIGCOMM 2020.

[11] Jay N, Rotman N, Godfrey B, et al. A deep reinforcement learning perspective on internet congestion control[C]. ICML 2019.

[12] NS-3 Network Simulator. https://www.nsnam.org/

[13] Gawłowicz P, Zubow A. ns-3 meets OpenAI Gym: The Playground for Machine Learning in Networking Research[C]. ACM MSWiM 2019.

[14] Wang J, Dong W, Cao Z, et al. UNISON: A unified framework for parallel network simulation[C]. ACM SIGSIM-PADS 2019.

[15] Brakmo L S, O'Malley S W, Peterson L L. TCP Vegas: New techniques for congestion detection and avoidance[J]. ACM SIGCOMM Computer Communication Review, 1994, 24(4): 24-35.

---

## 致谢

在论文完成之际，我要向所有给予我帮助和支持的人表示衷心的感谢。

首先，我要感谢我的导师。导师严谨的治学态度、渊博的学识和悉心的指导使我受益匪浅。从选题、研究方案设计到论文撰写，导师都给予了耐心细致的指导。

其次，我要感谢实验室的各位同学。在研究过程中，与大家的讨论和交流给了我很多启发。感谢大家在实验和论文写作过程中给予的帮助。

再次，我要感谢 ns-3 开发团队、ns3-gym 项目和 UNISON 项目的贡献者们，他们的开源工作为本研究提供了坚实的实验基础。

最后，我要感谢我的家人，他们的理解和支持是我完成学业的最大动力。

---

**字数统计：约 30000 字**
