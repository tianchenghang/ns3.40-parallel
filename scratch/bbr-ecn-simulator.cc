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

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("BbrEcnSimulator");

// ============================================================================
// 实验目标：研究 BBR + RED/ECN 的交互。
// 与 dctcp-ecn-simulator.cc 用同一拓扑/RED 参数，方便横向比较：
//   * DCTCP: 对 ECN-echo 做加权 cwnd 缩减
//   * BBR:   不主动响应 ECE，这里观察 BBR 在 RED 标记/丢包下的表现
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

static void PacingTracer(Ptr<OutputStreamWrapper> stream, DataRate oldRate,
                         DataRate newRate) {
  *stream->GetStream() << Simulator::Now().GetSeconds() << " "
                       << newRate.GetBitRate() << std::endl;
}

static void ConnectSocketTraces(Ptr<OutputStreamWrapper> cwndStream,
                                Ptr<OutputStreamWrapper> rttStream,
                                Ptr<OutputStreamWrapper> ecnStream,
                                Ptr<OutputStreamWrapper> pacingStream) {
  Config::ConnectWithoutContext(
      "/NodeList/0/$ns3::TcpL4Protocol/SocketList/0/CongestionWindow",
      MakeBoundCallback(&CwndTracer, cwndStream));
  Config::ConnectWithoutContext(
      "/NodeList/0/$ns3::TcpL4Protocol/SocketList/0/RTT",
      MakeBoundCallback(&RttTracer, rttStream));
  Config::ConnectWithoutContext(
      "/NodeList/0/$ns3::TcpL4Protocol/SocketList/0/EcnState",
      MakeBoundCallback(&EcnStateTracer, ecnStream));
  Config::ConnectWithoutContext(
      "/NodeList/0/$ns3::TcpL4Protocol/SocketList/0/PacingRate",
      MakeBoundCallback(&PacingTracer, pacingStream));
}

int main(int argc, char *argv[]) {
  std::string bottleneckBw = "100Mbps";
  std::string bottleneckDelay = "1ms";
  std::string accessBw = "1Gbps";
  std::string accessDelay = "1ms";
  uint32_t queueSizePkts = 100;
  uint32_t redMinTh = 20;
  uint32_t redMaxTh = 60;
  bool useEcn = true; // 想看 BBR 在 RED-ECN / RED-drop 两种情况下的差异，可切换
  double simTime = 20.0;

  CommandLine cmd;
  cmd.AddValue("bottleneckBw", "Bottleneck bandwidth", bottleneckBw);
  cmd.AddValue("bottleneckDelay", "Bottleneck delay", bottleneckDelay);
  cmd.AddValue("queueSizePkts", "Bottleneck queue size (packets)",
               queueSizePkts);
  cmd.AddValue("redMinTh", "RED MinTh", redMinTh);
  cmd.AddValue("redMaxTh", "RED MaxTh", redMaxTh);
  cmd.AddValue("useEcn", "Enable ECN marking on RED", useEcn);
  cmd.AddValue("simTime", "Simulation time (s)", simTime);
  cmd.Parse(argc, argv);

  //! 使用 BBR
  Config::SetDefault("ns3::TcpL4Protocol::SocketType",
                     TypeIdValue(TcpBbr::GetTypeId()));
  Config::SetDefault("ns3::TcpSocketState::EnablePacing", BooleanValue(true));

  //! TCP ECN（对 BBR 来说，这里主要是让 sender/receiver 协商 ECN 能力）
  Config::SetDefault("ns3::TcpSocketBase::UseEcn",
                     StringValue(useEcn ? "On" : "Off"));

  //! RED 全局配置
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
  LogComponentEnable("BbrEcnSimulator", LOG_LEVEL_INFO);

  NodeContainer sender, router, receiver;
  sender.Create(1);
  router.Create(1);
  receiver.Create(1);

  InternetStackHelper stack;
  stack.InstallAll();

  PointToPointHelper p2pAccess;
  p2pAccess.SetDeviceAttribute("DataRate", StringValue(accessBw));
  p2pAccess.SetChannelAttribute("Delay", StringValue(accessDelay));

  PointToPointHelper p2pBottleneck;
  p2pBottleneck.SetDeviceAttribute("DataRate", StringValue(bottleneckBw));
  p2pBottleneck.SetChannelAttribute("Delay", StringValue(bottleneckDelay));

  NetDeviceContainer devLeft = p2pAccess.Install(sender.Get(0), router.Get(0));
  NetDeviceContainer devRight =
      p2pBottleneck.Install(router.Get(0), receiver.Get(0));

  TrafficControlHelper tchAccess;
  tchAccess.SetRootQueueDisc("ns3::PfifoFastQueueDisc");
  tchAccess.Uninstall(devLeft);
  tchAccess.Install(devLeft);

  TrafficControlHelper tchBottleneck;
  tchBottleneck.SetRootQueueDisc(
      "ns3::RedQueueDisc", "LinkBandwidth", StringValue(bottleneckBw),
      "LinkDelay", StringValue(bottleneckDelay), "MinTh", DoubleValue(redMinTh),
      "MaxTh", DoubleValue(redMaxTh), "UseEcn", BooleanValue(useEcn));
  tchBottleneck.Uninstall(devRight);
  QueueDiscContainer qdBottleneck = tchBottleneck.Install(devRight);

  Ipv4AddressHelper address;
  address.SetBase("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer ifLeft = address.Assign(devLeft);
  address.SetBase("10.1.2.0", "255.255.255.0");
  Ipv4InterfaceContainer ifRight = address.Assign(devRight);

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  uint16_t port = 9;
  PacketSinkHelper sinkHelper("ns3::TcpSocketFactory",
                              InetSocketAddress(Ipv4Address::GetAny(), port));
  ApplicationContainer sinkApp = sinkHelper.Install(receiver.Get(0));
  Ptr<PacketSink> sink = StaticCast<PacketSink>(sinkApp.Get(0));
  sinkApp.Start(Seconds(0.0));
  sinkApp.Stop(Seconds(simTime + 1.0));

  BulkSendHelper source("ns3::TcpSocketFactory",
                        InetSocketAddress(ifRight.GetAddress(1), port));
  source.SetAttribute("MaxBytes", UintegerValue(0));
  ApplicationContainer sourceApp = source.Install(sender.Get(0));
  sourceApp.Start(Seconds(1.0));
  sourceApp.Stop(Seconds(simTime));

  AsciiTraceHelper asciiHelper;
  auto cwndStream = asciiHelper.CreateFileStream("cwnd.log");
  auto rttStream = asciiHelper.CreateFileStream("rtt.log");
  auto ecnStream = asciiHelper.CreateFileStream("ecn-state.log");
  auto pacingStream = asciiHelper.CreateFileStream("pacing.log");
  auto qlenStream = asciiHelper.CreateFileStream("qlen.log");

  Simulator::Schedule(Seconds(1.001), &ConnectSocketTraces, cwndStream,
                      rttStream, ecnStream, pacingStream);

  Ptr<QueueDisc> redQd = qdBottleneck.Get(0);
  redQd->TraceConnectWithoutContext(
      "PacketsInQueue", MakeBoundCallback(&QueueLengthTracer, qlenStream));

  FlowMonitorHelper flowMon;
  Ptr<FlowMonitor> monitor = flowMon.InstallAll();

  Simulator::Stop(Seconds(simTime + 2.0));
  Simulator::Run();

  QueueDisc::Stats st = redQd->GetStats();
  std::ofstream redStats("red-stats.log");
  redStats << "# RED queue stats on bottleneck (BBR, useEcn=" << useEcn
           << ")\n";
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
