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
  LIBNAME internet-apps
  SOURCE_FILES
    helper/dhcp-helper.cc
    helper/ping-helper.cc
    helper/ping6-helper.cc
    helper/radvd-helper.cc
    helper/v4ping-helper.cc
    helper/v4traceroute-helper.cc
    model/dhcp-client.cc
    model/dhcp-header.cc
    model/dhcp-server.cc
    model/ping.cc
    model/ping6.cc
    model/radvd-interface.cc
    model/radvd-prefix.cc
    model/radvd.cc
    model/v4ping.cc
    model/v4traceroute.cc
  HEADER_FILES
    helper/dhcp-helper.h
    helper/ping-helper.h
    helper/ping6-helper.h
    helper/radvd-helper.h
    helper/v4ping-helper.h
    helper/v4traceroute-helper.h
    model/dhcp-client.h
    model/dhcp-header.h
    model/dhcp-server.h
    model/ping.h
    model/ping6.h
    model/radvd-interface.h
    model/radvd-prefix.h
    model/radvd.h
    model/v4ping.h
    model/v4traceroute.h
  LIBRARIES_TO_LINK ${libinternet}
  TEST_SOURCES
    test/dhcp-test.cc
    test/ipv6-radvd-test.cc
    test/ping-test.cc
)
