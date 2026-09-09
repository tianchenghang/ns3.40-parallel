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
 * Authors: Pavel Boyko <boyko@iitp.ru>
 */

#ifndef BUG780_TEST_H
#define BUG780_TEST_H

#include "ns3/node-container.h"
#include "ns3/nstime.h"
#include "ns3/ptr.h"
#include "ns3/test.h"

namespace ns3 {

class Socket;

namespace olsr {

/**
 * \ingroup olsr-test
 * \ingroup tests
 *
 * See \bugid{780}
 */
class Bug780Test : public TestCase {
public:
  Bug780Test();
  ~Bug780Test() override;

private:
  /// Total simulation time
  const Time m_time;
  /// Create & configure test network
  void CreateNodes();
  void DoRun() override;
  /// Send one ping
  void SendPing();
  /**
   * Receive echo reply
   * \param socket the socket
   */
  void Receive(Ptr<Socket> socket);
  /// Socket
  Ptr<Socket> m_socket;
  /// Sequence number
  uint16_t m_seq;
  /// Received ECHO Reply counter
  uint16_t m_recvCount;
};

} // namespace olsr
} // namespace ns3

#endif /* BUG780_TEST_H */
