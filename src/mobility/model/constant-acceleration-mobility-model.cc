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
#include "constant-acceleration-mobility-model.h"

#include "ns3/simulator.h"

namespace ns3 {

NS_OBJECT_ENSURE_REGISTERED(ConstantAccelerationMobilityModel);

TypeId ConstantAccelerationMobilityModel::GetTypeId() {
  static TypeId tid = TypeId("ns3::ConstantAccelerationMobilityModel")
                          .SetParent<MobilityModel>()
                          .SetGroupName("Mobility")
                          .AddConstructor<ConstantAccelerationMobilityModel>();
  return tid;
}

ConstantAccelerationMobilityModel::ConstantAccelerationMobilityModel() {}

ConstantAccelerationMobilityModel::~ConstantAccelerationMobilityModel() {}

inline Vector ConstantAccelerationMobilityModel::DoGetVelocity() const {
  double t = (Simulator::Now() - m_baseTime).GetSeconds();
  return Vector(m_baseVelocity.x + m_acceleration.x * t,
                m_baseVelocity.y + m_acceleration.y * t,
                m_baseVelocity.z + m_acceleration.z * t);
}

inline Vector ConstantAccelerationMobilityModel::DoGetPosition() const {
  double t = (Simulator::Now() - m_baseTime).GetSeconds();
  double half_t_square = t * t * 0.5;
  return Vector(m_basePosition.x + m_baseVelocity.x * t +
                    m_acceleration.x * half_t_square,
                m_basePosition.y + m_baseVelocity.y * t +
                    m_acceleration.y * half_t_square,
                m_basePosition.z + m_baseVelocity.z * t +
                    m_acceleration.z * half_t_square);
}

void ConstantAccelerationMobilityModel::DoSetPosition(const Vector &position) {
  m_baseVelocity = DoGetVelocity();
  m_baseTime = Simulator::Now();
  m_basePosition = position;
  NotifyCourseChange();
}

void ConstantAccelerationMobilityModel::SetVelocityAndAcceleration(
    const Vector &velocity, const Vector &acceleration) {
  m_basePosition = DoGetPosition();
  m_baseTime = Simulator::Now();
  m_baseVelocity = velocity;
  m_acceleration = acceleration;
  NotifyCourseChange();
}

} // namespace ns3
