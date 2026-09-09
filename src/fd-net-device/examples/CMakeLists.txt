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

include_directories(${DPDK_INCLUDE_DIRS})

build_lib_example(
  NAME dummy-network
  SOURCE_FILES dummy-network.cc
  LIBRARIES_TO_LINK
    ${libfd-net-device}
    ${libinternet}
    ${libinternet-apps}
)

build_lib_example(
  NAME fd2fd-onoff
  SOURCE_FILES fd2fd-onoff.cc
  LIBRARIES_TO_LINK
    ${libfd-net-device}
    ${libinternet}
    ${libapplications}
)

build_lib_example(
  NAME realtime-dummy-network
  SOURCE_FILES realtime-dummy-network.cc
  LIBRARIES_TO_LINK
    ${libfd-net-device}
    ${libinternet}
    ${libapplications}
    ${libinternet-apps}
)

build_lib_example(
  NAME realtime-fd2fd-onoff
  SOURCE_FILES realtime-fd2fd-onoff.cc
  LIBRARIES_TO_LINK
    ${libfd-net-device}
    ${libinternet}
    ${libapplications}
)

if(${ENABLE_EMU})
  build_lib_example(
    NAME fd-emu-ping
    SOURCE_FILES fd-emu-ping.cc
    LIBRARIES_TO_LINK
      ${libfd-net-device}
      ${libinternet}
      ${libinternet-apps}
  )

  build_lib_example(
    NAME fd-emu-udp-echo
    SOURCE_FILES fd-emu-udp-echo.cc
    LIBRARIES_TO_LINK
      ${libfd-net-device}
      ${libinternet}
      ${libapplications}
  )

  build_lib_example(
    NAME fd-emu-onoff
    SOURCE_FILES fd-emu-onoff.cc
    LIBRARIES_TO_LINK
      ${libfd-net-device}
      ${libinternet}
      ${libapplications}
  )

  build_lib_example(
    NAME fd-emu-send
    SOURCE_FILES fd-emu-send.cc
    LIBRARIES_TO_LINK
      ${libfd-net-device}
      ${libinternet}
      ${libapplications}
      ${libinternet-apps}
      ${libtraffic-control}
  )

  build_lib_example(
    NAME fd-emu-tc
    SOURCE_FILES fd-emu-tc.cc
    LIBRARIES_TO_LINK
      ${libfd-net-device}
      ${libinternet}
      ${libapplications}
      ${libinternet-apps}
      ${libtraffic-control}
  )
endif()

if(${ENABLE_TAPNETDEV})
  build_lib_example(
    NAME fd-tap-ping
    SOURCE_FILES fd-tap-ping.cc
    LIBRARIES_TO_LINK
      ${libfd-net-device}
      ${libinternet}
      ${libinternet-apps}
  )

  build_lib_example(
    NAME fd-tap-ping6
    SOURCE_FILES fd-tap-ping6.cc
    LIBRARIES_TO_LINK
      ${libfd-net-device}
      ${libinternet}
      ${libinternet-apps}
      ${libcsma}
  )
endif()
