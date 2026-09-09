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
  LIBNAME aodv
  SOURCE_FILES
    helper/aodv-helper.cc
    model/aodv-dpd.cc
    model/aodv-id-cache.cc
    model/aodv-neighbor.cc
    model/aodv-packet.cc
    model/aodv-routing-protocol.cc
    model/aodv-rqueue.cc
    model/aodv-rtable.cc
  HEADER_FILES
    helper/aodv-helper.h
    model/aodv-dpd.h
    model/aodv-id-cache.h
    model/aodv-neighbor.h
    model/aodv-packet.h
    model/aodv-routing-protocol.h
    model/aodv-rqueue.h
    model/aodv-rtable.h
  LIBRARIES_TO_LINK ${libinternet}
                    ${libwifi}
  TEST_SOURCES
    test/aodv-id-cache-test-suite.cc
    test/aodv-regression.cc
    test/aodv-test-suite.cc
    test/loopback.cc
    test/bug-772.cc
)
