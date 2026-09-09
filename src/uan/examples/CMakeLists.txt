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
    uan-cw-example
    uan-rc-example
    uan-ipv4-example
    uan-ipv6-example
    uan-raw-example
)
foreach(
  example
  ${base_examples}
)
  build_lib_example(
    NAME ${example}
    SOURCE_FILES ${example}.cc
    LIBRARIES_TO_LINK
      ${libinternet}
      ${libmobility}
      ${libstats}
      ${libapplications}
      ${libuan}
  )
endforeach()

build_lib_example(
  NAME uan-6lowpan-example
  SOURCE_FILES uan-6lowpan-example.cc
  LIBRARIES_TO_LINK
    ${libinternet}
    ${libmobility}
    ${libstats}
    ${libapplications}
    ${libuan}
    ${libsixlowpan}
)
