/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
#include "tcp-gemini.h"

#include "ns3/core-module.h"
#include "ns3/log.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE("ns3::TcpGemini");
NS_OBJECT_ENSURE_REGISTERED(TcpGemini);

TypeId TcpGemini::GetTypeId(void) {
  static TypeId tid = TypeId("ns3::TcpGemini")
                          .SetParent<TcpRlBase>()
                          .SetGroupName("Internet")
                          .AddConstructor<TcpGemini>();
  return tid;
}

TcpGemini::TcpGemini(void) : TcpRlBase() {}

TcpGemini::TcpGemini(const TcpGemini &sock) : TcpRlBase(sock) {}

TcpGemini::~TcpGemini(void) {}

std::string TcpGemini::GetName() const { return "TcpGemini"; }

Ptr<TcpCongestionOps> TcpGemini::Fork() { return CopyObject<TcpGemini>(this); }

void TcpGemini::CreateGymEnv() {
  NS_LOG_FUNCTION(this);
  Ptr<TcpGeminiEnv> env = CreateObject<TcpGeminiEnv>();
  env->SetSocketUuid(TcpRlBase::GenerateUuid());
  m_tcpGymEnv = env;

  ConnectSocketCallbacks();
}

} // namespace ns3
