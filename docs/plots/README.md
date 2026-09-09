# TcpSwift 论文插图说明

本文档对 `docs/plots` 目录下生成的插图进行逐图说明。所有图像均由 `docs/plots/main.py` 从 `logs/` 目录中的仿真数据（FlowMonitor 原始产物）自动生成，可用于会议论文、发明专利和研究生毕业论文中的实验分析、方法说明和系统机制展示。

## 图像生成与数据来源

绘图脚本会遍历 `logs/` 下的全部 FlowMonitor 文件并解析：

- `logs/comparison/*.flowmonitor`：纯 TCP 设置（`enable_udp_burst=false`）。
- `logs/comparison-udp/*.flowmonitor`：UDP Burst 设置（突发平均负载 = 瓶颈速率 32%、峰值 64%、50% 占空比、1024 B 报文）。
- 全部指标仅在**前向数据流**（10.1.x → 10.2.x）上定义；导出结果写入 `logs/summary/kpi_forward.csv`（288 条记录），并断言与归档版本一致。
- 详细展开场景为表 S1--S19（共 19 个纯 TCP 场景；其中 15 个具有 UDP 配对场景），与论文/学位论文中的场景编号一致；其余 17 个补充场景保留在 `kpi_forward.csv` 中供检索。

当前批量生成 6 组图像（`fig01_goodput_clean`、`fig02_delay_clean`、`fig03_tradeoff_clean`、`fig04_udp_burst_clean`、`fig06_architecture_zh`、`fig07_workflow_zh`），每组同时提供 `.png`、`.pdf` 和 `.svg` 三种格式：`.png` 适合 Word 和 Markdown 预览，`.pdf` 适合 LaTeX 排版，`.svg` 适合后续矢量编辑。

## 批量更新方法

在仓库根目录执行：

```bash
python3 docs/plots/main.py
```

执行后脚本会重新读取 `logs/`，重算 `logs/summary/kpi_forward.csv`，更新全部 `fig*.png/pdf/svg`，并刷新 `docs/plots/figure_manifest.json`。`logs/plots/` 与 `logs/plots-udp/` 下的批量对比图（吞吐/时延/丢包/雷达图等）由根目录的 `python3 main.py draw` 生成，每次数据更新后应一并重跑。

## fig01_goodput_clean —— 代表性场景聚合吞吐量

19 个代表性场景（S1--S19）纯 TCP 设置的聚合前向吞吐量，对数纵轴同时呈现百兆至万兆以上链路。图中 Swift 在全部场景取得最高柱体；相对最强基线增益约 +2%~+6%（均值约 +4.1%）。用于论文/学位论文实验章节的吞吐总览。

## fig02_delay_clean —— 平均单向时延与基线传播时延

19 个代表性场景的平均单向前向时延（对数坐标），黑色短划线为基线传播时延（BaseOWD = 2 × 接入时延 + 瓶颈时延）。在 RED/ECN 配置下四协议时延同量级、均贴近基线上方；柱顶与短划线的距离为排队分量。

## fig03_tradeoff_clean —— 利用率-时延权衡

纯 TCP 设置 19 个场景的瓶颈利用率—平均单向时延散点（时延对数坐标）。用于回应"吞吐提升是否以时延/丢包为代价"的疑问。

## fig04_udp_burst_clean —— 跨流量鲁棒性

15 个配对场景在 UDP Burst（平均 32% / 峰值 64% 瓶颈速率、50% 占空比）下相对纯 TCP 设置的吞吐量变化（上）与新增丢包（下，符号对数坐标）。在 RED/ECN 对称配置下四协议回落幅度接近（约 -27%~-38%），无协议塌缩；Swift 的绝对吞吐量在全部配对场景保持领先。

## fig06_architecture_zh —— 系统架构（方法/系统框图）

Swift 控制回路总体架构：协议栈五类回调采集 11 维有效状态（+4 项元数据），经跨进程同步信道送入决策模块，依次执行拥塞三分类判定、两级 BDP 估计与基线相对反馈自适应，输出 [ssThresh, cWnd] 决策并写回协议栈。图中不出现具体算法品牌名，可改写后用于发明专利的系统实施例框图。

## fig07_workflow_zh —— 方法流程图

拥塞控制方法整体流程（状态获取 → 拥塞判定 → 参数自适应 → 目标窗口逼近 → 差异化缩减与安全保护 → 决策应用）。图中不出现具体算法品牌名与实验数值，直接用于发明专利的方法实施例与摘要附图。

## 术语约定与使用注意

- 上述方法图使用的术语为"状态采集—决策输出—性能反馈"的中性表达，不包含学习类表述：算法主体为确定性规则（启发式），性能反馈值仅驱动控制参数相对自身慢速基线的在线微调，不涉及训练或模型推理。
- 论文正文引用实验数值时，应以 `logs/summary/kpi_forward.csv` 中的记录为准（该文件与 `docs/plots/main.py` 的导出结果逐字节一致）。
- 专利正文不建议直接暴露具体实验数值与协议品牌名：可使用 `fig06_architecture_zh`、`fig07_workflow_zh` 说明技术方案；如需在专利材料中使用本组图像，应自行核对模块命名是否符合专利撰写要求。
- 若后续重新运行仿真并更新 `logs/`，应重新执行 `python3 docs/plots/main.py` 与 `python3 main.py draw` 以刷新全部图像。
- LaTeX 文档优先引用 `.pdf`；Word 文档优先插入 `.png`；需二次编辑时使用 `.svg`。
