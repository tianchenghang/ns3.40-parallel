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

# This is a stub module that loads the actual ns-3
# bindings from ns3.ns
import sys

try:
    import ns3.ns

    sys.modules["ns"] = ns3.ns
except ModuleNotFoundError as e:
    print("Install the ns3 package with pip install ns3.", file=sys.stderr)
    exit(-1)
