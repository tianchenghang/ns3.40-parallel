#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/flow-monitor-helper.h"
#include "ns3/flow-monitor-module.h" // FlowMonitor 模块
#include "ns3/internet-module.h"
#include "ns3/ipv4-flow-classifier.h" // 关键头文件
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/ping-helper.h"
#include "ns3/point-to-point-module.h"
#include "ns3/ssid.h"
#include "ns3/tcp-bbr.h"
#include "ns3/tcp-socket-factory.h"
#include "ns3/traffic-control-module.h" // 流量控制模块
#include "ns3/yans-wifi-helper.h"

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("Bbr4to1Simulator");

int main(int argc, char *argv[]) {
  Config::SetDefault("ns3::TcpL4Protocol::SocketType",
                     TypeIdValue(TcpBbr::GetTypeId()));

  //! BBR must use pacing
  Config::SetDefault("ns3::TcpSocketState::EnablePacing", BooleanValue(true));

  //! 全局 TCP 参数
  Config::SetDefault("ns3::TcpSocket::SndBufSize", UintegerValue(1 << 22));
  Config::SetDefault("ns3::TcpSocket::RcvBufSize", UintegerValue(1 << 22));

  //! 配置队列
  Config::SetDefault("ns3::RedQueueDisc::MaxSize", StringValue("10000p"));

  //! 基础参数设置
  Time::SetResolution(Time::NS);
  LogComponentEnable("Bbr4to1Simulator", LOG_LEVEL_INFO);
  LogComponentEnable("TcpSocketBase", LOG_LEVEL_WARN);
  LogComponentEnable("TcpBbr", LOG_LEVEL_INFO);

  //! 创建节点容器
  NodeContainer senders; // n0‑n3
  senders.Create(4);
  Ptr<Node> receiver = CreateObject<Node>(); // n4
  Ptr<Node> router = CreateObject<Node>();   // n5

  //! 安装协议栈
  InternetStackHelper stack;
  stack.Install(senders);
  stack.Install(router);
  stack.Install(receiver);

  // n0 -> n4; n1 -> n4; n2 -> n4; n3 -> n4
  PointToPointHelper p2pLeft;

  //! 1Gbps left bandwidth
  p2pLeft.SetDeviceAttribute("DataRate", StringValue("30Gbps"));
  p2pLeft.SetChannelAttribute("Delay", StringValue("100ms"));

  PointToPointHelper p2pRight;

  //! 100Mbps right bandwidth (bottleneck)
  p2pRight.SetDeviceAttribute("DataRate", StringValue("100Mbps")); // 瓶颈
  p2pRight.SetChannelAttribute("Delay", StringValue("10ms"));

  std::vector<NetDeviceContainer> ndcLeft(4);
  for (uint32_t i = 0; i < 4; ++i) {
    ndcLeft[i] = p2pLeft.Install(senders.Get(i), router);

    //! 创建随机丢包模型
    Ptr<RateErrorModel> rem = CreateObject<RateErrorModel>();
    rem->SetAttribute("ErrorRate", DoubleValue(0.00001));
    rem->SetAttribute("ErrorUnit", StringValue("ERROR_UNIT_PACKET"));
    ndcLeft[i].Get(0)->SetAttribute("ReceiveErrorModel", PointerValue(rem));
    ndcLeft[i].Get(1)->SetAttribute("ReceiveErrorModel", PointerValue(rem));
  }

  NetDeviceContainer ndcRight = p2pRight.Install(router, receiver);

  TrafficControlHelper tchLeft;
  // tchLeft.SetRootQueueDisc("ns3::RedQueueDisc");
  for (uint32_t i = 0; i < 4; ++i) {
    tchLeft.Install(ndcLeft[i]);
  }

  TrafficControlHelper tchRight;
  // tchRight.SetRootQueueDisc("ns3::RedQueueDisc");
  tchRight.Install(ndcRight);

  Ipv4AddressHelper addr;
  std::vector<Ipv4InterfaceContainer> icLeft(4);
  for (uint32_t i = 0; i < 4; ++i) {
    std::ostringstream s;
    // 10.1.1.0/24
    // 10.1.2.0/24
    // 10.1.3.0/24
    // 10.1.4.0/24
    s << "10.1." << (i + 1) << ".0";
    addr.SetBase(s.str().c_str(), "255.255.255.0");
    icLeft[i] = addr.Assign(ndcLeft[i]);
  }
  addr.SetBase("10.1.100.0", "255.255.255.0");
  Ipv4InterfaceContainer icRight = addr.Assign(ndcRight);

  Ipv4StaticRoutingHelper sr;
  Ptr<Ipv4StaticRouting> srLeft =
      sr.GetStaticRouting(router->GetObject<Ipv4>());
  for (uint32_t i = 0; i < 4; ++i) {
    srLeft->AddNetworkRouteTo(
        Ipv4Address(("10.1." + std::to_string(i + 1) + ".0").c_str()),
        Ipv4Mask("255.255.255.0"), i + 1);
  }
  srLeft->AddNetworkRouteTo(Ipv4Address("10.1.100.0"),
                            Ipv4Mask("255.255.255.0"), 5);

  Ptr<Ipv4StaticRouting> srRight =
      sr.GetStaticRouting(receiver->GetObject<Ipv4>());
  srRight->SetDefaultRoute(icRight.GetAddress(0), 1);

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  OnOffHelper mainTcp("ns3::TcpSocketFactory",
                      InetSocketAddress(icRight.GetAddress(1), 9000));

  //! 1G main tcp flow
  mainTcp.SetAttribute("DataRate", StringValue("1Gbps"));
  mainTcp.SetAttribute("PacketSize", UintegerValue(1472));
  mainTcp.SetAttribute(
      "OnTime", StringValue("ns3::ConstantRandomVariable[Constant=100]"));
  mainTcp.SetAttribute("OffTime",
                       StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  ApplicationContainer mainApp = mainTcp.Install(senders.Get(0));

  for (uint32_t i = 1; i < 4; ++i) {
    OnOffHelper burst("ns3::UdpSocketFactory",
                      InetSocketAddress(icRight.GetAddress(1), 9000 + i));

    //! 4 * 1G udp burst
    burst.SetAttribute("DataRate", StringValue("1Gbps"));
    burst.SetAttribute("PacketSize", UintegerValue(1472));
    burst.SetAttribute("OnTime",
                       StringValue("ns3::ConstantRandomVariable[Constant=1]"));
    burst.SetAttribute("OffTime",
                       StringValue("ns3::ConstantRandomVariable[Constant=0]"));
    ApplicationContainer burstApp = burst.Install(senders.Get(i));

    for (double t = 50.0; t < 100.0; t += 5.0) {
      burstApp.Start(Seconds(t));
      burstApp.Stop(Seconds(t + 1.0));
    }
  }

  ApplicationContainer sinkApp;
  PacketSinkHelper tcpSink("ns3::TcpSocketFactory",
                           InetSocketAddress(Ipv4Address::GetAny(), 9000));

  sinkApp.Add(tcpSink.Install(receiver));
  for (uint16_t port = 9001; port <= 9003; ++port) {
    PacketSinkHelper udpSink("ns3::UdpSocketFactory",
                             InetSocketAddress(Ipv4Address::GetAny(), port));
    sinkApp.Add(udpSink.Install(receiver));
  }

  Ptr<PacketSink> sink = StaticCast<PacketSink>(sinkApp.Get(0));

  sinkApp.Start(Seconds(0.5));
  sinkApp.Stop(Seconds(101.5));
  mainApp.Start(Seconds(1.0));
  mainApp.Stop(Seconds(101.0));

  //! 安装流量监控
  FlowMonitorHelper flowMon;
  Ptr<FlowMonitor> monitor = flowMon.InstallAll();

  Simulator::Stop(Seconds(103.0));

  //! <<< Ping start
  PingHelper ping(icRight.GetAddress(0));
  ping.SetAttribute("Interval", TimeValue(MilliSeconds(100)));
  ping.SetAttribute("Count", UintegerValue(10000));

  ApplicationContainer pingApps = ping.Install(receiver);
  pingApps.Start(Seconds(1.0));
  pingApps.Stop(Seconds(101.0));

  std::ofstream rttLog("rtt.log");
  Ptr<Ping> pingApp = DynamicCast<Ping>(pingApps.Get(0));
  Callback<void, uint16_t, Time> rttCallback([&rttLog](uint16_t seq, Time rtt) {
    rttLog << Simulator::Now().GetSeconds() << " " << rtt.GetMilliSeconds()
           << std::endl;
    // RttCache::Instance().PushRtt(rtt); // 缓存 RTT
  });
  pingApp->TraceConnectWithoutContext("Rtt", rttCallback);
  //! >>> Ping end

  Simulator::Run();

  //! 输出结果
  monitor->CheckForLostPackets();
  Ptr<ns3::Ipv4FlowClassifier> classifier =
      DynamicCast<ns3::Ipv4FlowClassifier>(flowMon.GetClassifier());

  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

  for (auto &iter : stats) {
    Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(iter.first);
    NS_LOG_UNCOND("\n\n\nFlow Id: " << iter.first << " src: " << t.sourceAddress
                                    << " dst: " << t.destinationAddress);
    NS_LOG_UNCOND(
        "Time last rx packet: " << iter.second.timeLastRxPacket.GetSeconds());
    NS_LOG_UNCOND(
        "Time first tx packet: " << iter.second.timeFirstTxPacket.GetSeconds());
    NS_LOG_UNCOND("Tx packets: " << iter.second.txPackets);
    NS_LOG_UNCOND("Rx packets: " << iter.second.rxPackets);
    NS_LOG_UNCOND("Lost packets: " << iter.second.lostPackets);

    NS_LOG_UNCOND(
        "Loss: " << (iter.second.lostPackets / (double)iter.second.txPackets) *
                        100
                 << "%");
    NS_LOG_UNCOND("Throughput: "
                  << iter.second.rxBytes * 8.0 /
                         (iter.second.timeLastRxPacket.GetSeconds() -
                          iter.second.timeFirstTxPacket.GetSeconds()) /
                         1e6
                  << " Mbps");
  }
  NS_LOG_UNCOND("Total rx: " << sink->GetTotalRx());
  Simulator::Destroy();
  return 0;
}
