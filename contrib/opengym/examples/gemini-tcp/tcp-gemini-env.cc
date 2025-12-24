/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
#include "tcp-gemini-env.h"

#include "ns3/log.h"
#include "ns3/simulator.h"

namespace ns3
{

NS_LOG_COMPONENT_DEFINE("ns3::TcpGeminiEnv");
NS_OBJECT_ENSURE_REGISTERED(TcpGeminiEnv);

TcpGeminiEnv::TcpGeminiEnv()
    : TcpGymEnv()
{
    NS_LOG_FUNCTION(this);
    m_caEvent = TcpSocketState::CA_EVENT_TX_START; // Default init
}

TcpGeminiEnv::~TcpGeminiEnv()
{
    NS_LOG_FUNCTION(this);
}

TypeId
TcpGeminiEnv::GetTypeId(void)
{
    static TypeId tid = TypeId("ns3::TcpGeminiEnv")
                            .SetParent<TcpGymEnv>()
                            .SetGroupName("OpenGym")
                            .AddConstructor<TcpGeminiEnv>();
    return tid;
}

void
TcpGeminiEnv::DoDispose()
{
    NS_LOG_FUNCTION(this);
}

Ptr<OpenGymSpace>
TcpGeminiEnv::GetObservationSpace()
{
    // Same 15 parameters as TcpEventGymEnv to support the Python parsing
    // [0]uuid, [1]type, [2]time, [3]nodeId, [4]ssThresh, [5]cwnd
    // [6]segSize, [7]acked, [8]flight, [9]rtt, [10]minRtt, [11]func, [12-14]states
    uint32_t parameterNum = 15;
    float low = 0.0;
    float high = 1000000000.0; // Large enough for bytes/time
    std::vector<uint32_t> shape = {
        parameterNum,
    };
    std::string dtype = TypeNameGet<uint64_t>();
    Ptr<OpenGymBoxSpace> box = CreateObject<OpenGymBoxSpace>(low, high, shape, dtype);
    return box;
}

Ptr<OpenGymDataContainer>
TcpGeminiEnv::GetObservation()
{
    // Populating the 15-element Observation vector
    uint32_t parameterNum = 15;
    std::vector<uint32_t> shape = {
        parameterNum,
    };
    Ptr<OpenGymBoxContainer<uint64_t>> box = CreateObject<OpenGymBoxContainer<uint64_t>>(shape);

    // [0]uuid, [1]type, [2]time, [3]nodeId
    box->AddValue(m_socketUuid);
    box->AddValue(0); // Event-based
    box->AddValue(Simulator::Now().GetMicroSeconds());
    box->AddValue(m_nodeId);

    // [4]ssThresh, [5]cwnd, [6]segSize, [7]acked, [8]flight, [9]rtt, [10]minRtt
    box->AddValue(m_tcb->m_ssThresh);
    box->AddValue(m_tcb->m_cWnd);
    box->AddValue(m_tcb->m_segmentSize);
    box->AddValue(m_segmentsAcked);
    box->AddValue(m_bytesInFlight);
    box->AddValue(m_rtt.GetMicroSeconds());
    box->AddValue(m_tcb->m_minRtt.GetMicroSeconds());

    // [11]calledFunc (0=Loss/GetSsThresh, 1=Ack/IncreaseWindow)
    box->AddValue(m_calledFunc);

    // [12] Congestion State
    box->AddValue(m_tcb->m_congState);

    // [13] CA Event (Captured from CwndEvent callback)
    box->AddValue(m_caEvent);

    // [14] ECN State (Crucial for ECN support)
    // TcpSocketState::EcnState_t is an enum, cast to uint
    box->AddValue(static_cast<uint64_t>(m_tcb->m_ecnState));

    return box;
}

void
TcpGeminiEnv::TxPktTrace(Ptr<const Packet>, const TcpHeader&, Ptr<const TcpSocketBase>)
{
}

void
TcpGeminiEnv::RxPktTrace(Ptr<const Packet>, const TcpHeader&, Ptr<const TcpSocketBase>)
{
}

uint32_t
TcpGeminiEnv::GetSsThresh(Ptr<const TcpSocketState> tcb, uint32_t bytesInFlight)
{
    m_calledFunc = CalledFunc_t::GET_SS_THRESH; // Loss Event
    m_tcb = tcb;
    m_bytesInFlight = bytesInFlight;
    m_segmentsAcked = 0;
    m_rtt = Time(0);
    Notify();              // Trigger Python
    return m_new_ssThresh; // Return new ssThresh from Python
}

void
TcpGeminiEnv::IncreaseWindow(Ptr<TcpSocketState> tcb, uint32_t segmentsAcked)
{
    m_calledFunc = CalledFunc_t::INCREASE_WINDOW;
    m_tcb = tcb;
    m_segmentsAcked = segmentsAcked;
    m_bytesInFlight = tcb->m_bytesInFlight;
    // m_rtt is set in PktsAcked, which is called before IncreaseWindow
    Notify();                 // Trigger Python
    tcb->m_cWnd = m_new_cWnd; // Apply new cWnd from Python
}

void
TcpGeminiEnv::PktsAcked(Ptr<TcpSocketState> tcb, uint32_t segmentsAcked, const Time& rtt)
{
    // Crucial for collecting RTT and segmentsAcked before IncreaseWindow is called
    m_tcb = tcb;
    m_segmentsAcked = segmentsAcked;
    m_rtt = rtt;
}

void
TcpGeminiEnv::CongestionStateSet(Ptr<TcpSocketState> tcb,
                                 const TcpSocketState::TcpCongState_t newState)
{
    m_tcb = tcb;
}

void
TcpGeminiEnv::CwndEvent(Ptr<TcpSocketState> tcb, const TcpSocketState::TcpCAEvent_t event)
{
    m_tcb = tcb;
    m_caEvent = event; // Capture the event for observation
}

} // namespace ns3
