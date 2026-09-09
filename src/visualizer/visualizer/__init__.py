# Copyright 2026 hangtiancheng
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from ns import *

# Some useful tricks for visualizer
# we need to check if the node has a mobility model, but we can't pass Ptr<MobilityModel> to python
ns.cppyy.cppdef(
    """using namespace ns3; bool hasMobilityModel(Ptr<Node> node){ return !(node->GetObject<MobilityModel>() == 0); };"""
)
ns.cppyy.cppdef(
    """using namespace ns3; Vector3D getNodePosition(Ptr<Node> node){ return node->GetObject<MobilityModel>()->GetPosition(); };"""
)
ns.cppyy.cppdef(
    """using namespace ns3; Ptr<Ipv4> getNodeIpv4(Ptr<Node> node){ return node->GetObject<Ipv4>(); };"""
)
ns.cppyy.cppdef(
    """using namespace ns3; Ptr<Ipv6> getNodeIpv6(Ptr<Node> node){ return node->GetObject<Ipv6>(); };"""
)
ns.cppyy.cppdef(
    """using namespace ns3; std::string getMobilityModelName(Ptr<Node> node){ return node->GetObject<MobilityModel>()->GetInstanceTypeId().GetName(); };"""
)
ns.cppyy.cppdef(
    """using namespace ns3; bool hasOlsr(Ptr<Node> node){ return !(node->GetObject<olsr::RoutingProtocol>() == 0); };"""
)
ns.cppyy.cppdef(
    """using namespace ns3; Ptr<olsr::RoutingProtocol> getNodeOlsr(Ptr<Node> node){ return node->GetObject<olsr::RoutingProtocol>(); };"""
)


from .core import start, register_plugin, set_bounds, add_initialization_hook
