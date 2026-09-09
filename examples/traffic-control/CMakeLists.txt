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
  NAME traffic-control
  SOURCE_FILES traffic-control.cc
  LIBRARIES_TO_LINK
    ${libinternet}
    ${libpoint-to-point}
    ${libapplications}
    ${libtraffic-control}
    ${libflow-monitor}
)

build_example(
  NAME queue-discs-benchmark
  SOURCE_FILES queue-discs-benchmark.cc
  LIBRARIES_TO_LINK
    ${libinternet}
    ${libpoint-to-point}
    ${libapplications}
    ${libinternet-apps}
    ${libtraffic-control}
    ${libflow-monitor}
)

build_example(
  NAME red-vs-fengadaptive
  SOURCE_FILES red-vs-fengadaptive.cc
  LIBRARIES_TO_LINK
    ${libinternet}
    ${libpoint-to-point}
    ${libpoint-to-point-layout}
    ${libapplications}
    ${libtraffic-control}
)

build_example(
  NAME red-vs-nlred
  SOURCE_FILES red-vs-nlred.cc
  LIBRARIES_TO_LINK
    ${libinternet}
    ${libpoint-to-point}
    ${libpoint-to-point-layout}
    ${libapplications}
    ${libtraffic-control}
)

build_example(
  NAME tbf-example
  SOURCE_FILES tbf-example.cc
  LIBRARIES_TO_LINK
    ${libinternet}
    ${libpoint-to-point}
    ${libapplications}
    ${libtraffic-control}
)

build_example(
  NAME cobalt-vs-codel
  SOURCE_FILES cobalt-vs-codel.cc
  LIBRARIES_TO_LINK
    ${libinternet}
    ${libpoint-to-point}
    ${libapplications}
    ${libtraffic-control}
)
