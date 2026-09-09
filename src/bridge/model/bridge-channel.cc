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

/*
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
 * Author: Gustavo Carneiro  <gjc@inescporto.pt>
 */

#include "bridge-channel.h"

#include "ns3/log.h"

/**
 * \file
 * \ingroup bridge
 * ns3::BridgeChannel implementation.
 */

namespace ns3 {

NS_LOG_COMPONENT_DEFINE("BridgeChannel");

NS_OBJECT_ENSURE_REGISTERED(BridgeChannel);

TypeId BridgeChannel::GetTypeId() {
  static TypeId tid = TypeId("ns3::BridgeChannel")
                          .SetParent<Channel>()
                          .SetGroupName("Bridge")
                          .AddConstructor<BridgeChannel>();
  return tid;
}

BridgeChannel::BridgeChannel() : Channel() { NS_LOG_FUNCTION_NOARGS(); }

BridgeChannel::~BridgeChannel() {
  NS_LOG_FUNCTION_NOARGS();

  for (auto iter = m_bridgedChannels.begin(); iter != m_bridgedChannels.end();
       iter++) {
    *iter = nullptr;
  }
  m_bridgedChannels.clear();
}

void BridgeChannel::AddChannel(Ptr<Channel> bridgedChannel) {
  m_bridgedChannels.push_back(bridgedChannel);
}

std::size_t BridgeChannel::GetNDevices() const {
  uint32_t ndevices = 0;
  for (auto iter = m_bridgedChannels.begin(); iter != m_bridgedChannels.end();
       iter++) {
    ndevices += (*iter)->GetNDevices();
  }
  return ndevices;
}

Ptr<NetDevice> BridgeChannel::GetDevice(std::size_t i) const {
  std::size_t ndevices = 0;
  for (auto iter = m_bridgedChannels.begin(); iter != m_bridgedChannels.end();
       iter++) {
    if ((i - ndevices) < (*iter)->GetNDevices()) {
      return (*iter)->GetDevice(i - ndevices);
    }
    ndevices += (*iter)->GetNDevices();
  }
  return nullptr;
}

} // namespace ns3
