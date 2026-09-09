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
  NAME wifi-phy-test
  SOURCE_FILES wifi-phy-test.cc
  LIBRARIES_TO_LINK
    ${libcore}
    ${libmobility}
    ${libnetwork}
    ${libwifi}
)

build_lib_example(
  NAME wifi-test-interference-helper
  SOURCE_FILES wifi-test-interference-helper.cc
  LIBRARIES_TO_LINK
    ${libcore}
    ${libmobility}
    ${libnetwork}
    ${libwifi}
)

build_lib_example(
  NAME wifi-manager-example
  SOURCE_FILES wifi-manager-example.cc
  LIBRARIES_TO_LINK
    ${libcore}
    ${libnetwork}
    ${libwifi}
    ${libstats}
    ${libmobility}
    ${libpropagation}
)

build_lib_example(
  NAME wifi-trans-example
  SOURCE_FILES wifi-trans-example.cc
  LIBRARIES_TO_LINK
    ${libcore}
    ${libnetwork}
    ${libwifi}
    ${libstats}
    ${libmobility}
    ${libpropagation}
)

build_lib_example(
  NAME wifi-phy-configuration
  SOURCE_FILES wifi-phy-configuration.cc
  LIBRARIES_TO_LINK ${libwifi}
                    ${libconfig-store}
)

build_lib_example(
  NAME wifi-bianchi
  SOURCE_FILES wifi-bianchi.cc
  LIBRARIES_TO_LINK
    ${libwifi}
    ${libapplications}
    ${libinternet-apps}
)
