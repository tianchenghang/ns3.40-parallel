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

if(${ENABLE_TAP})
  build_lib_example(
    NAME tap-csma
    SOURCE_FILES tap-csma.cc
    LIBRARIES_TO_LINK
      ${libcsma}
      ${libtap-bridge}
      ${libinternet}
      ${libwifi}
  )

  build_lib_example(
    NAME tap-csma-virtual-machine
    SOURCE_FILES tap-csma-virtual-machine.cc
    LIBRARIES_TO_LINK
      ${libcsma}
      ${libtap-bridge}
      ${libinternet}
  )

  build_lib_example(
    NAME tap-wifi-virtual-machine
    SOURCE_FILES tap-wifi-virtual-machine.cc
    LIBRARIES_TO_LINK
      ${libcsma}
      ${libtap-bridge}
      ${libinternet}
      ${libwifi}
      ${libmobility}
  )

  build_lib_example(
    NAME tap-wifi-dumbbell
    SOURCE_FILES tap-wifi-dumbbell.cc
    LIBRARIES_TO_LINK
      ${libwifi}
      ${libcsma}
      ${libpoint-to-point}
      ${libtap-bridge}
      ${libinternet}
      ${libapplications}
  )

endif()
