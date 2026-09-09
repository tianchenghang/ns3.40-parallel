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

set(base_examples
    lena-cc-helper
    lena-cqi-threshold
    lena-deactivate-bearer
    lena-distributed-ffr
    lena-dual-stripe
    lena-fading
    lena-frequency-reuse
    lena-intercell-interference
    lena-ipv6-addr-conf
    lena-ipv6-ue-rh
    lena-ipv6-ue-ue
    lena-pathloss-traces
    lena-profiling
    lena-radio-link-failure
    lena-rem
    lena-rem-sector-antenna
    lena-rlc-traces
    lena-simple
    lena-simple-epc
    lena-simple-epc-backhaul
    lena-uplink-power-control
    lena-x2-handover
    lena-x2-handover-measures
)

foreach(
  example
  ${base_examples}
)
  build_lib_example(
    NAME ${example}
    SOURCE_FILES ${example}.cc
    LIBRARIES_TO_LINK ${liblte}
                      ${libconfig-store}
  )
endforeach()

if(${ENABLE_EMU})
  build_lib_example(
    NAME lena-simple-epc-emu
    SOURCE_FILES lena-simple-epc-emu.cc
    LIBRARIES_TO_LINK
      ${liblte}
      ${fd-net-device}
      ${libconfig-store}
  )
endif()
