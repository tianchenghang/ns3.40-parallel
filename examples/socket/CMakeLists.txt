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

build_example(
  NAME socket-bound-static-routing
  SOURCE_FILES socket-bound-static-routing.cc
  LIBRARIES_TO_LINK
    ${libnetwork}
    ${libcsma}
    ${libpoint-to-point}
    ${libinternet}
)

build_example(
  NAME socket-bound-tcp-static-routing
  SOURCE_FILES socket-bound-tcp-static-routing.cc
  LIBRARIES_TO_LINK
    ${libnetwork}
    ${libcsma}
    ${libpoint-to-point}
    ${libinternet}
    ${libapplications}
)

build_example(
  NAME socket-options-ipv4
  SOURCE_FILES socket-options-ipv4.cc
  LIBRARIES_TO_LINK
    ${libnetwork}
    ${libcsma}
    ${libpoint-to-point}
    ${libinternet}
)

build_example(
  NAME socket-options-ipv6
  SOURCE_FILES socket-options-ipv6.cc
  LIBRARIES_TO_LINK
    ${libnetwork}
    ${libcsma}
    ${libpoint-to-point}
    ${libinternet}
)
