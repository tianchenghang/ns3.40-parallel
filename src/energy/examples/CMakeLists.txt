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
  NAME generic-battery-discharge-example
  SOURCE_FILES generic-battery-discharge-example.cc
  LIBRARIES_TO_LINK ${libcore}
                    ${libenergy}
)

build_example(
  NAME generic-battery-wifiradio-example
  SOURCE_FILES generic-battery-wifiradio-example.cc
  LIBRARIES_TO_LINK
    ${libcore}
    ${libconfig-store}
    ${libenergy}
    ${libinternet}
    ${libmobility}
    ${libwifi}
)

build_lib_example(
  NAME li-ion-energy-source-example
  SOURCE_FILES li-ion-energy-source-example.cc
  LIBRARIES_TO_LINK ${libcore}
                    ${libenergy}
)

build_lib_example(
  NAME rv-battery-model-test
  SOURCE_FILES rv-battery-model-test.cc
  LIBRARIES_TO_LINK
    ${libcore}
    ${libenergy}
    ${libwifi}
)

build_lib_example(
  NAME basic-energy-model-test
  SOURCE_FILES basic-energy-model-test.cc
  LIBRARIES_TO_LINK
    ${libcore}
    ${libenergy}
    ${libwifi}
)
