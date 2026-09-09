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
 * Authors: Joe Kopena <tjkopena@cs.drexel.edu>
 */

#ifndef TIMESTAMP_TAG_H
#define TIMESTAMP_TAG_H

#include "ns3/nstime.h"
#include "ns3/tag-buffer.h"
#include "ns3/tag.h"
#include "ns3/type-id.h"

#include <iostream>

namespace ns3 {

/**
 * Timestamp tag for associating a timestamp with a packet.
 *
 * It would have been more realistic to include this info in
 * a header. Here we show how to avoid the extra overhead in
 * a simulation.
 */
class TimestampTag : public Tag {
public:
  /**
   * \brief Get the type ID.
   * \return the object TypeId
   */
  static TypeId GetTypeId();
  TypeId GetInstanceTypeId() const override;

  /**
   * \brief Construct a new TimestampTag object
   */
  TimestampTag();

  /**
   * \brief Construct a new TimestampTag object with the given timestamp
   * \param timestamp The timestamp
   */
  TimestampTag(Time timestamp);

  void Serialize(TagBuffer i) const override;
  void Deserialize(TagBuffer i) override;
  uint32_t GetSerializedSize() const override;
  void Print(std::ostream &os) const override;

  /**
   * \brief Get the Timestamp object
   * \return Time for this tag
   */
  Time GetTimestamp() const;

  /**
   * \brief Set the Timestamp object
   * \param timestamp Timestamp to assign to tag
   */
  void SetTimestamp(Time timestamp);

private:
  Time m_timestamp{0}; //!< Timestamp
};

} // namespace ns3

#endif // TIMESTAMP_TAG_H
