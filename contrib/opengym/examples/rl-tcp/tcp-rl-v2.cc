/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
/*
 * Copyright (c) 2018 Technische Universität Berlin
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation;
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 *
 * Author: Piotr Gawlowicz <gawlowicz@tkn.tu-berlin.de>
 */

#include "tcp-rl-v2.h"

#include "tcp-rl-env.h"

#include "ns3/core-module.h"
#include "ns3/log.h"
#include "ns3/node-list.h"
#include "ns3/object.h"
#include "ns3/simulator.h"
#include "ns3/tcp-header.h"
#include "ns3/tcp-l4-protocol.h"
#include "ns3/tcp-socket-base.h"

namespace ns3 {

NS_OBJECT_ENSURE_REGISTERED(TcpSocketDerivedV2);

TypeId TcpSocketDerivedV2::GetTypeId(void) {
  static TypeId tid = TypeId("ns3::TcpSocketDerivedV2")
                          .SetParent<TcpSocketBase>()
                          .SetGroupName("Internet")
                          .AddConstructor<TcpSocketDerivedV2>();
  return tid;
}

TypeId TcpSocketDerivedV2::GetInstanceTypeId() const {
  return TcpSocketDerivedV2::GetTypeId();
}

TcpSocketDerivedV2::TcpSocketDerivedV2(void) {}

Ptr<TcpCongestionOps> TcpSocketDerivedV2::GetCongestionControlAlgorithm() {
  return m_congestionControl;
}

TcpSocketDerivedV2::~TcpSocketDerivedV2(void) {}

NS_LOG_COMPONENT_DEFINE("ns3::TcpRlBaseV2");
NS_OBJECT_ENSURE_REGISTERED(TcpRlBaseV2);

TypeId TcpRlBaseV2::GetTypeId(void) {
  static TypeId tid = TypeId("ns3::TcpRlBaseV2")
                          .SetParent<TcpCongestionOps>()
                          .SetGroupName("Internet")
                          .AddConstructor<TcpRlBaseV2>();
  return tid;
}

TcpRlBaseV2::TcpRlBaseV2(void) : TcpLinuxReno() {
  NS_LOG_FUNCTION(this);
  m_tcpSocket = 0;
  m_tcpGymEnv = 0;
}

TcpRlBaseV2::TcpRlBaseV2(const TcpRlBaseV2 &sock) : TcpLinuxReno(sock) {
  NS_LOG_FUNCTION(this);
  m_tcpSocket = 0;
  m_tcpGymEnv = 0;
}

TcpRlBaseV2::~TcpRlBaseV2(void) {
  m_tcpSocket = 0;
  m_tcpGymEnv = 0;
}

uint64_t TcpRlBaseV2::GenerateUuid() {
  static uint64_t uuid = 0;
  uuid++;
  return uuid;
}

void TcpRlBaseV2::CreateGymEnv() {
  NS_LOG_FUNCTION(this);
  // should never be called, only child classes: TcpRlV2 and TcpRlTimeBasedV2
}

void TcpRlBaseV2::ConnectSocketCallbacks() {
  NS_LOG_FUNCTION(this);

  bool foundSocket = false;
  for (NodeList::Iterator i = NodeList::Begin(); i != NodeList::End(); ++i) {
    Ptr<Node> node = *i;
    Ptr<TcpL4Protocol> tcp = node->GetObject<TcpL4Protocol>();

    ObjectVectorValue socketVec;
    tcp->GetAttribute("SocketList", socketVec);
    NS_LOG_DEBUG("Node: " << node->GetId()
                          << " TCP socket num: " << socketVec.GetN());

    uint32_t sockNum = socketVec.GetN();
    for (uint32_t j = 0; j < sockNum; j++) {
      Ptr<Object> sockObj = socketVec.Get(j);
      Ptr<TcpSocketBase> tcpSocket = DynamicCast<TcpSocketBase>(sockObj);
      NS_LOG_DEBUG("Node: " << node->GetId() << " TCP Socket: " << tcpSocket);
      if (!tcpSocket) {
        continue;
      }

      Ptr<TcpSocketDerivedV2> dtcpSocket =
          StaticCast<TcpSocketDerivedV2>(tcpSocket);
      Ptr<TcpCongestionOps> ca = dtcpSocket->GetCongestionControlAlgorithm();
      NS_LOG_DEBUG("CA name: " << ca->GetName());
      Ptr<TcpRlBaseV2> rlCa = DynamicCast<TcpRlBaseV2>(ca);
      if (rlCa == this) {
        NS_LOG_DEBUG("Found TcpRlV2 CA!");
        foundSocket = true;
        m_tcpSocket = tcpSocket;
        break;
      }
    }

    if (foundSocket) {
      break;
    }
  }

  NS_ASSERT_MSG(m_tcpSocket, "TCP socket was not found.");

  if (m_tcpSocket) {
    NS_LOG_DEBUG("Found TCP Socket: " << m_tcpSocket);
    m_tcpSocket->TraceConnectWithoutContext(
        "Tx", MakeCallback(&TcpGymEnv::TxPktTrace, m_tcpGymEnv));
    m_tcpSocket->TraceConnectWithoutContext(
        "Rx", MakeCallback(&TcpGymEnv::RxPktTrace, m_tcpGymEnv));
    NS_LOG_DEBUG("Connect socket callbacks "
                 << m_tcpSocket->GetNode()->GetId());
    m_tcpGymEnv->SetNodeId(m_tcpSocket->GetNode()->GetId());
  }
}

std::string TcpRlBaseV2::GetName() const { return "TcpRlBaseV2"; }

uint32_t TcpRlBaseV2::GetSsThresh(Ptr<const TcpSocketState> state,
                                  uint32_t bytesInFlight) {
  NS_LOG_FUNCTION(this << state << bytesInFlight);

  if (!m_tcpGymEnv) {
    CreateGymEnv();
  }

  uint32_t newSsThresh = 0;
  if (m_tcpGymEnv) {
    newSsThresh = m_tcpGymEnv->GetSsThresh(state, bytesInFlight);
  }

  return newSsThresh;
}

void TcpRlBaseV2::IncreaseWindow(Ptr<TcpSocketState> tcb,
                                 uint32_t segmentsAcked) {
  NS_LOG_FUNCTION(this << tcb << segmentsAcked);

  if (!m_tcpGymEnv) {
    CreateGymEnv();
  }

  if (m_tcpGymEnv) {
    m_tcpGymEnv->IncreaseWindow(tcb, segmentsAcked);
  }
}

void TcpRlBaseV2::PktsAcked(Ptr<TcpSocketState> tcb, uint32_t segmentsAcked,
                            const Time &rtt) {
  NS_LOG_FUNCTION(this);

  if (!m_tcpGymEnv) {
    CreateGymEnv();
  }

  if (m_tcpGymEnv) {
    m_tcpGymEnv->PktsAcked(tcb, segmentsAcked, rtt);
  }
}

void TcpRlBaseV2::CongestionStateSet(
    Ptr<TcpSocketState> tcb, const TcpSocketState::TcpCongState_t newState) {
  NS_LOG_FUNCTION(this);

  if (!m_tcpGymEnv) {
    CreateGymEnv();
  }

  if (m_tcpGymEnv) {
    m_tcpGymEnv->CongestionStateSet(tcb, newState);
  }
}

void TcpRlBaseV2::CwndEvent(Ptr<TcpSocketState> tcb,
                            const TcpSocketState::TcpCAEvent_t event) {
  NS_LOG_FUNCTION(this);

  if (!m_tcpGymEnv) {
    CreateGymEnv();
  }

  if (m_tcpGymEnv) {
    m_tcpGymEnv->CwndEvent(tcb, event);
  }
}

Ptr<TcpCongestionOps> TcpRlBaseV2::Fork() {
  return CopyObject<TcpRlBaseV2>(this);
}

NS_OBJECT_ENSURE_REGISTERED(TcpRlV2);

TypeId TcpRlV2::GetTypeId(void) {
  static TypeId tid =
      TypeId("ns3::TcpRlV2")
          .SetParent<TcpRlBaseV2>()
          .SetGroupName("Internet")
          .AddConstructor<TcpRlV2>()
          .AddAttribute("Reward", "Reward when increasing congestion window.",
                        DoubleValue(1.0),
                        MakeDoubleAccessor(&TcpRlV2::m_reward),
                        MakeDoubleChecker<double>())
          .AddAttribute("Penalty", "Reward when increasing congestion window.",
                        DoubleValue(-10.0),
                        MakeDoubleAccessor(&TcpRlV2::m_penalty),
                        MakeDoubleChecker<double>());
  return tid;
}

TcpRlV2::TcpRlV2(void) : TcpRlBaseV2() { NS_LOG_FUNCTION(this); }

TcpRlV2::TcpRlV2(const TcpRlV2 &sock) : TcpRlBaseV2(sock) {
  NS_LOG_FUNCTION(this);
}

TcpRlV2::~TcpRlV2(void) {}

std::string TcpRlV2::GetName() const { return "TcpRlV2"; }

void TcpRlV2::CreateGymEnv() {
  NS_LOG_FUNCTION(this);
  Ptr<TcpEventGymEnv> env = CreateObject<TcpEventGymEnv>();
  env->SetSocketUuid(TcpRlBaseV2::GenerateUuid());
  env->SetReward(m_reward);
  env->SetPenalty(m_penalty);
  m_tcpGymEnv = env;

  ConnectSocketCallbacks();
}

NS_OBJECT_ENSURE_REGISTERED(TcpRlTimeBasedV2);

TypeId TcpRlTimeBasedV2::GetTypeId(void) {
  static TypeId tid =
      TypeId("ns3::TcpRlTimeBasedV2")
          .SetParent<TcpRlBaseV2>()
          .SetGroupName("Internet")
          .AddConstructor<TcpRlTimeBasedV2>()
          .AddAttribute("StepTime",
                        "Step interval used in TCP env. Default: 100ms",
                        TimeValue(MilliSeconds(100)),
                        MakeTimeAccessor(&TcpRlTimeBasedV2::m_timeStep),
                        MakeTimeChecker());
  return tid;
}

TcpRlTimeBasedV2::TcpRlTimeBasedV2(void) : TcpRlBaseV2() {
  NS_LOG_FUNCTION(this);
}

TcpRlTimeBasedV2::TcpRlTimeBasedV2(const TcpRlTimeBasedV2 &sock)
    : TcpRlBaseV2(sock) {
  NS_LOG_FUNCTION(this);
}

TcpRlTimeBasedV2::~TcpRlTimeBasedV2(void) {}

std::string TcpRlTimeBasedV2::GetName() const { return "TcpRlTimeBasedV2"; }

void TcpRlTimeBasedV2::CreateGymEnv() {
  NS_LOG_FUNCTION(this);
  Ptr<TcpTimeStepGymEnv> env = CreateObject<TcpTimeStepGymEnv>(m_timeStep);
  env->SetSocketUuid(TcpRlBaseV2::GenerateUuid());
  m_tcpGymEnv = env;

  ConnectSocketCallbacks();
}

} // namespace ns3
