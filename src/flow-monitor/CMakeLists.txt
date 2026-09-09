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

build_lib(
  LIBNAME flow-monitor
  SOURCE_FILES
    helper/flow-monitor-helper.cc
    model/flow-classifier.cc
    model/flow-monitor.cc
    model/flow-probe.cc
    model/ipv4-flow-classifier.cc
    model/ipv4-flow-probe.cc
    model/ipv6-flow-classifier.cc
    model/ipv6-flow-probe.cc
  HEADER_FILES
    helper/flow-monitor-helper.h
    model/flow-classifier.h
    model/flow-monitor.h
    model/flow-probe.h
    model/ipv4-flow-classifier.h
    model/ipv4-flow-probe.h
    model/ipv6-flow-classifier.h
    model/ipv6-flow-probe.h
  LIBRARIES_TO_LINK ${libinternet}
                    ${libstats}
)
