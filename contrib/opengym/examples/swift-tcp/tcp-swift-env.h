/*
 * Copyright 2026 hangtiancheng
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
#ifndef TCP_SWIFT_ENV_H
#define TCP_SWIFT_ENV_H

#include "../rl-tcp/tcp-rl-env.h" // Inherit basic structures

#include "ns3/opengym-module.h"
#include "ns3/tcp-socket-base.h"

namespace ns3 {

class TcpSwiftEnv : public TcpGymEnv {
public:
  TcpSwiftEnv();
  virtual ~TcpSwiftEnv();
  static TypeId GetTypeId(void);
  virtual void DoDispose();

  // OpenGym interface
  virtual Ptr<OpenGymSpace> GetObservationSpace();
  Ptr<OpenGymDataContainer> GetObservation();

  // Callbacks
  virtual void TxPktTrace(Ptr<const Packet>, const TcpHeader &,
                          Ptr<const TcpSocketBase>);
  virtual void RxPktTrace(Ptr<const Packet>, const TcpHeader &,
                          Ptr<const TcpSocketBase>);

  // Congestion Control Interface
  virtual uint32_t GetSsThresh(Ptr<const TcpSocketState> tcb,
                               uint32_t bytesInFlight);
  virtual void IncreaseWindow(Ptr<TcpSocketState> tcb, uint32_t segmentsAcked);

  // Optional functions used to collect obs
  virtual void PktsAcked(Ptr<TcpSocketState> tcb, uint32_t segmentsAcked,
                         const Time &rtt);
  virtual void
  CongestionStateSet(Ptr<TcpSocketState> tcb,
                     const TcpSocketState::TcpCongState_t newState);
  virtual void CwndEvent(Ptr<TcpSocketState> tcb,
                         const TcpSocketState::TcpCAEvent_t event);

private:
  // Core state
  CalledFunc_t m_calledFunc;
  Ptr<const TcpSocketState> m_tcb;
  uint32_t m_bytesInFlight;
  uint32_t m_segmentsAcked;
  Time m_rtt;
  TcpSocketState::TcpCAEvent_t m_caEvent;

  // ECN Enhanced Support
  uint32_t m_ecnCeCounter;      // Count of ECN CE marks received
  bool m_ecnCongestionDetected; // Flag for ECN-based congestion detection
  Time m_lastEcnTime;           // Time of last ECN event

  // Additional metrics for RL optimization
  uint64_t m_totalBytesAcked; // Cumulative bytes acked
  Time m_lastAckTime;         // Time of last ACK for inter-ACK calculation

  // Deferred cwnd from GetSsThresh (const tcb cannot be modified directly)
  bool m_hasPendingCwnd;  // Whether a deferred cwnd is pending
  uint32_t m_pendingCwnd; // The deferred cwnd value from Python
};

} // namespace ns3

#endif /* TCP_SWIFT_ENV_H */
