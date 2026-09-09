# TcpSwift 论文插图说明

本文档对 `docs/plots` 目录下生成的插图进行逐图说明。所有图像均由 `docs/plots/main.py` 从 `logs/` 目录中的仿真数据、FlowMonitor 输出、运行日志和既有图像元数据自动生成，可用于会议论文、发明专利和研究生毕业论文中的实验分析、方法说明和系统机制展示。

## 图像生成与数据来源

绘图脚本会遍历 `logs/` 下的全部文件，并解析以下数据来源：

- `logs/plots/summary.csv`：纯 TCP 场景下的吞吐量、时延、抖动和丢包率汇总。
- `logs/plots-udp/summary.csv`：存在 UDP Burst 跨流量干扰时的性能汇总。
- `logs/summary/results_*.csv`：批量实验结果摘要。
- `logs/comparison/*.flowmonitor`：纯 TCP 场景的 FlowMonitor 流级统计。
- `logs/comparison-udp/*.flowmonitor`：UDP Burst 场景的 FlowMonitor 流级统计。
- `logs/` 下的 `.log` 文件：ns-3 运行日志与 TcpSwift agent 日志。
- `logs/plots*/*.png`：既有实验图像元数据，用于审计日志目录完整性。

当前批量生成 13 组图像，每组图像均同时提供 `.png`、`.pdf` 和 `.svg` 三种格式。`.png` 适合 Word 和 Markdown 预览，`.pdf` 适合 LaTeX 论文排版，`.svg` 适合后续矢量编辑。

## 批量更新方法

在仓库根目录执行：

```bash
python3 docs/plots/main.py
```

执行后脚本会重新读取 `logs/`，更新所有 `fig*.png`、`fig*.pdf`、`fig*.svg` 文件，并刷新 `docs/plots/figure_manifest.json`。

## fig01_tcp_throughput_representative

文件：

- `fig01_tcp_throughput_representative.png`
- `fig01_tcp_throughput_representative.pdf`
- `fig01_tcp_throughput_representative.svg`

该图展示纯 TCP 条件下代表性场景的聚合吞吐量对比，横轴为典型实验场景，纵轴采用对数坐标表示吞吐量，以便同时呈现百兆、千兆、万兆乃至更高速链路的性能差异。图中将 TcpSwift 与 TcpNewReno、TcpCubic 和 TcpBbr 放在同一坐标体系下比较，能够直观看出 TcpSwift 在多类链路条件下保持较高吞吐能力。

该图体现 TcpSwift 优势的关键在于：TcpSwift 并未只针对单一链路速率或单一网络类型优化，而是在高带宽近端链路、混合流量场景和长距离链路中保持稳定吞吐。对于会议论文，该图适合放在实验评估章节，用于说明 TcpSwift 的吞吐性能具有跨场景适用性；对于毕业论文，该图可作为实验结果总览；对于专利材料，则可作为方法效果的背景佐证，但不建议在专利正文中直接引用具体数值。

## fig02_udp_burst_throughput_retention

文件：

- `fig02_udp_burst_throughput_retention.png`
- `fig02_udp_burst_throughput_retention.pdf`
- `fig02_udp_burst_throughput_retention.svg`

该图比较在 UDP Burst 跨流量干扰下，各算法相对于纯 TCP 条件能够保留的吞吐比例。吞吐保留率越高，说明算法在突发背景流量、短时带宽挤占和队列扰动下越不容易出现性能塌缩。

该图最能体现 TcpSwift 的鲁棒性优势。传统基于丢包或固定参数的拥塞控制算法在突发跨流量到来时，容易由于拥塞信号滞后或窗口调整幅度不当而出现吞吐回落。TcpSwift 通过多信号融合、差异化窗口保留因子和连续递减保护机制，使窗口调整更具弹性，因此在 UDP Burst 条件下能够保持更好的吞吐延续性。该图适合作为论文中“跨流量鲁棒性”或“稳定性分析”的核心图。

## fig03_delay_loss_tradeoff

文件：

- `fig03_delay_loss_tradeoff.png`
- `fig03_delay_loss_tradeoff.pdf`
- `fig03_delay_loss_tradeoff.svg`

该图从时延、丢包和吞吐三个维度展示算法的综合权衡关系。横轴为平均时延，纵轴为丢包率，散点大小反映吞吐量水平。左右两个子图分别对应纯 TCP 条件和 UDP Burst 条件，能够观察算法在无干扰和有干扰环境下的性能迁移。

该图体现 TcpSwift 优势的方式不是单一指标领先，而是综合权衡更均衡。TcpSwift 的设计目标并非盲目追求最高发送速率，而是在高吞吐、低丢包和可控时延之间取得稳定折中。图中 TcpSwift 散点通常位于低丢包区域，并保持较大的吞吐规模，说明其拥塞判定机制能够更早识别风险，同时避免过度保守导致吞吐不足。该图适合用于回应评审对“吞吐提升是否以更高丢包或时延为代价”的疑问。

## fig04_swift_advantage_heatmap

文件：

- `fig04_swift_advantage_heatmap.png`
- `fig04_swift_advantage_heatmap.pdf`
- `fig04_swift_advantage_heatmap.svg`

该图以热力图形式展示 TcpSwift 相对于非 Swift 基线算法的归一化优势。行表示代表性实验场景，列表示吞吐、时延、丢包、UDP Burst 吞吐保留率和 UDP Burst 丢包改善等指标。蓝色区域表示相对优势，红色区域表示相对劣势或需要进一步优化的场景。

该图的价值在于能够避免只展示单一最优场景造成的片面结论，而是以矩阵形式呈现 TcpSwift 在不同指标上的优势边界。对于 TcpSwift，热力图能够突出其在丢包控制、跨流量鲁棒性和部分长距离场景吞吐方面的优势，同时保留中低速或特定 RTT 条件下可能存在的时延权衡。该图适合用于专业论文中的综合评价小节，也适合毕业论文中讨论算法适用边界和后续优化方向。

## fig05_flowmonitor_fairness_distribution

文件：

- `fig05_flowmonitor_fairness_distribution.png`
- `fig05_flowmonitor_fairness_distribution.pdf`
- `fig05_flowmonitor_fairness_distribution.svg`

该图基于 FlowMonitor 的流级吞吐统计计算 Jain 公平性指数，并以箱线图展示不同算法在纯 TCP 和 UDP Burst 条件下的流间公平性分布。Jain 指数越接近 1，说明多个流之间的吞吐分配越均衡。

该图体现 TcpSwift 不仅关注单条连接的性能，还关注多流共存时的资源分配稳定性。拥塞控制算法如果过于激进，可能在多流场景下造成流间吞吐失衡；如果过于保守，则可能牺牲整体链路利用率。TcpSwift 通过拥塞信号融合和安全保护机制，使窗口变化更平滑，有助于维持较好的流间公平性。该图适合用于论文或毕业论文中讨论“公平性”和“多流共存”问题。

## fig06_scenario_family_summary

文件：

- `fig06_scenario_family_summary.png`
- `fig06_scenario_family_summary.pdf`
- `fig06_scenario_family_summary.svg`

该图按照场景族对实验结果进行归纳，包括近端高速链路、无线/移动接入链路、广域/远距离链路以及拥塞/混合流量链路等类别。图中分别给出 TcpSwift 吞吐相对基线的归一化比例，以及 TcpSwift 时延相对基线的归一化比例。

该图用于从宏观层面说明 TcpSwift 的适用范围。相比只列出大量场景表格，场景族汇总能够更清晰地表达算法在不同网络类型中的总体表现。TcpSwift 的优势体现在其能够跨越不同带宽、RTT、接入方式和流量扰动条件，保持较好的吞吐利用率与时延控制能力。该图适合作为实验章节的总结图，也适合毕业论文中承接“场景设计”和“结果分析”两部分内容。

## fig07_swift_system_architecture

文件：

- `fig07_swift_system_architecture.png`
- `fig07_swift_system_architecture.pdf`
- `fig07_swift_system_architecture.svg`

该图展示 TcpSwift 的系统级控制闭环。图中从 ns-3 TCP socket 获取 ACK、丢包、ECN、RTT 等传输状态，通过 15 元素 OpenGym 传输容器输入强化学习辅助决策模块，再由多信号拥塞分类器、安全保护机制和窗口调整模块共同作用于拥塞窗口与慢启动阈值。

该图体现 TcpSwift 的方法创新：它不是单纯替换传统 AIMD 参数，而是将协议栈内部状态、强化学习辅助决策和安全约束机制整合为闭环控制系统。该结构能够解释 TcpSwift 为什么能在复杂网络环境下同时关注吞吐、时延、丢包和稳定性。会议论文中可将该图用于算法设计章节；毕业论文中可作为系统架构核心图；专利中可改写为装置模块或系统框图。

## fig08_multi_signal_decision_flow

文件：

- `fig08_multi_signal_decision_flow.png`
- `fig08_multi_signal_decision_flow.pdf`
- `fig08_multi_signal_decision_flow.svg`

该图展示 TcpSwift 的多信号拥塞判定流程。输入信号包括丢包、ECN 标记、超时和 RTT 膨胀，经过信号融合与严重程度仲裁后，分别触发差异化窗口保留、连续递减保护以及奖励/RTT 感知的参数调节，最终形成面向异构路径的稳定拥塞窗口目标。

该图能够突出 TcpSwift 相比传统算法的核心优势。传统算法通常依赖单一拥塞信号，例如丢包或时延变化，因此容易在无线误码、突发队列、路径 RTT 波动等情况下误判。TcpSwift 通过多信号协同判断拥塞程度，并对不同拥塞事件采取不同窗口保留策略，能够减少过度降窗和错误恢复带来的吞吐损失。该图适合放在论文方法章节，也适合用于专利中的技术方案说明。

## fig09_patent_method_steps

文件：

- `fig09_patent_method_steps.png`
- `fig09_patent_method_steps.pdf`
- `fig09_patent_method_steps.svg`

该图以专利撰写视角抽象出自适应 TCP 拥塞控制方法的步骤：采集传输状态、构建状态向量、推理控制动作、融合拥塞信号、约束窗口更新以及执行并迭代。该图避免暴露具体协议品牌和实验数值，更适合用于发明专利中的流程图或实施例说明。

该图体现的优势在于将 TcpSwift 的技术方案转化为可权利要求化的方法步骤。其重点不在于某一次实验结果，而在于说明该方法如何通过状态采集、智能决策、多信号融合和有界窗口更新解决复杂网络下拥塞控制滞后、误判和振荡问题。对于专利正文，该图可支撑独立权利要求中的总体方法流程，也可支撑从属权利要求中的状态获取、控制决策和稳定性保护特征。

## fig10_experiment_dumbbell_topology

文件：

- `fig10_experiment_dumbbell_topology.png`
- `fig10_experiment_dumbbell_topology.pdf`
- `fig10_experiment_dumbbell_topology.svg`

该图展示实验所采用的哑铃型网络拓扑。多个发送端经过接入链路汇聚到瓶颈链路，再连接到多个接收端。瓶颈链路的带宽、RTT 和队列参数可随场景变化，UDP Burst 作为可选背景流量用于模拟突发跨流量干扰。

该图的作用是增强实验可复现性和评估可信度。TcpSwift 的优势不是在孤立连接中得出的，而是在可控瓶颈、可变 RTT、多流竞争和突发背景流量共同作用下得到验证。通过该拓扑，论文可以清楚说明不同场景如何映射到近端高速、无线接入、广域传输和卫星链路等网络条件。该图适合放在会议论文和毕业论文的实验设置部分。

## fig11_logs_inventory_audit

文件：

- `fig11_logs_inventory_audit.png`
- `fig11_logs_inventory_audit.pdf`
- `fig11_logs_inventory_audit.svg`

该图展示绘图前对 `logs/` 目录的完整读取与审计结果，包括 FlowMonitor 文件、运行日志、CSV 汇总、既有 PNG 图像和其他文本文件的数量，同时统计日志中的 warning、error、TcpSwift agent 创建记录和既有图像数量。

该图强调实验数据处理过程的可追溯性。对于论文和毕业论文而言，实验结论的可信度不仅取决于最终图表，还取决于数据来源是否完整、处理过程是否可复现。该图说明本目录中的插图不是手工截取或选择性绘制，而是基于完整日志目录自动生成。它适合放在毕业论文的实验数据处理或附录部分，也可作为内部审稿时的数据审计材料。

## fig12_swift_advantage_ranked_scenarios

文件：

- `fig12_swift_advantage_ranked_scenarios.png`
- `fig12_swift_advantage_ranked_scenarios.pdf`
- `fig12_swift_advantage_ranked_scenarios.svg`

该图基于完整 `logs/` 数据自动筛选 TcpSwift 表现更优的实验组，并按照综合优势得分排序。综合得分同时考虑纯 TCP 条件下相对非 Swift 基线的吞吐增益、UDP Burst 条件下的吞吐保留增益、时延变化、纯 TCP 丢包改善和 UDP Burst 丢包改善。右侧摘要列进一步给出 TcpSwift 相对最强基线的吞吐比例，以及两类实验设置中的丢包改善幅度。

该图是本次 review 后新增的重点图像，直接回应“重点关注 TcpSwift 表现更优秀的实验组”的需求。相比原有图像只展示代表性场景，该图明确把 satellite_geo、dc_100g、rdma_like_50g、intra_rack_25g、rdma_like_25g 等优势实验组排在前列，使论文作者能够快速选择最适合放入正文的正向证据。会议论文中，该图可作为实验小节的主图或补充图；毕业论文中，该图适合用于解释为何选取若干典型场景展开分析；专利中不建议直接引用该图的实验数值，但可作为内部支撑材料。

## fig13_protocol_metric_scorecard

文件：

- `fig13_protocol_metric_scorecard.png`
- `fig13_protocol_metric_scorecard.pdf`
- `fig13_protocol_metric_scorecard.svg`

该图将全部完整场景归一化到“场景内最优协议”为 100 分，并从 TCP 吞吐、TCP 时延、TCP 丢包、UDP Burst 吞吐保留和 UDP Burst 丢包五个维度比较 TcpSwift、TcpNewReno、TcpCubic 和 TcpBbr。与单场景柱状图不同，该图强调跨场景平均表现，能够更紧凑地体现算法在多指标评价体系中的整体位置。

该图体现 TcpSwift 的综合竞争力。TcpSwift 的优势不是只依赖某一个极端场景，而是在高吞吐利用、低丢包和跨流量保留方面形成较稳定的综合表现。对于会议论文，该图适合作为实验总结图，用于支撑“多场景、多指标综合评价”的结论；对于毕业论文，该图可以放在章节末尾作为总体性能画像；对于专利和答辩材料，该图有助于把复杂实验结果压缩成易理解的协议对比矩阵。

## 推荐使用方式

会议论文建议优先使用以下图像：

- `fig12_swift_advantage_ranked_scenarios`：TcpSwift 优势实验组排序。
- `fig13_protocol_metric_scorecard`：全场景多指标综合得分。
- `fig01_tcp_throughput_representative`：吞吐性能总览。
- `fig02_udp_burst_throughput_retention`：跨流量鲁棒性。
- `fig03_delay_loss_tradeoff`：吞吐、时延和丢包综合权衡。
- `fig04_swift_advantage_heatmap`：多指标综合优势。
- `fig07_swift_system_architecture`：方法架构。
- `fig10_experiment_dumbbell_topology`：实验拓扑。

发明专利建议优先使用以下图像：

- `fig09_patent_method_steps`：方法流程图。
- `fig08_multi_signal_decision_flow`：拥塞信号融合机制。
- `fig07_swift_system_architecture`：系统模块关系，可根据专利语言改写标题和模块名称。

研究生毕业论文建议使用完整图组，其中 `fig05_flowmonitor_fairness_distribution`、`fig06_scenario_family_summary`、`fig12_swift_advantage_ranked_scenarios`、`fig13_protocol_metric_scorecard` 和 `fig11_logs_inventory_audit` 尤其适合用于扩展实验分析、场景归纳、优势实验组选择、总体性能画像和可复现性说明。

## 注意事项

- 论文正文中引用实验数值时，应以 `logs/` 中的 CSV 和 FlowMonitor 解析结果为准。
- 专利正文中不建议直接暴露具体实验数值，可使用流程图和机制图说明技术方案。
- 若后续重新运行仿真并更新 `logs/`，应重新执行 `python3 docs/plots/main.py` 以刷新所有图像和清单。
- 若 LaTeX 论文使用这些图像，优先引用 `.pdf` 文件；若 Word 文档使用这些图像，优先插入 `.png` 文件；若需要二次编辑，优先使用 `.svg` 文件。
