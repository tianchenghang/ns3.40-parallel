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
 * Authors: Joe Kopena <tjkopena@cs.drexel.edu>
 */

#include "timestamp-tag.h"

#include "ns3/nstime.h"
#include "ns3/tag-buffer.h"
#include "ns3/tag.h"
#include "ns3/type-id.h"
#include "ns3/uinteger.h"

namespace ns3 {

NS_OBJECT_ENSURE_REGISTERED(TimestampTag);

TimestampTag::TimestampTag() = default;

TimestampTag::TimestampTag(Time timestamp) : m_timestamp(timestamp) {}

TypeId TimestampTag::GetTypeId() {
  static TypeId tid = TypeId("ns3::TimestampTag")
                          .SetParent<Tag>()
                          .SetGroupName("Network")
                          .AddConstructor<TimestampTag>();
  return tid;
}

TypeId TimestampTag::GetInstanceTypeId() const { return GetTypeId(); }

uint32_t TimestampTag::GetSerializedSize() const { return 8; }

void TimestampTag::Serialize(TagBuffer i) const {
  i.WriteU64(m_timestamp.GetTimeStep());
}

void TimestampTag::Deserialize(TagBuffer i) {
  m_timestamp = TimeStep(i.ReadU64());
}

void TimestampTag::Print(std::ostream &os) const {
  os << "timestamp=" << m_timestamp.As(Time::S);
}

Time TimestampTag::GetTimestamp() const { return m_timestamp; }

void TimestampTag::SetTimestamp(Time timestamp) { m_timestamp = timestamp; }

} // namespace ns3
