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
 * Author: George Riley <riley@ece.gatech.edu>
 */

/**
 * \file
 * \ingroup mpi
 * ns3::MpiReceiver implementation,
 * provides an interface to aggregate to MPI-compatible NetDevices.
 */

#include "mpi-receiver.h"

namespace ns3 {

TypeId MpiReceiver::GetTypeId() {
  static TypeId tid = TypeId("ns3::MpiReceiver")
                          .SetParent<Object>()
                          .SetGroupName("Mpi")
                          .AddConstructor<MpiReceiver>();
  return tid;
}

MpiReceiver::~MpiReceiver() {}

void MpiReceiver::SetReceiveCallback(Callback<void, Ptr<Packet>> callback) {
  m_rxCallback = callback;
}

void MpiReceiver::Receive(Ptr<Packet> p) {
  NS_ASSERT(!m_rxCallback.IsNull());
  m_rxCallback(p);
}

void MpiReceiver::DoDispose() {
  m_rxCallback = MakeNullCallback<void, Ptr<Packet>>();
}

} // namespace ns3
