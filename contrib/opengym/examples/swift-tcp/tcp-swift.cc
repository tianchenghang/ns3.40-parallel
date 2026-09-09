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

/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
#include "tcp-swift.h"

#include "ns3/core-module.h"
#include "ns3/log.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE("TcpSwift");
NS_OBJECT_ENSURE_REGISTERED(TcpSwift);

TypeId TcpSwift::GetTypeId(void) {
  static TypeId tid = TypeId("ns3::TcpSwift")
                          .SetParent<TcpRlBase>()
                          .SetGroupName("Internet")
                          .AddConstructor<TcpSwift>();
  return tid;
}

TcpSwift::TcpSwift(void) : TcpRlBase() {}

TcpSwift::TcpSwift(const TcpSwift &sock) : TcpRlBase(sock) {}

TcpSwift::~TcpSwift(void) {}

std::string TcpSwift::GetName() const { return "TcpSwift"; }

Ptr<TcpCongestionOps> TcpSwift::Fork() { return CopyObject<TcpSwift>(this); }

void TcpSwift::CreateGymEnv() {
  NS_LOG_FUNCTION(this);
  Ptr<TcpSwiftEnv> env = CreateObject<TcpSwiftEnv>();
  env->SetSocketUuid(TcpRlBase::GenerateUuid());
  m_tcpGymEnv = env;

  ConnectSocketCallbacks();
}

} // namespace ns3
