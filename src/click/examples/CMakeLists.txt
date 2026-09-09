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

build_lib_example(
  NAME nsclick-simple-lan
  SOURCE_FILES nsclick-simple-lan.cc
  LIBRARIES_TO_LINK
    ${libclick}
    ${libcsma}
    ${libinternet}
    ${libapplications}
)

build_lib_example(
  NAME nsclick-raw-wlan
  SOURCE_FILES nsclick-raw-wlan.cc
  LIBRARIES_TO_LINK
    ${libclick}
    ${libwifi}
    ${libinternet}
    ${libapplications}
)

build_lib_example(
  NAME nsclick-udp-client-server-csma
  SOURCE_FILES nsclick-udp-client-server-csma.cc
  LIBRARIES_TO_LINK
    ${libclick}
    ${libcsma}
    ${libinternet}
    ${libapplications}
)

build_lib_example(
  NAME nsclick-udp-client-server-wifi
  SOURCE_FILES nsclick-udp-client-server-wifi.cc
  LIBRARIES_TO_LINK
    ${libclick}
    ${libwifi}
    ${libinternet}
    ${libapplications}
)

build_lib_example(
  NAME nsclick-routing
  SOURCE_FILES nsclick-routing.cc
  LIBRARIES_TO_LINK
    ${libclick}
    ${libcsma}
    ${libinternet}
    ${libapplications}
)

build_lib_example(
  NAME nsclick-defines
  SOURCE_FILES nsclick-defines.cc
  LIBRARIES_TO_LINK ${libclick}
)
