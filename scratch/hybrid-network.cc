// clang-format -i -style=google ./scratch/*.cc
#include "ns3/applications-module.h"
#include "ns3/core-module.h"
#include "ns3/flow-monitor-helper.h"
#include "ns3/flow-monitor-module.h" // FlowMonitor 模块
#include "ns3/internet-module.h"
#include "ns3/ipv4-flow-classifier.h" // 关键头文件
#include "ns3/mobility-module.h"
#include "ns3/network-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/ssid.h"
#include "ns3/tcp-bbr.h"
#include "ns3/tcp-socket-factory.h"
#include "ns3/traffic-control-module.h" // 流量控制模块
#include "ns3/yans-wifi-helper.h"

#include <ostream>

using namespace ns3;

NS_LOG_COMPONENT_DEFINE("main");

int main(int argc, char *argv[]) {
  Config::SetDefault("ns3::TcpL4Protocol::SocketType",
                     TypeIdValue(TcpBbr::GetTypeId()));
  //! BBR must use pacing
  Config::SetDefault("ns3::TcpSocketState::EnablePacing", BooleanValue(true));

  //! 使用 DCTCP
  // Config::SetDefault("ns3::TcpL4Protocol::SocketType",
  // TypeIdValue(TcpDctcp::GetTypeId()));

  //! 开启 TCP ECN 支持
  // Config::SetDefault("ns3::TcpSocketBase::UseEcn", StringValue("On"));

  //! 配置队列, 以支持 ECN
  // Config::SetDefault("ns3::CoDelQueueDisc::UseEcn", BooleanValue(false));
  // Config::SetDefault("ns3::CoDelQueueDisc::MaxSize", StringValue("10000p"));
  // Config::SetDefault("ns3::RedQueueDisc::UseEcn", BooleanValue(true));
  Config::SetDefault("ns3::RedQueueDisc::MaxSize", StringValue("10000p"));
  // Config::SetDefault("ns3::FifoQueueDisc::UseEcn", BooleanValue(true));
  // Config::SetDefault("ns3::FifoQueueDisc::MaxSize", StringValue("10000p"));

  //! 开启窗口缩放
  // Config::SetDefault("ns3::TcpSocketBase::WindowScaling",
  // BooleanValue(true));

  //! 全局 TCP 参数
  Time::SetResolution(Time::NS);
  LogComponentEnable("main", LOG_LEVEL_DEBUG);
  LogComponentEnable("TcpSocketBase", LOG_LEVEL_WARN);
  LogComponentEnable("TcpBbr", LOG_LEVEL_WARN);
  // Config::SetDefault("ns3::TcpBbr::HighGain", DoubleValue(2.89));
  // Config::SetDefault("ns3::TcpBbr::BwWindowLength", UintegerValue(10));

  //! 创建节点容器
  NodeContainer wiredNodes;
  wiredNodes.Create(1); // 左端服务器节点 (n0)
  NodeContainer router;
  router.Create(1); // 路由器节点 (n1, AP)
  NodeContainer wifiStaNodes;
  wifiStaNodes.Create(1); // 右端无线终端节点 (n2, STA)
  PointToPointHelper p2pLeft;

  //! 安装协议栈
  InternetStackHelper stack;
  stack.Install(wiredNodes);   // 安装有线节点 n0
  stack.Install(router);       // 安装路由器 n1 (AP)
  stack.Install(wifiStaNodes); // 安装无线节点 n2 (STA)

  //! 配置左侧有线链路 (n0 -> n1)
  p2pLeft.SetDeviceAttribute("DataRate", StringValue("1Gbps"));
  p2pLeft.SetChannelAttribute("Delay", StringValue("100ms"));

  //! 配置队列规则
  NetDeviceContainer wiredDevicesLeft =
      p2pLeft.Install(wiredNodes.Get(0), router.Get(0));
  TrafficControlHelper tchLeft;
  // tchLeft.SetRootQueueDisc("ns3::CoDelQueueDisc",
  //                          "MaxSize",
  //                          StringValue("10000p"),
  //                          "UseEcn",
  //                          BooleanValue(false));
  tchLeft.SetRootQueueDisc("ns3::RedQueueDisc",
                             "MaxSize",
                             StringValue("10000p")/** ,
                             "UseEcn",
                             BooleanValue(true) */);
  // tchLeft.SetRootQueueDisc("ns3::FifoQueueDisc",
  //                          "MaxSize",
  //                          StringValue("10000p"),
  //                          "UseEcn",
  //                          BooleanValue(true));
  tchLeft.Install(wiredDevicesLeft);

  //! 创建随机丢包模型
  Ptr<RateErrorModel> em = CreateObject<RateErrorModel>();
  em->SetAttribute("ErrorRate", DoubleValue(0.00001)); // 0.01% 丢包率
  em->SetAttribute("ErrorUnit", StringValue("ERROR_UNIT_PACKET"));

  //! 对 n0, n1 应用丢包模型
  wiredDevicesLeft.Get(0)->SetAttribute("ReceiveErrorModel", PointerValue(em));
  wiredDevicesLeft.Get(1)->SetAttribute("ReceiveErrorModel", PointerValue(em));

  //! 配置无线链路 (n1: AP -> n2: STA)
  YansWifiChannelHelper channel;
  channel.SetPropagationDelay("ns3::ConstantSpeedPropagationDelayModel",
                              "Speed",
                              DoubleValue(3e8)); // 默认 3e8
  // 路径损耗指数 Exponent: 值越大, 信号衰减越快
  // channel.AddPropagationLoss("ns3::LogDistancePropagationLossModel",
  //                            "Exponent",
  //                            DoubleValue(2.0), // 路径损耗指数默认 2.0
  //                            "ReferenceDistance",
  //                            DoubleValue(1.0), // 参考距离 1m
  //                            "ReferenceLoss",
  //                            DoubleValue(46.0)); // 2.4GHz 频段参考损耗
  channel.AddPropagationLoss("ns3::RandomPropagationLossModel");
  YansWifiPhyHelper phy;
  phy.SetChannel(channel.Create());
  WifiHelper wifi;
  wifi.SetStandard(WIFI_STANDARD_80211n); // 802.11n 标准

  //! HtMcs3 信号要求低, 抗干扰能力强, 典型速率 (20MHz) 慢, ≈65 Mbps
  // wifi.SetRemoteStationManager("ns3::ConstantRateWifiManager",
  //                              "DataMode",
  //                              StringValue("HtMcs3"),
  //                              "ControlMode",
  //                              StringValue("HtMcs0"));

  //! HtMcs7 信号要求高, 抗干扰能力弱, 典型速率 (20MHz) 快, ≈72.2Mbps
  // 数据帧使用 HtMcs7, 高吞吐
  wifi.SetRemoteStationManager("ns3::ConstantRateWifiManager", "DataMode",
                               StringValue("HtMcs7"), "ControlMode",
                               StringValue("HtMcs0")); // 控制帧使用 HtMcs0

  WifiMacHelper mac;
  Ssid ssid = Ssid("HybridNetwork");

  // 配置 AP (n1 路由器)
  mac.SetType("ns3::ApWifiMac", "Ssid", SsidValue(ssid));
  NetDeviceContainer apDevices = wifi.Install(phy, mac, router.Get(0));

  // 配置 STA (n2 终端)
  // ActiveProbing: false, STA 不会主动发送探测请求
  mac.SetType("ns3::StaWifiMac", "Ssid", SsidValue(ssid), "ActiveProbing",
              BooleanValue(false));
  NetDeviceContainer wirelessDeviceRight = wifi.Install(phy, mac, wifiStaNodes);

  // 设置节点位置
  MobilityHelper mobility;

  // AP 位置 (0, 0, 0)
  mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
  mobility.Install(router);
  router.Get(0)->GetObject<MobilityModel>()->SetPosition(Vector(0, 0, 0));

  // AP 位置 (0, 0, 0)
  // STA 位置 (40, y, 0)
  // [(40, 0, 0), (40, 10, 0), (40, 20, 0), ...]
  mobility.SetPositionAllocator("ns3::GridPositionAllocator", "MinX",
                                DoubleValue(40), // startX = 40
                                "MinY",
                                DoubleValue(0.0), // startY = 0
                                "DeltaX",
                                DoubleValue(0.0), // deltaX = 0
                                "DeltaY",
                                DoubleValue(10.0), // deltaY = 10
                                "GridWidth", UintegerValue(1), "LayoutType",
                                StringValue("RowFirst"));
  mobility.SetMobilityModel("ns3::ConstantPositionMobilityModel");
  mobility.Install(wifiStaNodes);

  TrafficControlHelper tchRight;
  // tchRight.SetRootQueueDisc("ns3::CoDelQueueDisc",
  //                           "MaxSize",
  //                           StringValue("10000p"),
  //                           "UseEcn",
  //                           BooleanValue(false));
  tchRight.SetRootQueueDisc("ns3::RedQueueDisc",
                              "MaxSize",
                              StringValue("10000p")/** ,
                              "UseEcn",
                              BooleanValue(true) */);
  // tchLeft.SetRootQueueDisc("ns3::FifoQueueDisc",
  //                          "MaxSize",
  //                          StringValue("10000p"),
  //                          "UseEcn",
  //                          BooleanValue(true));
  tchRight.Install(wirelessDeviceRight);

  // 分配 IP 地址
  Ipv4AddressHelper address;

  //! 有线网络 (10.1.1.0/24)
  address.SetBase("10.1.1.0", "255.255.255.0");
  Ipv4InterfaceContainer p2pInterfaces = address.Assign(wiredDevicesLeft);

  //! 无线网络 (192.168.1.0/24)
  address.SetBase("192.168.1.0", "255.255.255.0");
  Ipv4InterfaceContainer apInterface = address.Assign(apDevices);
  Ipv4InterfaceContainer staInterfaces = address.Assign(wirelessDeviceRight);

  //! 开启路由转发
  router.Get(0)->GetObject<Ipv4>()->SetAttribute("IpForward",
                                                 BooleanValue(true));
  Ipv4StaticRoutingHelper staticRouting;
  Ptr<Ipv4StaticRouting> staticRouter =
      staticRouting.GetStaticRouting(router.Get(0)->GetObject<Ipv4>());

  //! 配置 n1 的路由表 (无线网络 ---> 有线网络)
  staticRouter->AddNetworkRouteTo(Ipv4Address("10.1.1.0"),
                                  Ipv4Mask("255.255.255.0"), 1);

  //! 配置 n1 的路由表 (无线网络 <--- 无线网络)
  staticRouter->AddNetworkRouteTo(Ipv4Address("192.168.1.0"),
                                  Ipv4Mask("255.255.255.0"), 2);

  //! 为无线节点 (n2) 添加默认路由
  for (uint32_t i = 0; i < wifiStaNodes.GetN(); ++i) {
    Ptr<Ipv4StaticRouting> staStaticRouting =
        staticRouting.GetStaticRouting(wifiStaNodes.Get(i)->GetObject<Ipv4>());
    // 网关指向 AP 的 IP
    staStaticRouting->SetDefaultRoute(
        router.Get(0)->GetObject<Ipv4>()->GetAddress(2, 0).GetLocal(), 1);
  }

  //! 安装 TCP 接收端 (右端节点 n2)
  Ipv4GlobalRoutingHelper::PopulateRoutingTables();
  PacketSinkHelper sinkHelper("ns3::TcpSocketFactory",
                              InetSocketAddress(Ipv4Address::GetAny(), 9));
  ApplicationContainer sinkApp = sinkHelper.Install(wifiStaNodes.Get(0));
  Ptr<PacketSink> sink = StaticCast<PacketSink>(sinkApp.Get(0));

  //! 安装 TCP 发送端 (左端节点 n0)
  OnOffHelper server("ns3::TcpSocketFactory",
                     InetSocketAddress(staInterfaces.GetAddress(0), 9));
  server.SetAttribute("PacketSize", UintegerValue(1472));
  server.SetAttribute("DataRate", StringValue("1Gbps"));
  server.SetAttribute("OnTime",
                      StringValue("ns3::ConstantRandomVariable[Constant=100]"));
  server.SetAttribute("OffTime",
                      StringValue("ns3::ConstantRandomVariable[Constant=0]"));

  //! 为节点 n0 安装服务器程序
  ApplicationContainer serverApp = server.Install(wiredNodes.Get(0));

  // BulkSendHelper sender("ns3::TcpSocketFactory",
  //                       InetSocketAddress(p2pInterfacesRight.GetAddress(1),
  //                       9));
  // sender.SetAttribute("MaxBytes", UintegerValue(100 * 1e6 * 100 / 8));
  // // 100Mbps * 100s 为节点 n0 安装服务器程序 ApplicationContainer serverApp =
  // sender.Install(leftWiredNodes.Get(0));

  //! 启动应用
  sinkApp.Start(Seconds(0.0));
  serverApp.Start(Seconds(1.0));
  serverApp.Stop(Seconds(100.0));

  //! 安装流量监控
  FlowMonitorHelper flowMonitor;
  Ptr<FlowMonitor> monitor = flowMonitor.InstallAll();
  LogComponentEnable("main", LOG_LEVEL_WARN);
  Simulator::Stop(Seconds(103.0));

  //! 左侧节点 (n0) IP
  auto n0Ipv4 = wiredNodes.Get(0)->GetObject<Ipv4>();
  for (auto i = 0; i < n0Ipv4->GetNInterfaces(); ++i) {
    NS_LOG_UNCOND("[n0] Interface" << i << ": "
                                   << n0Ipv4->GetAddress(i, 0).GetLocal());
  }

  //! 路由器 (n1) IP
  Ptr<Ipv4> routerIpv4 = router.Get(0)->GetObject<Ipv4>();
  for (uint32_t i = 0; i < routerIpv4->GetNInterfaces(); ++i) {
    NS_LOG_UNCOND("[n1] Interface" << i << ": "
                                   << routerIpv4->GetAddress(i, 0).GetLocal());
  }

  //! 右侧节点 (n2) IP
  auto n2Ipv4 = wifiStaNodes.Get(0)->GetObject<Ipv4>();
  for (auto i = 0; i < n2Ipv4->GetNInterfaces(); ++i) {
    NS_LOG_UNCOND("[n2] Interface" << i << ": "
                                   << n2Ipv4->GetAddress(i, 0).GetLocal());
  }

  // 运行仿真
  Simulator::Run();

  // 输出结果
  monitor->CheckForLostPackets();
  Ptr<ns3::Ipv4FlowClassifier> classifier =
      DynamicCast<ns3::Ipv4FlowClassifier>(flowMonitor.GetClassifier());
  std::map<FlowId, FlowMonitor::FlowStats> stats = monitor->GetFlowStats();
  for (auto iter = stats.begin(); iter != stats.end(); ++iter) {
    Ipv4FlowClassifier::FiveTuple t = classifier->FindFlow(iter->first);

    NS_LOG_UNCOND("TCP Flow " << iter->first << " Src Addr: " << t.sourceAddress
                              << " Dst Addr: " << t.destinationAddress);
    NS_LOG_UNCOND("Tx Packets Count: " << iter->second.txPackets);
    NS_LOG_UNCOND("Rx Packets Count: " << iter->second.rxPackets);
    NS_LOG_UNCOND("Loss Rate: " << (iter->second.lostPackets /
                                    (double)iter->second.txPackets) *
                                       100
                                << "%");
    NS_LOG_UNCOND("Throughput: "
                  << iter->second.rxBytes * 8.0 /
                         (iter->second.timeLastRxPacket.GetSeconds() -
                          iter->second.timeFirstTxPacket.GetSeconds()) /
                         1e6
                  << "Mbps");
  }
  NS_LOG_UNCOND("Total Rx Bytes Count: " << sink->GetTotalRx());
  Simulator::Destroy();

  return 0;
}
