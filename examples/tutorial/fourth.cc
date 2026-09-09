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
 */

#include "ns3/object.h"
#include "ns3/simulator.h"
#include "ns3/trace-source-accessor.h"
#include "ns3/traced-value.h"
#include "ns3/uinteger.h"

#include <iostream>

using namespace ns3;

/**
 * Tutorial 4 - a simple Object to show how to hook a trace.
 */
class MyObject : public Object {
public:
  /**
   * Register this type.
   * \return The TypeId.
   */
  static TypeId GetTypeId() {
    static TypeId tid =
        TypeId("MyObject")
            .SetParent<Object>()
            .SetGroupName("Tutorial")
            .AddConstructor<MyObject>()
            .AddTraceSource("MyInteger", "An integer value to trace.",
                            MakeTraceSourceAccessor(&MyObject::m_myInt),
                            "ns3::TracedValueCallback::Int32");
    return tid;
  }

  MyObject() {}

  TracedValue<int32_t> m_myInt; //!< The traced value.
};

void IntTrace(int32_t oldValue, int32_t newValue) {
  std::cout << "Traced " << oldValue << " to " << newValue << std::endl;
}

int main(int argc, char *argv[]) {
  Ptr<MyObject> myObject = CreateObject<MyObject>();
  myObject->TraceConnectWithoutContext("MyInteger", MakeCallback(&IntTrace));

  myObject->m_myInt = 1234;

  return 0;
}
