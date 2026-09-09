// Copyright 2026 hangtiancheng
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/flow-monitor-helper.h"
#include "ns3/flow-monitor-module.h"
#include "ns3/internet-module.h"
#include "ns3/ipv4-flow-classifier.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/tcp-socket-factory.h"
#include "ns3/traffic-control-module.h"

#include <fstream>
#include <iomanip>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("DctcpEcnSimulator");

// ============================================================================
// 实验目标：DCTCP + RED/ECN 主基线
// 拓扑：sender(n0) --1Gbps/1ms-- router(n1) --100Mbps/1ms-- receiver(n2)
// 瓶颈 RTT ≈ 4ms（接近数据中心场景），更能体现 DCTCP 的 ECN 反应。
// ECN 相关观测：
//   * 瓶颈队列长度 qlen.log
//   * RED UNFORCED_MARK / FORCED_MARK / UNFORCED_DROP 计数 red-stats.log
//   * 发送端 cwnd.log / rtt.log / ecn-state.log
// ============================================================================

static void QueueLengthTracer(Ptr<OutputStreamWrapper> stream, uint32_t oldVal,
                              uint32_t newVal) {
  *stream->GetStream() << Simulator::Now().GetSeconds() << " " << newVal
                       << std::endl;
}

static void CwndTracer(Ptr<OutputStreamWrapper> stream, uint32_t oldCwnd,
                       uint32_t newCwnd) {
  *stream->GetStream() << Simulator::Now().GetSeconds() << " " << newCwnd
                       << std::endl;
}

static void RttTracer(Ptr<OutputStreamWrapper> stream, Time oldRtt,
                      Time newRtt) {
  *stream->GetStream() << Simulator::Now().GetSeconds() << " "
                       << newRtt.GetMicroSeconds() << std::endl;
}

static void EcnStateTracer(Ptr<OutputStreamWrapper> stream,
                           TcpSocketState::EcnState_t oldState,
                           TcpSocketState::EcnState_t newState) {
  *stream->GetStream() << Simulator::Now().GetSeconds() << " "
                       << static_cast<int>(newState) << std::endl;
}

static void ConnectSocketTraces(Ptr<OutputStreamWrapper> cwndStream,
                                Ptr<OutputStreamWrapper> rttStream,
                                Ptr<OutputStreamWrapper> ecnStream) {
  Config::ConnectWithoutContext(
      "/NodeList/0/$ns3::TcpL4Protocol/SocketList/0/CongestionWindow",
      MakeBoundCallback(&CwndTracer, cwndStream));
  Config::ConnectWithoutContext(
      "/NodeList/0/$ns3::TcpL4Protocol/SocketList/0/RTT",
      MakeBoundCallback(&RttTracer, rttStream));
  Config::ConnectWithoutContext(
      "/NodeList/0/$ns3::TcpL4Protocol/SocketList/0/EcnState",
      MakeBoundCallback(&EcnStateTracer, ecnStream));
}

int main(int argc, char *argv[]) {
  //! 命令行可调参数（便于批量跑 ECN 实验）
  std::string bottleneckBw = "100Mbps";
  std::string bottleneckDelay = "1ms";
  std::string accessBw = "1Gbps";
  std::string accessDelay = "1ms";
  uint32_t queueSizePkts = 100; // 浅缓冲，典型 DCTCP 场景
  uint32_t redMinTh = 20;       // 标记下阈值
  uint32_t redMaxTh = 60;       // 标记上阈值
  double simTime = 20.0;

  CommandLine cmd;
  cmd.AddValue("bottleneckBw", "Bottleneck bandwidth", bottleneckBw);
  cmd.AddValue("bottleneckDelay", "Bottleneck delay", bottleneckDelay);
  cmd.AddValue("queueSizePkts", "Bottleneck queue size (packets)",
               queueSizePkts);
  cmd.AddValue("redMinTh", "RED MinTh", redMinTh);
  cmd.AddValue("redMaxTh", "RED MaxTh", redMaxTh);
  cmd.AddValue("simTime", "Simulation time (s)", simTime);
  cmd.Parse(argc, argv);

  //! 使用 DCTCP
  Config::SetDefault("ns3::TcpL4Protocol::SocketType",
                     TypeIdValue(TcpDctcp::GetTypeId()));

  //! 开启 TCP ECN（必需）
  Config::SetDefault("ns3::TcpSocketBase::UseEcn", StringValue("On"));

  //! RED 全局配置
  Config::SetDefault("ns3::RedQueueDisc::UseEcn", BooleanValue(true));
  Config::SetDefault("ns3::RedQueueDisc::UseHardDrop", BooleanValue(false));
  Config::SetDefault("ns3::RedQueueDisc::MeanPktSize", UintegerValue(1500));
  Config::SetDefault("ns3::RedQueueDisc::QW", DoubleValue(1.0));
  Config::SetDefault("ns3::RedQueueDisc::MinTh", DoubleValue(redMinTh));
  Config::SetDefault("ns3::RedQueueDisc::MaxTh", DoubleValue(redMaxTh));
  Config::SetDefault(
      "ns3::RedQueueDisc::MaxSize",
      QueueSizeValue(QueueSize(QueueSizeUnit::PACKETS, queueSizePkts)));

  //! TCP Buffer
  Config::SetDefault("ns3::TcpSocket::SndBufSize", UintegerValue(1 << 22));
  Config::SetDefault("ns3::TcpSocket::RcvBufSize", UintegerValue(1 << 22));
  Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(1448));

  Time::SetResolution(Time::NS);
  LogComponentEnable("DctcpEcnSimulator", LOG_LEVEL_INFO);

  //! 节点
  NodeContainer sender, router, receiver;
  sender.Create(1);
  router.Create(1);
  receiver.Create(1);

  InternetStackHelper stack;
  stack.InstallAll();

  //! 接入链路（非瓶颈）
  PointToPointHelper p2pAccess;
  p2pAccess.SetDeviceAttribute("DataRate", StringValue(accessBw));
  p2pAccess.SetChannelAttribute("Delay", StringValue(accessDelay));

  //! 瓶颈链路
  PointToPointHelper p2pBottleneck;
  p2pBottleneck.SetDeviceAttribute("DataRate", StringValue(bottleneckBw));
  p2pBottleneck.SetChannelAttribute("Delay", StringValue(bottleneckDelay));

  NetDeviceContainer devLeft = p2pAccess.Install(sender.Get(0), router.Get(0));
  NetDeviceContainer devRight =
      p2pBottleneck.Install(router.Get(0), receiver.Get(0));

  //! 关键修复：必须显式 SetRootQueueDisc，否则默认会退化为 FqCoDel，
  //! 而不是我们想研究的 RED+ECN。瓶颈一侧启用 ECN 标记。
  //! 左侧接入链路换成 PfifoFast，避免 FqCoDel 干扰 ECN 研究。
  TrafficControlHelper tchAccess;
  tchAccess.SetRootQueueDisc("ns3::PfifoFastQueueDisc");
  tchAccess.Uninstall(devLeft);
  tchAccess.Install(devLeft);

  TrafficControlHelper tchBottleneck;
  tchBottleneck.SetRootQueueDisc(
      "ns3::RedQueueDisc", "LinkBandwidth", StringValue(bottleneckBw),
      "LinkDelay", StringValue(bottleneckDelay), "MinTh", DoubleValue(redMinTh),
      "MaxTh", DoubleValue(redMaxTh), "UseEcn", BooleanValue(true));
  tchBottleneck.Uninstall(devRight);
  QueueDiscContainer qdBottleneck = tchBottleneck.Install(devRight);

  //! 分配 IP
  Ipv4AddressHelper address;
  address.SetBase("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer ifLeft = address.Assign(devLeft);
  address.SetBase("10.1.2.0", "255.255.255.0");
  Ipv4InterfaceContainer ifRight = address.Assign(devRight);

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  //! 接收端
  uint16_t port = 9;
  PacketSinkHelper sinkHelper("ns3::TcpSocketFactory",
                              InetSocketAddress(Ipv4Address::GetAny(), port));
  ApplicationContainer sinkApp = sinkHelper.Install(receiver.Get(0));
  Ptr<PacketSink> sink = StaticCast<PacketSink>(sinkApp.Get(0));
  sinkApp.Start(Seconds(0.0));
  sinkApp.Stop(Seconds(simTime + 1.0));

  //! 发送端：长连接 BulkSend，避免 OnOff 应用层节流导致 cwnd 不能反映瓶颈
  BulkSendHelper source("ns3::TcpSocketFactory",
                        InetSocketAddress(ifRight.GetAddress(1), port));
  source.SetAttribute("MaxBytes", UintegerValue(0));
  ApplicationContainer sourceApp = source.Install(sender.Get(0));
  sourceApp.Start(Seconds(1.0));
  sourceApp.Stop(Seconds(simTime));

  //! ECN 相关 trace
  AsciiTraceHelper asciiHelper;
  auto cwndStream = asciiHelper.CreateFileStream("cwnd.log");
  auto rttStream = asciiHelper.CreateFileStream("rtt.log");
  auto ecnStream = asciiHelper.CreateFileStream("ecn-state.log");
  auto qlenStream = asciiHelper.CreateFileStream("qlen.log");

  //! 等 socket 创建后再连 trace
  Simulator::Schedule(Seconds(1.001), &ConnectSocketTraces, cwndStream,
                      rttStream, ecnStream);

  //! 瓶颈队列长度
  Ptr<QueueDisc> redQd = qdBottleneck.Get(0);
  redQd->TraceConnectWithoutContext(
      "PacketsInQueue", MakeBoundCallback(&QueueLengthTracer, qlenStream));

  //! FlowMonitor
  FlowMonitorHelper flowMon;
  Ptr<FlowMonitor> monitor = flowMon.InstallAll();

  Simulator::Stop(Seconds(simTime + 2.0));
  Simulator::Run();

  //! 输出 RED ECN 相关统计
  QueueDisc::Stats st = redQd->GetStats();
  std::ofstream redStats("red-stats.log");
  redStats << "# RED queue stats on bottleneck\n";
  redStats << "TotalEnqueuedPackets " << st.nTotalEnqueuedPackets << "\n";
  redStats << "TotalDequeuedPackets " << st.nTotalDequeuedPackets << "\n";
  redStats << "TotalDroppedPackets  " << st.nTotalDroppedPackets << "\n";
  redStats << "TotalMarkedPackets   " << st.nTotalMarkedPackets << "\n";
  redStats << "UnforcedMark         "
           << st.GetNMarkedPackets(RedQueueDisc::UNFORCED_MARK) << "\n";
  redStats << "ForcedMark           "
           << st.GetNMarkedPackets(RedQueueDisc::FORCED_MARK) << "\n";
  redStats << "UnforcedDrop         "
           << st.GetNDroppedPackets(RedQueueDisc::UNFORCED_DROP) << "\n";
  redStats << "ForcedDrop           "
           << st.GetNDroppedPackets(RedQueueDisc::FORCED_DROP) << "\n";

  //! FlowMonitor
  monitor->CheckForLostPackets();
  auto classifier = DynamicCast<Ipv4FlowClassifier>(flowMon.GetClassifier());
  for (auto &it : monitor->GetFlowStats()) {
    auto t = classifier->FindFlow(it.first);
    double duration = it.second.timeLastRxPacket.GetSeconds() -
                      it.second.timeFirstTxPacket.GetSeconds();
    double throughputMbps =
        duration > 0 ? it.second.rxBytes * 8.0 / duration / 1e6 : 0.0;
    NS_LOG_UNCOND("Flow " << it.first << " " << t.sourceAddress << " -> "
                          << t.destinationAddress
                          << " tx=" << it.second.txPackets
                          << " rx=" << it.second.rxPackets
                          << " lost=" << it.second.lostPackets
                          << " throughput=" << std::fixed
                          << std::setprecision(2) << throughputMbps << " Mbps");
  }
  NS_LOG_UNCOND("Total rx bytes: " << sink->GetTotalRx());

  Simulator::Destroy();
  return 0;
}
