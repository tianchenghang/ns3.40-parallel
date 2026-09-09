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
    csma-one-subnet
    csma-broadcast
    csma-packet-socket
    csma-multicast
)
foreach(
  example
  ${base_examples}
)
  build_lib_example(
    NAME ${example}
    SOURCE_FILES ${example}.cc
    LIBRARIES_TO_LINK
      ${libcsma}
      ${libinternet}
      ${libapplications}
  )
endforeach()

build_lib_example(
  NAME csma-raw-ip-socket
  SOURCE_FILES csma-raw-ip-socket.cc
  LIBRARIES_TO_LINK
    ${libcsma}
    ${libinternet}
    ${libapplications}
    ${libinternet-apps}
)

build_lib_example(
  NAME csma-ping
  SOURCE_FILES csma-ping.cc
  LIBRARIES_TO_LINK
    ${libcsma}
    ${libinternet}
    ${libapplications}
    ${libinternet-apps}
)
