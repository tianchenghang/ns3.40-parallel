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
#include "ns3/tcp-bbr.h"
#include "ns3/tcp-socket-factory.h"
#include "ns3/traffic-control-module.h"

#include <fstream>
#include <iomanip>
#include <sstream>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("MultiFlowEcnSimulator");

// ============================================================================
// 实验目标：N-to-1 聚合场景下的 ECN 标记与公平性研究
// 拓扑：
//   sender_i (N 个) --accessBw/accessDelay-- router -- bottleneckBw/delay --
//   receiver
// 所有 N 个发送端使用同一协议（默认为 DCTCP），所有流经过同一瓶颈
// 瓶颈安装 RED+ECN。主要观察：
//   * 每条流的吞吐是否公平
//   * RED 标记是否均匀分布
//   * 队列长度在多流下是否更抖动
// 可以通过 --tcpType=dctcp|cubic|bbr 切换协议，复用同一拓扑。
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

static void ConnectSocketCwnd(uint32_t nodeId,
                              Ptr<OutputStreamWrapper> cwndStream) {
  std::ostringstream path;
  path << "/NodeList/" << nodeId
       << "/$ns3::TcpL4Protocol/SocketList/0/CongestionWindow";
  Config::ConnectWithoutContext(path.str(),
                                MakeBoundCallback(&CwndTracer, cwndStream));
}

int main(int argc, char *argv[]) {
  uint32_t nFlows = 4;
  std::string tcpType = "dctcp"; // dctcp | cubic | bbr
  std::string bottleneckBw = "100Mbps";
  std::string bottleneckDelay = "1ms";
  std::string accessBw = "1Gbps";
  std::string accessDelay = "1ms";
  uint32_t queueSizePkts = 200;
  uint32_t redMinTh = 40;
  uint32_t redMaxTh = 120;
  bool useEcn = true;
  double simTime = 20.0;

  CommandLine cmd;
  cmd.AddValue("nFlows", "Number of aggregated flows", nFlows);
  cmd.AddValue("tcpType", "TCP variant: dctcp|cubic|bbr", tcpType);
  cmd.AddValue("bottleneckBw", "Bottleneck bandwidth", bottleneckBw);
  cmd.AddValue("bottleneckDelay", "Bottleneck delay", bottleneckDelay);
  cmd.AddValue("queueSizePkts", "Bottleneck queue size (packets)",
               queueSizePkts);
  cmd.AddValue("redMinTh", "RED MinTh", redMinTh);
  cmd.AddValue("redMaxTh", "RED MaxTh", redMaxTh);
  cmd.AddValue("useEcn", "Enable ECN marking on RED + TCP", useEcn);
  cmd.AddValue("simTime", "Simulation time (s)", simTime);
  cmd.Parse(argc, argv);

  //! 选择 TCP 变体
  TypeId tid;
  if (tcpType == "dctcp") {
    tid = TcpDctcp::GetTypeId();
  } else if (tcpType == "cubic") {
    tid = TcpCubic::GetTypeId();
  } else if (tcpType == "bbr") {
    tid = TcpBbr::GetTypeId();
    Config::SetDefault("ns3::TcpSocketState::EnablePacing", BooleanValue(true));
  } else {
    NS_FATAL_ERROR("Unsupported tcpType: " << tcpType);
  }
  Config::SetDefault("ns3::TcpL4Protocol::SocketType", TypeIdValue(tid));

  Config::SetDefault("ns3::TcpSocketBase::UseEcn",
                     StringValue(useEcn ? "On" : "Off"));

  Config::SetDefault("ns3::RedQueueDisc::UseEcn", BooleanValue(useEcn));
  Config::SetDefault("ns3::RedQueueDisc::UseHardDrop", BooleanValue(false));
  Config::SetDefault("ns3::RedQueueDisc::MeanPktSize", UintegerValue(1500));
  Config::SetDefault("ns3::RedQueueDisc::QW", DoubleValue(1.0));
  Config::SetDefault("ns3::RedQueueDisc::MinTh", DoubleValue(redMinTh));
  Config::SetDefault("ns3::RedQueueDisc::MaxTh", DoubleValue(redMaxTh));
  Config::SetDefault(
      "ns3::RedQueueDisc::MaxSize",
      QueueSizeValue(QueueSize(QueueSizeUnit::PACKETS, queueSizePkts)));

  Config::SetDefault("ns3::TcpSocket::SndBufSize", UintegerValue(1 << 22));
  Config::SetDefault("ns3::TcpSocket::RcvBufSize", UintegerValue(1 << 22));
  Config::SetDefault("ns3::TcpSocket::SegmentSize", UintegerValue(1448));

  Time::SetResolution(Time::NS);
  LogComponentEnable("MultiFlowEcnSimulator", LOG_LEVEL_INFO);

  //! 节点
  NodeContainer senders;
  senders.Create(nFlows);
  Ptr<Node> router = CreateObject<Node>();
  Ptr<Node> receiver = CreateObject<Node>();

  InternetStackHelper stack;
  stack.Install(senders);
  stack.Install(router);
  stack.Install(receiver);

  //! 接入链路
  PointToPointHelper p2pAccess;
  p2pAccess.SetDeviceAttribute("DataRate", StringValue(accessBw));
  p2pAccess.SetChannelAttribute("Delay", StringValue(accessDelay));

  //! 瓶颈链路
  PointToPointHelper p2pBottleneck;
  p2pBottleneck.SetDeviceAttribute("DataRate", StringValue(bottleneckBw));
  p2pBottleneck.SetChannelAttribute("Delay", StringValue(bottleneckDelay));

  //! access 链路用 PfifoFast
  TrafficControlHelper tchAccess;
  tchAccess.SetRootQueueDisc("ns3::PfifoFastQueueDisc");

  std::vector<NetDeviceContainer> accessDevs(nFlows);
  std::vector<Ipv4InterfaceContainer> accessIfs(nFlows);
  Ipv4AddressHelper address;
  for (uint32_t i = 0; i < nFlows; ++i) {
    accessDevs[i] = p2pAccess.Install(senders.Get(i), router);
    tchAccess.Uninstall(accessDevs[i]);
    tchAccess.Install(accessDevs[i]);

    std::ostringstream base;
    base << "10.1." << (i + 1) << ".0";
    address.SetBase(base.str().c_str(), "255.255.255.0");
    accessIfs[i] = address.Assign(accessDevs[i]);
  }

  NetDeviceContainer bottleneckDevs = p2pBottleneck.Install(router, receiver);

  TrafficControlHelper tchBottleneck;
  tchBottleneck.SetRootQueueDisc(
      "ns3::RedQueueDisc", "LinkBandwidth", StringValue(bottleneckBw),
      "LinkDelay", StringValue(bottleneckDelay), "MinTh", DoubleValue(redMinTh),
      "MaxTh", DoubleValue(redMaxTh), "UseEcn", BooleanValue(useEcn));
  tchBottleneck.Uninstall(bottleneckDevs);
  QueueDiscContainer qdBottleneck = tchBottleneck.Install(bottleneckDevs);

  address.SetBase("10.1.100.0", "255.255.255.0");
  Ipv4InterfaceContainer bottleneckIfs = address.Assign(bottleneckDevs);

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  //! receiver 上一个 sink 接所有流
  uint16_t port = 9000;
  PacketSinkHelper sinkHelper("ns3::TcpSocketFactory",
                              InetSocketAddress(Ipv4Address::GetAny(), port));
  ApplicationContainer sinkApp = sinkHelper.Install(receiver);
  Ptr<PacketSink> sink = StaticCast<PacketSink>(sinkApp.Get(0));
  sinkApp.Start(Seconds(0.0));
  sinkApp.Stop(Seconds(simTime + 1.0));

  //! N 个 BulkSend 发送端，错开 10ms 启动避免完全同步
  ApplicationContainer sourceApps;
  for (uint32_t i = 0; i < nFlows; ++i) {
    BulkSendHelper source("ns3::TcpSocketFactory",
                          InetSocketAddress(bottleneckIfs.GetAddress(1), port));
    source.SetAttribute("MaxBytes", UintegerValue(0));
    ApplicationContainer app = source.Install(senders.Get(i));
    app.Start(Seconds(1.0 + i * 0.01));
    app.Stop(Seconds(simTime));
    sourceApps.Add(app);
  }

  //! trace
  AsciiTraceHelper asciiHelper;
  auto qlenStream = asciiHelper.CreateFileStream("qlen.log");
  Ptr<QueueDisc> redQd = qdBottleneck.Get(0);
  redQd->TraceConnectWithoutContext(
      "PacketsInQueue", MakeBoundCallback(&QueueLengthTracer, qlenStream));

  //! 每个发送端一个独立 cwnd 文件
  for (uint32_t i = 0; i < nFlows; ++i) {
    std::ostringstream fn;
    fn << "cwnd-sender" << i << ".log";
    auto cwndStream = asciiHelper.CreateFileStream(fn.str());
    Simulator::Schedule(Seconds(1.0 + i * 0.01 + 0.001), &ConnectSocketCwnd,
                        senders.Get(i)->GetId(), cwndStream);
  }

  FlowMonitorHelper flowMon;
  Ptr<FlowMonitor> monitor = flowMon.InstallAll();

  Simulator::Stop(Seconds(simTime + 2.0));
  Simulator::Run();

  //! RED 统计
  QueueDisc::Stats st = redQd->GetStats();
  std::ofstream redStats("red-stats.log");
  redStats << "# N-to-1 aggregation, tcp=" << tcpType << " useEcn=" << useEcn
           << " nFlows=" << nFlows << "\n";
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

  //! 公平性：Jain's index
  monitor->CheckForLostPackets();
  auto classifier = DynamicCast<Ipv4FlowClassifier>(flowMon.GetClassifier());
  double sumThr = 0.0;
  double sumThr2 = 0.0;
  uint32_t n = 0;
  for (auto &it : monitor->GetFlowStats()) {
    auto t = classifier->FindFlow(it.first);
    double duration = it.second.timeLastRxPacket.GetSeconds() -
                      it.second.timeFirstTxPacket.GetSeconds();
    double throughputMbps =
        duration > 0 ? it.second.rxBytes * 8.0 / duration / 1e6 : 0.0;
    if (t.protocol == 6 /* TCP */) {
      sumThr += throughputMbps;
      sumThr2 += throughputMbps * throughputMbps;
      ++n;
    }
    NS_LOG_UNCOND("Flow " << it.first << " " << t.sourceAddress << " -> "
                          << t.destinationAddress << " proto="
                          << (int)t.protocol << " tx=" << it.second.txPackets
                          << " rx=" << it.second.rxPackets
                          << " lost=" << it.second.lostPackets
                          << " throughput=" << std::fixed
                          << std::setprecision(2) << throughputMbps << " Mbps");
  }
  if (n > 0 && sumThr2 > 0) {
    double jain = (sumThr * sumThr) / (n * sumThr2);
    NS_LOG_UNCOND("Jain's fairness index over " << n
                                                << " TCP flows = " << jain);
  }

  NS_LOG_UNCOND("Total rx bytes: " << sink->GetTotalRx());

  Simulator::Destroy();
  return 0;
}
