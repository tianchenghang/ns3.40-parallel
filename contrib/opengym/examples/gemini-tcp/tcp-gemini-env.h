/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
#ifndef TCP_GEMINI_ENV_H
#define TCP_GEMINI_ENV_H

#include "../rl-tcp/tcp-rl-env.h" // Inherit basic structures

#include "ns3/opengym-module.h"
#include "ns3/tcp-socket-base.h"

namespace ns3
{

class TcpGeminiEnv : public TcpGymEnv
{
  public:
    TcpGeminiEnv();
    virtual ~TcpGeminiEnv();
    static TypeId GetTypeId(void);
    virtual void DoDispose();

    // OpenGym interface
    virtual Ptr<OpenGymSpace> GetObservationSpace();
    Ptr<OpenGymDataContainer> GetObservation();

    // Callbacks
    virtual void TxPktTrace(Ptr<const Packet>, const TcpHeader&, Ptr<const TcpSocketBase>);
    virtual void RxPktTrace(Ptr<const Packet>, const TcpHeader&, Ptr<const TcpSocketBase>);

    // Congestion Control Interface
    virtual uint32_t GetSsThresh(Ptr<const TcpSocketState> tcb, uint32_t bytesInFlight);
    virtual void IncreaseWindow(Ptr<TcpSocketState> tcb, uint32_t segmentsAcked);

    // Optional functions used to collect obs
    virtual void PktsAcked(Ptr<TcpSocketState> tcb, uint32_t segmentsAcked, const Time& rtt);
    virtual void CongestionStateSet(Ptr<TcpSocketState> tcb,
                                    const TcpSocketState::TcpCongState_t newState);
    virtual void CwndEvent(Ptr<TcpSocketState> tcb, const TcpSocketState::TcpCAEvent_t event);

  private:
    CalledFunc_t m_calledFunc;
    Ptr<const TcpSocketState> m_tcb;
    uint32_t m_bytesInFlight;
    uint32_t m_segmentsAcked;
    Time m_rtt;
    TcpSocketState::TcpCAEvent_t m_caEvent;

    // Gemini needs detailed stats, passing standard metrics allows Python to compute BDP/Rates
};

} // namespace ns3

#endif /* TCP_GEMINI_ENV_H */
