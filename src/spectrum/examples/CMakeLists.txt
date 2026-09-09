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
  NAME adhoc-aloha-ideal-phy
  SOURCE_FILES adhoc-aloha-ideal-phy.cc
  LIBRARIES_TO_LINK
    ${libapplications}
    ${libinternet}
    ${libmobility}
    ${libspectrum}
)

build_lib_example(
  NAME adhoc-aloha-ideal-phy-matrix-propagation-loss-model
  SOURCE_FILES adhoc-aloha-ideal-phy-matrix-propagation-loss-model.cc
  LIBRARIES_TO_LINK
    ${libapplications}
    ${libinternet}
    ${libmobility}
    ${libspectrum}
)

build_lib_example(
  NAME adhoc-aloha-ideal-phy-with-microwave-oven
  SOURCE_FILES adhoc-aloha-ideal-phy-with-microwave-oven.cc
  LIBRARIES_TO_LINK
    ${libapplications}
    ${libinternet}
    ${libmobility}
    ${libspectrum}
)

build_lib_example(
  NAME tv-trans-example
  SOURCE_FILES tv-trans-example.cc
  LIBRARIES_TO_LINK
    ${libcore}
    ${libmobility}
    ${libspectrum}
)

build_lib_example(
  NAME tv-trans-regional-example
  SOURCE_FILES tv-trans-regional-example.cc
  LIBRARIES_TO_LINK
    ${libcore}
    ${libmobility}
    ${libspectrum}
)

build_lib_example(
  NAME three-gpp-channel-example
  SOURCE_FILES three-gpp-channel-example.cc
  LIBRARIES_TO_LINK
    ${libcore}
    ${liblte}
    ${libmobility}
    ${libspectrum}
)

build_lib_example(
  NAME three-gpp-two-ray-channel-calibration
  SOURCE_FILES three-gpp-two-ray-channel-calibration.cc
  LIBRARIES_TO_LINK
    ${libcore}
    ${liblte}
    ${libmobility}
    ${libspectrum}
)
