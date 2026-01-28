/* -*-  Mode: C++; c-file-style: "gnu"; indent-tabs-mode:nil; -*- */
#ifndef TCP_GEMINI_H
#define TCP_GEMINI_H

#include "../rl-tcp/tcp-rl.h" // Inherit base logic from RL example
#include "tcp-gemini-env.h"

namespace ns3 {

class TcpGemini : public TcpRlBase {
public:
  static TypeId GetTypeId(void);

  TcpGemini();
  TcpGemini(const TcpGemini &sock);
  ~TcpGemini();

  virtual std::string GetName() const;
  virtual Ptr<TcpCongestionOps> Fork();

private:
  virtual void CreateGymEnv();
};

} // namespace ns3

#endif /* TCP_GEMINI_H */
