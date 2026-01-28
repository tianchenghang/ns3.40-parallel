/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
#include "tcp-gemini-env.h"

#include "ns3/log.h"
#include "ns3/simulator.h"

namespace ns3 {

NS_LOG_COMPONENT_DEFINE("ns3::TcpGeminiEnv");
NS_OBJECT_ENSURE_REGISTERED(TcpGeminiEnv);

TcpGeminiEnv::TcpGeminiEnv()
    : TcpGymEnv(), m_calledFunc(CalledFunc_t::INCREASE_WINDOW),
      m_bytesInFlight(0), m_segmentsAcked(0), m_rtt(Time(0)),
      m_caEvent(TcpSocketState::CA_EVENT_TX_START), m_ecnCeCounter(0),
      m_ecnCongestionDetected(false), m_lastEcnTime(Time(0)),
      m_totalBytesAcked(0), m_lastAckTime(Time(0)) {
  NS_LOG_FUNCTION(this);
}

TcpGeminiEnv::~TcpGeminiEnv() { NS_LOG_FUNCTION(this); }

TypeId TcpGeminiEnv::GetTypeId(void) {
  static TypeId tid = TypeId("ns3::TcpGeminiEnv")
                          .SetParent<TcpGymEnv>()
                          .SetGroupName("OpenGym")
                          .AddConstructor<TcpGeminiEnv>();
  return tid;
}

void TcpGeminiEnv::DoDispose() { NS_LOG_FUNCTION(this); }

Ptr<OpenGymSpace> TcpGeminiEnv::GetObservationSpace() {
  // 15 parameters for comprehensive RL observation:
  // [0]uuid, [1]type, [2]time, [3]nodeId, [4]ssThresh, [5]cwnd
  // [6]segSize, [7]acked, [8]flight, [9]rtt, [10]minRtt, [11]func,
  // [12-14]states
  uint32_t parameterNum = 15;
  float low = 0.0;
  float high = 1000000000.0;
  std::vector<uint32_t> shape = {parameterNum};
  std::string dtype = TypeNameGet<uint64_t>();
  Ptr<OpenGymBoxSpace> box =
      CreateObject<OpenGymBoxSpace>(low, high, shape, dtype);
  return box;
}

Ptr<OpenGymDataContainer> TcpGeminiEnv::GetObservation() {
  uint32_t parameterNum = 15;
  std::vector<uint32_t> shape = {parameterNum};
  Ptr<OpenGymBoxContainer<uint64_t>> box =
      CreateObject<OpenGymBoxContainer<uint64_t>>(shape);

  // [0] Socket UUID - unique identifier for multi-flow scenarios
  box->AddValue(m_socketUuid);

  // [1] Env Type - 0 = Event-based (Gemini uses event-based)
  box->AddValue(0);

  // [2] Simulation Time in microseconds
  box->AddValue(Simulator::Now().GetMicroSeconds());

  // [3] Node ID
  box->AddValue(m_nodeId);

  // Guard against null m_tcb pointer
  if (!m_tcb) {
    // Return default values if m_tcb is not yet initialized
    for (uint32_t i = 4; i < parameterNum; i++) {
      box->AddValue(0);
    }
    return box;
  }

  // [4] ssThresh - Slow Start Threshold
  box->AddValue(m_tcb->m_ssThresh);

  // [5] cWnd - Current Congestion Window
  box->AddValue(m_tcb->m_cWnd);

  // [6] Segment Size
  box->AddValue(m_tcb->m_segmentSize);

  // [7] Segments Acked in this event
  box->AddValue(m_segmentsAcked);

  // [8] Bytes In Flight
  box->AddValue(m_bytesInFlight);

  // [9] Last RTT in microseconds
  box->AddValue(m_rtt.GetMicroSeconds());

  // [10] Minimum RTT in microseconds (baseline for BDP calculation)
  // Guard against uninitialized m_minRtt (Time::Max())
  if (m_tcb->m_minRtt == Time::Max()) {
    box->AddValue(0);
  } else {
    box->AddValue(m_tcb->m_minRtt.GetMicroSeconds());
  }

  // [11] Called Function: 0=GET_SS_THRESH (loss), 1=INCREASE_WINDOW (ack)
  box->AddValue(m_calledFunc);

  // [12] Congestion State: CA_OPEN=0, CA_DISORDER=1, CA_CWR=2, CA_RECOVERY=3,
  // CA_LOSS=4
  box->AddValue(m_tcb->m_congState);

  // [13] CA Event - includes ECN events:
  //      CA_EVENT_ECN_NO_CE=4, CA_EVENT_ECN_IS_CE=5
  box->AddValue(m_caEvent);

  // [14] ECN State: ECN_DISABLED=0, ECN_IDLE=1, ECN_CE_RCVD=2,
  //      ECN_SENDING_ECE=3, ECN_ECE_RCVD=4, ECN_CWR_SENT=5
  box->AddValue(static_cast<uint64_t>(m_tcb->m_ecnState));

  return box;
}

void TcpGeminiEnv::TxPktTrace(Ptr<const Packet>, const TcpHeader &,
                              Ptr<const TcpSocketBase>) {
  // Packet transmission trace - can be extended for detailed analysis
}

void TcpGeminiEnv::RxPktTrace(Ptr<const Packet>, const TcpHeader &,
                              Ptr<const TcpSocketBase>) {
  // Could track received packets for more detailed analysis
}

uint32_t TcpGeminiEnv::GetSsThresh(Ptr<const TcpSocketState> tcb,
                                   uint32_t bytesInFlight) {
  NS_LOG_FUNCTION(this << bytesInFlight);

  if (!tcb) {
    NS_LOG_WARN("GetSsThresh called with null tcb");
    return bytesInFlight / 2;
  }

  m_calledFunc = CalledFunc_t::GET_SS_THRESH; // Loss Event
  m_tcb = tcb;
  m_bytesInFlight = bytesInFlight;
  m_segmentsAcked = 0;
  m_rtt = Time(0);

  // Default to current values in case no valid action is received
  m_new_ssThresh = tcb->m_ssThresh;
  m_new_cWnd = tcb->m_cWnd;

  // Check if this is ECN-triggered or actual packet loss
  // ECN CE received triggers CWR state before GetSsThresh
  if (tcb->m_ecnState == TcpSocketState::ECN_CE_RCVD ||
      tcb->m_ecnState == TcpSocketState::ECN_ECE_RCVD) {
    m_ecnCongestionDetected = true;
    m_ecnCeCounter++;
    m_lastEcnTime = Simulator::Now();
    NS_LOG_INFO("ECN-triggered ssThresh reduction at " << Simulator::Now());
  }

  // Set reward based on loss type
  if (m_ecnCongestionDetected) {
    // ECN-based loss is less severe (proactive congestion signal)
    m_envReward = -5.0;
    m_ecnCongestionDetected = false;
  } else {
    // Actual packet loss - more severe penalty
    m_envReward = -15.0;
  }

  Notify(); // Trigger Python agent
  return m_new_ssThresh;
}

void TcpGeminiEnv::IncreaseWindow(Ptr<TcpSocketState> tcb,
                                  uint32_t segmentsAcked) {
  NS_LOG_FUNCTION(this << segmentsAcked);

  if (!tcb) {
    NS_LOG_WARN("IncreaseWindow called with null tcb");
    return;
  }

  m_calledFunc = CalledFunc_t::INCREASE_WINDOW;
  m_tcb = tcb;
  m_segmentsAcked = segmentsAcked;
  m_bytesInFlight = tcb->m_bytesInFlight;
  m_totalBytesAcked += segmentsAcked * tcb->m_segmentSize;

  // Default to current values in case no valid action is received
  m_new_ssThresh = tcb->m_ssThresh;
  m_new_cWnd = tcb->m_cWnd;

  // Calculate reward based on throughput progress
  // Higher reward for more segments acked (throughput optimization)
  float throughputBonus = static_cast<float>(segmentsAcked) * 0.5;

  // Penalize if RTT is inflating (queue building up)
  float rttPenalty = 0.0;
  if (m_rtt > Time(0) && tcb->m_minRtt > Time(0) &&
      tcb->m_minRtt != Time::Max()) {
    double rttRatio = m_rtt.GetDouble() / tcb->m_minRtt.GetDouble();
    if (rttRatio > 1.5) {
      rttPenalty = (rttRatio - 1.0) * 2.0;
    }
  }

  m_envReward = throughputBonus - rttPenalty;
  m_lastAckTime = Simulator::Now();

  Notify();
  tcb->m_cWnd = m_new_cWnd;
}

void TcpGeminiEnv::PktsAcked(Ptr<TcpSocketState> tcb, uint32_t segmentsAcked,
                             const Time &rtt) {
  NS_LOG_FUNCTION(this << segmentsAcked << rtt);

  if (!tcb) {
    NS_LOG_WARN("PktsAcked called with null tcb");
    return;
  }

  m_tcb = tcb;
  m_segmentsAcked = segmentsAcked;
  m_rtt = rtt;
}

void TcpGeminiEnv::CongestionStateSet(
    Ptr<TcpSocketState> tcb, const TcpSocketState::TcpCongState_t newState) {
  NS_LOG_FUNCTION(this << newState);

  if (!tcb) {
    NS_LOG_WARN("CongestionStateSet called with null tcb");
    return;
  }

  m_tcb = tcb;

  // Track ECN-related state transitions
  if (newState == TcpSocketState::CA_CWR) {
    // Congestion Window Reduced state - typically ECN triggered
    NS_LOG_INFO("Entering CWR state (ECN response) at " << Simulator::Now());
  }
}

void TcpGeminiEnv::CwndEvent(Ptr<TcpSocketState> tcb,
                             const TcpSocketState::TcpCAEvent_t event) {
  NS_LOG_FUNCTION(this << event);

  if (!tcb) {
    NS_LOG_WARN("CwndEvent called with null tcb");
    return;
  }

  m_tcb = tcb;
  m_caEvent = event;

  // Enhanced ECN event handling
  switch (event) {
  case TcpSocketState::CA_EVENT_ECN_IS_CE:
    // ECN Congestion Experienced mark received
    m_ecnCeCounter++;
    m_ecnCongestionDetected = true;
    m_lastEcnTime = Simulator::Now();
    NS_LOG_INFO("ECN CE mark detected at " << Simulator::Now());
    break;

  case TcpSocketState::CA_EVENT_ECN_NO_CE:
    // No congestion experienced - network is clear
    m_ecnCongestionDetected = false;
    break;

  case TcpSocketState::CA_EVENT_COMPLETE_CWR:
    // CWR phase completed
    NS_LOG_INFO("CWR complete at " << Simulator::Now());
    break;

  case TcpSocketState::CA_EVENT_LOSS:
    // Explicit loss event
    NS_LOG_INFO("Loss event at " << Simulator::Now());
    break;

  default:
    break;
  }
}

} // namespace ns3
