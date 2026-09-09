# Prompts

```md
/pdf /skill-creator

阅读 `.github/skills/ns-3-tutorial.pdf`, 先转为 markdown `.github/skills/ns3.40/reference/ns-3-tutorial.md` , 再为我创建 `.github/skills/ns3.40` 的 Agent Skill, MUST 全面、详细的介绍 ns3 (版本 3.40), MUST 使用专业的英文
```

```md
/ns3

你是一位计算机网络拥塞控制专家

基于 ns3 仿真器

- 版本 3.40 `https://www.nsnam.org/releases/ns-3-40/`
- 代码仓库 `https://gitlab.com/nsnam/ns-3-dev/-/tree/ns-3.40?ref_type=tags`

结合 ns3-gym 强化学习 `https://github.com/tkn-tub/ns3-gym`

我提出了一个新的拥塞控制协议 TcpSwift, 对标 TcpCubic, TcpNewReno, TcpBBr
新的拥塞控制协议 TcpSwift 的代码 `contrib/opengym/examples/swift-tcp`
主要的参考论文 `Gemini.pdf`

实验结果 `logs`

制品

- 会议论文 `docs/thesis.tex`
- 发明专利 `docs/patent.md`
- 研究生毕业论文 `docs/NJUPT_Professional_Thesis_draft1`

你的工作:

研究 ns3 仿真器, 版本 3.40, ns3-gym 强化学习

- 理解我提出的新的拥塞控制协议的代码 `contrib/opengym/examples/swift-tcp`
- 查看全部实验结果 `logs`
- 阅读主要的参考论文 `Gemini.pdf` 和会议论文 `docs/thesis.tex`

## MUST 阅读的前置要求

1. 目前会议论文、研究生毕业论文、发明专利中的 motivation 动机错误, TcpSwift 不是专为数据中心网络设计, 而是:

- 远距离传输
- 终端设备的多模态: 手机、电脑、..., 考虑到终端设备的复杂性, 引入强化学习辅助拥塞控制
- 会议论文、研究生毕业论文、发明专利中, 全文不要提到专为数据中心网络设计

2. 核心创新点限制在 2~3 个

## 第一步: 更新会议论文

- 请 MUST 过滤 `logs` 中异常的数据, 并将异常的数据记录到 `logs/error.txt`
- 重点关注 TcpSwift 表现更优秀的实验组

优化会议论文的表述, 以方便投递到中国计算机学会 A 类会议

## 第二步: 更新研究生毕业论文

基于以上的研究和修改, 同步更新研究生毕业论文

- 请 MUST 过滤 `logs` 中异常的数据, 并将异常的数据记录到 `logs/error.txt`
- 重点关注 TcpSwift 表现更优秀的实验组

优化研究生毕业论文的表述, 以符合优秀研究生毕业论文要求

## 第三步: 更新发明专利

基于以上的研究和修改, 同步更新中国大陆发明专利

- 发明专利中不需要指出是 Swift 协议, 可以描述为: 提出的新的拥塞控制协议
- 发明专利中不需要透出具体的实验数据

优化发明专利的表述, 以符合优秀中国大陆发明专利要求
```

```md
/skill-creator

为我创建 `.github/update-ns3.40-docs` 的 Agent Skill, 使用专业的英文, 该 skill 目的是指导 Agent 如何按顺序更新制品:

- 会议论文 `docs/thesis.tex`
- 发明专利 `docs/patent.md`
- 研究生毕业论文 `docs/NJUPT_Professional_Thesis_draft1`
```

```md
/skill-creator

为我创建 `.github/skills/convert-ns3.40-docs` 的 Agent Skill, 使用专业的英文, 该 skill 目的是指导 Agent 如何按顺序将 latex/markdown/pdf 制品转换为 Microsoft Word 文件 (docx)

## 源文件

- 会议论文 LeTaX 版本 `docs/thesis.tex`, pdf 版本 `docs/thesis.pdf`
- 发明专利 markdown `docs/patent.md`
- 研究生毕业论文 pdf `docs/NJUPT_Professional_Thesis_draft1/NJUPT_Professional_Thesis_d1.pdf`

## 目标文件

- 会议论文 docx `docs/thesis.docx`, 严格参考模版 doc `docs/thesis_template.doc`
- 发明专利 docx `docs/南京-杭天铖-YYYY-MM-DD-计算机网络拥塞控制.docx`, 格式对齐中国大陆发明专利
- 研究生毕业论文 docx `docs/NJUPT_Professional_Thesis_draft1.docx`, 格式对齐原研究生毕业论文 pdf `docs/NJUPT_Professional_Thesis_draft1/NJUPT_Professional_Thesis_d1.pdf`

转换过程中可能使用到的 skill:

- pdf
- docx
```
