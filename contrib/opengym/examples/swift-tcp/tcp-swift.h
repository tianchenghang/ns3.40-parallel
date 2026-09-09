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
#ifndef TCP_SWIFT_H
#define TCP_SWIFT_H

#include "../rl-tcp/tcp-rl.h" // Inherit base logic from RL example
#include "tcp-swift-env.h"

namespace ns3 {

class TcpSwift : public TcpRlBase {
public:
  static TypeId GetTypeId(void);

  TcpSwift();
  TcpSwift(const TcpSwift &sock);
  ~TcpSwift();

  virtual std::string GetName() const;
  virtual Ptr<TcpCongestionOps> Fork();

private:
  virtual void CreateGymEnv();
};

} // namespace ns3

#endif /* TCP_SWIFT_H */
