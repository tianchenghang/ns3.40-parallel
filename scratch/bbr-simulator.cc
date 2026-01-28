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

NS_LOG_COMPONENT_DEFINE("BbrSimulator");

int main(int argc, char *argv[]) {
  Config::SetDefault("ns3::TcpL4Protocol::SocketType",
                     TypeIdValue(TcpBbr::GetTypeId()));
  //! BBR must use pacing
  Config::SetDefault("ns3::TcpSocketState::EnablePacing", BooleanValue(true));

  //! 开启窗口缩放
  // Config::SetDefault("ns3::TcpSocketBase::WindowScaling",
  // BooleanValue(true));

  //! 全局 TCP 参数
  Config::SetDefault("ns3::TcpSocket::SndBufSize",
                     UintegerValue(1 << 22 /** 22 */));
  Config::SetDefault("ns3::TcpSocket::RcvBufSize",
                     UintegerValue(1 << 22 /** 22 */));
  // Config::SetDefault("ns3::TcpBbr::HighGain", DoubleValue(2.89));
  // Config::SetDefault("ns3::TcpBbr::BwWindowLength", UintegerValue(10));

  //! 配置队列
  // Config::SetDefault("ns3::CoDelQueueDisc::MaxSize", StringValue("10000p"));
  Config::SetDefault("ns3::RedQueueDisc::MaxSize", StringValue("10000p"));
  // Config::SetDefault("ns3::FifoQueueDisc::MaxSize", StringValue("10000p"));

  //! 基础参数设置
  Time::SetResolution(Time::NS);
  LogComponentEnable("BbrSimulator", LOG_LEVEL_DEBUG);
  LogComponentEnable("TcpSocketBase", LOG_LEVEL_WARN);
  LogComponentEnable("TcpBbr", LOG_LEVEL_INFO);

  //! 创建节点容器
  NodeContainer sender;
  sender.Create(1); // 左端服务器节点 (n0)
  NodeContainer router;
  router.Create(1); // 路由器节点 (n1)
  NodeContainer receiver;
  receiver.Create(1); // 右端有线节点 (n2)

  //! 安装协议栈
  InternetStackHelper stack;
  stack.Install(sender);   // 安装有线节点 n0
  stack.Install(router);   // 安装路由器 n1
  stack.Install(receiver); // 安装有线节点 n2

  //! 配置左侧有线链路 (n0 -> n1)
  //! DataRate = 1Gbps, Delay = 100ms
  PointToPointHelper p2pLeft;
  p2pLeft.SetDeviceAttribute("DataRate", StringValue("1Gbps"));
  p2pLeft.SetChannelAttribute("Delay", StringValue("100ms"));

  //! 配置队列规则
  NetDeviceContainer p2pDevicesLeft =
      p2pLeft.Install(sender.Get(0), router.Get(0));
  TrafficControlHelper tchLeft;
  // tchLeft.SetRootQueueDisc("ns3::CoDelQueueDisc",
  //                          "MaxSize",
  //                          StringValue("10000p"),
  //                          "UseEcn",
  //                          BooleanValue(false));
  // tchLeft.SetRootQueueDisc("ns3::RedQueueDisc",
  //                          "MaxSize",
  //                          StringValue("10000p"),
  //                          "UseEcn",
  //                          BooleanValue(false));
  // tchLeft.SetRootQueueDisc("ns3::FifoQueueDisc",
  //                          "MaxSize",
  //                          StringValue("10000p"),
  //                          "UseEcn",
  //                          BooleanValue(false));
  tchLeft.Install(p2pDevicesLeft);

  //! 创建随机丢包模型
  Ptr<RateErrorModel> em = CreateObject<RateErrorModel>();
  em->SetAttribute("ErrorRate", DoubleValue(0.00001)); // 0.01% 丢包率
  em->SetAttribute("ErrorUnit", StringValue("ERROR_UNIT_PACKET"));
  //! 对 n0, n1 应用丢包模型
  p2pDevicesLeft.Get(0)->SetAttribute("ReceiveErrorModel", PointerValue(em));
  p2pDevicesLeft.Get(1)->SetAttribute("ReceiveErrorModel", PointerValue(em));

  //! 配置右侧有线链路 (n1 -> n2)
  //! DataRate = 100Mbps, Delay = 10ms
  PointToPointHelper p2pRight;
  p2pRight.SetDeviceAttribute("DataRate", StringValue("100Mbps"));
  p2pRight.SetChannelAttribute("Delay", StringValue("10ms"));

  //! 配置队列规则
  NetDeviceContainer p2pDevicesRight =
      p2pRight.Install(router.Get(0), receiver.Get(0));
  TrafficControlHelper tchRight;
  // tchRight.SetRootQueueDisc("ns3::CoDelQueueDisc", "MaxSize",
  //                           StringValue("10000p"), "UseEcn",
  //                           BooleanValue(false));
  // tchRight.SetRootQueueDisc("ns3::RedQueueDisc", "MaxSize",
  //                           StringValue("10000p"), "UseEcn",
  //                           BooleanValue(false));
  // tchRight.SetRootQueueDisc("ns3::FifoQueueDisc", "MaxSize",
  //                           StringValue("10000p"), "UseEcn",
  //                           BooleanValue(false));
  tchRight.Install(p2pDevicesRight);

  // 分配 IP 地址
  Ipv4AddressHelper address;

  //! 左侧有线网络 (10.1.1.0/24)
  address.SetBase("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer p2pInterfacesLeft = address.Assign(p2pDevicesLeft);

  //! 右侧有线网络 (10.1.2.0/24)
  address.SetBase("10.1.2.0", "255.255.255.0");
  Ipv4InterfaceContainer p2pInterfacesRight = address.Assign(p2pDevicesRight);

  //! 开启路由转发
  router.Get(0)->GetObject<Ipv4>()->SetAttribute("IpForward",
                                                 BooleanValue(true));
  Ipv4StaticRoutingHelper staticRouting;
  Ptr<Ipv4StaticRouting> staticRouter =
      staticRouting.GetStaticRouting(router.Get(0)->GetObject<Ipv4>());
  staticRouter->AddNetworkRouteTo(Ipv4Address("10.1.1.0"),
                                  Ipv4Mask("255.255.255.0"),
                                  1); // 左侧网络
  staticRouter->AddNetworkRouteTo(Ipv4Address("10.1.2.0"),
                                  Ipv4Mask("255.255.255.0"),
                                  2); // 右侧网络

  //! 为右端节点 (n2) 添加默认路由
  Ptr<Ipv4StaticRouting> rightNodeRouting =
      staticRouting.GetStaticRouting(receiver.Get(0)->GetObject<Ipv4>());
  rightNodeRouting->SetDefaultRoute(Ipv4Address("10.1.2.1"), 1);

  Ipv4GlobalRoutingHelper::PopulateRoutingTables();

  //! 安装 ping, 客户端定期探测 RTT
  PingHelper pingHelper(p2pInterfacesRight.GetAddress(0));
  pingHelper.SetAttribute("Interval", TimeValue(MilliSeconds(100)));
  pingHelper.SetAttribute("Count", UintegerValue(10000));
  ApplicationContainer pingApps = pingHelper.Install(receiver.Get(0));
  pingApps.Start(Seconds(1.0));
  pingApps.Stop(Seconds(100.0));

  std::ofstream rttLog("rtt.log");
  Ptr<Ping> pingApp = DynamicCast<Ping>(pingApps.Get(0));
  rttLog << "Timestamp(s)\tRtt(ms)\n";
  Callback<void, uint16_t, Time> rttCb([&rttLog](uint16_t seq, Time rtt) {
    rttLog << Simulator::Now().GetSeconds() << " " << rtt.GetMilliSeconds()
           << std::endl;
    // RttCache::Instance().PushRtt(rtt); // 缓存 RTT
  });

  pingApp->TraceConnectWithoutContext("Rtt", rttCb);

  //! 安装 TCP 接收端 (右端节点 n2)
  PacketSinkHelper sinkHelper("ns3::TcpSocketFactory",
                              InetSocketAddress(Ipv4Address::GetAny(), 9));
  ApplicationContainer sinkApp = sinkHelper.Install(receiver.Get(0));
  Ptr<PacketSink> sink = StaticCast<PacketSink>(sinkApp.Get(0));

  //! 安装 TCP 发送端 (左端节点 n0)
  OnOffHelper server("ns3::TcpSocketFactory",
                     InetSocketAddress(p2pInterfacesRight.GetAddress(1), 9));

  server.SetAttribute("DataRate", StringValue("1Gbps"));
  server.SetAttribute("PacketSize", UintegerValue(1472));

  server.SetAttribute(
      "OnTime",
      StringValue("ns3::ConstantRandomVariable[Constant=100]")); // 单位 s
  server.SetAttribute("OffTime",
                      StringValue("ns3::ConstantRandomVariable[Constant=0]"));
  //! 为节点 n0 安装服务器程序
  ApplicationContainer serverApp = server.Install(sender.Get(0));

  // BulkSendHelper sender("ns3::TcpSocketFactory",
  //                       InetSocketAddress(p2pInterfacesRight.GetAddress(1),
  //                       9));
  // sender.SetAttribute("MaxBytes", UintegerValue(100 * 1e6 * 100 / 8));
  // // 100Mbps * 100s 为节点 n0 安装服务器程序 ApplicationContainer serverApp =
  // sender.Install(leftWiredNodes.Get(0));

  // !!! <<< Burst start <<< !!!
  OnOffHelper onOff1("ns3::UdpSocketFactory",
                     InetSocketAddress(p2pInterfacesRight.GetAddress(1)));
  onOff1.SetAttribute("DataRate", DataRateValue(DataRate("1Gbps")));
  onOff1.SetAttribute("PacketSize", UintegerValue(1472));
  ApplicationContainer app1 = onOff1.Install(sender.Get(0));
  // app1.Start(Seconds(10.0));
  // app1.Stop(Seconds(50.0));
  for (auto start = 50.0; start < 100.0; start += 10.0) {
    app1.Start(Seconds(start));
    app1.Stop(Seconds(start + 1.0));
  }
  // !!! >>> Burst end >>> !!!

  //! 启动应用
  sinkApp.Start(Seconds(0.0));
  serverApp.Start(Seconds(1.0));
  serverApp.Stop(Seconds(100.0));

  //! 安装流量监控
  FlowMonitorHelper flowMonitor;
  Ptr<FlowMonitor> monitor = flowMonitor.InstallAll();

  Simulator::Stop(Seconds(103.0));

  //! 左侧节点 (n0) IP
  auto leftN0Ipv4 = sender.Get(0)->GetObject<Ipv4>();
  for (auto i = 0; i < leftN0Ipv4->GetNInterfaces(); ++i) {
    NS_LOG_UNCOND("[n0] Interface" << i << ": "
                                   << leftN0Ipv4->GetAddress(i, 0).GetLocal());
  }

  //! 路由器 (n1) IP
  Ptr<Ipv4> routerIpv4 = router.Get(0)->GetObject<Ipv4>();
  for (uint32_t i = 0; i < routerIpv4->GetNInterfaces(); ++i) {
    NS_LOG_UNCOND("[n1] Interface" << i << ": "
                                   << routerIpv4->GetAddress(i, 0).GetLocal());
  }

  //! 右侧节点 (n2) IP
  auto rightN0Ipv4 = receiver.Get(0)->GetObject<Ipv4>();
  for (auto i = 0; i < rightN0Ipv4->GetNInterfaces(); ++i) {
    NS_LOG_UNCOND("[n2] Interface" << i << ": "
                                   << rightN0Ipv4->GetAddress(i, 0).GetLocal());
  }

  // 运行仿真
  Simulator::Run();

  // 输出结果
  monitor->CheckForLostPackets();
  Ptr<ns3::Ipv4FlowClassifier> classifier =
      DynamicCast<ns3::Ipv4FlowClassifier>(flowMonitor.GetClassifier());

  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();

  for (auto &iter : stats) {
    Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(iter.first);
    NS_LOG_UNCOND("TCP Flow " << iter.first << " Src Addr: " << t.sourceAddress
                              << " Dst Addr: " << t.destinationAddress);
    NS_LOG_UNCOND(
        "Time Last Rx Packet: " << iter.second.timeLastRxPacket.GetSeconds());
    NS_LOG_UNCOND(
        "Time First Tx Packet: " << iter.second.timeFirstTxPacket.GetSeconds());
    NS_LOG_UNCOND("Tx Packets Count: " << iter.second.txPackets);
    NS_LOG_UNCOND("Rx Packets Count: " << iter.second.rxPackets);
    NS_LOG_UNCOND("Loss Rate: "
                  << (iter.second.lostPackets / (double)iter.second.txPackets) *
                         100
                  << "%");
    NS_LOG_UNCOND("Throughput: "
                  << iter.second.rxBytes * 8.0 /
                         (iter.second.timeLastRxPacket.GetSeconds() -
                          iter.second.timeFirstTxPacket.GetSeconds()) /
                         1e6
                  << " Mbps");
  }

  NS_LOG_UNCOND("Total Rx Bytes Count: " << sink->GetTotalRx());
  Simulator::Destroy();

  return 0;
}
