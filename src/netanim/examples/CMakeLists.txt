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
    dumbbell-animation
    grid-animation
    star-animation
    colors-link-description
    resources-counters
)

foreach(
  example
  ${base_examples}
)
  build_lib_example(
    NAME ${example}
    SOURCE_FILES ${example}.cc
    LIBRARIES_TO_LINK
      ${libnetanim}
      ${libapplications}
      ${libpoint-to-point-layout}
  )
endforeach()

build_lib_example(
  NAME wireless-animation
  SOURCE_FILES wireless-animation.cc
  LIBRARIES_TO_LINK
    ${libnetanim}
    ${libapplications}
    ${libpoint-to-point}
    ${libcsma}
    ${libwifi}
    ${libmobility}
    ${libnetwork}
)

build_lib_example(
  NAME uan-animation
  SOURCE_FILES uan-animation.cc
  LIBRARIES_TO_LINK
    ${libnetanim}
    ${libinternet}
    ${libmobility}
    ${libapplications}
    ${libuan}
)
