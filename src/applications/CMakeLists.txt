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
  LIBNAME applications
  SOURCE_FILES
    helper/bulk-send-helper.cc
    helper/on-off-helper.cc
    helper/packet-sink-helper.cc
    helper/three-gpp-http-helper.cc
    helper/udp-client-server-helper.cc
    helper/udp-echo-helper.cc
    model/application-packet-probe.cc
    model/bulk-send-application.cc
    model/onoff-application.cc
    model/packet-loss-counter.cc
    model/packet-sink.cc
    model/seq-ts-echo-header.cc
    model/seq-ts-header.cc
    model/seq-ts-size-header.cc
    model/three-gpp-http-client.cc
    model/three-gpp-http-header.cc
    model/three-gpp-http-server.cc
    model/three-gpp-http-variables.cc
    model/udp-client.cc
    model/udp-echo-client.cc
    model/udp-echo-server.cc
    model/udp-server.cc
    model/udp-trace-client.cc
  HEADER_FILES
    helper/bulk-send-helper.h
    helper/on-off-helper.h
    helper/packet-sink-helper.h
    helper/three-gpp-http-helper.h
    helper/udp-client-server-helper.h
    helper/udp-echo-helper.h
    model/application-packet-probe.h
    model/bulk-send-application.h
    model/onoff-application.h
    model/packet-loss-counter.h
    model/packet-sink.h
    model/seq-ts-echo-header.h
    model/seq-ts-header.h
    model/seq-ts-size-header.h
    model/three-gpp-http-client.h
    model/three-gpp-http-header.h
    model/three-gpp-http-server.h
    model/three-gpp-http-variables.h
    model/udp-client.h
    model/udp-echo-client.h
    model/udp-echo-server.h
    model/udp-server.h
    model/udp-trace-client.h
  LIBRARIES_TO_LINK ${libinternet}
                    ${libstats}
  TEST_SOURCES
    test/three-gpp-http-client-server-test.cc
    test/bulk-send-application-test-suite.cc
    test/udp-client-server-test.cc
)
