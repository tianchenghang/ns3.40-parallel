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
  NAME time-probe-example
  SOURCE_FILES time-probe-example.cc
  LIBRARIES_TO_LINK ${libstats}
)

set(base_examples
    gnuplot-example
    double-probe-example
    gnuplot-aggregator-example
    gnuplot-helper-example
    file-aggregator-example
    file-helper-example
)

foreach(
  example
  ${base_examples}
)
  build_lib_example(
    NAME ${example}
    SOURCE_FILES ${example}.cc
    LIBRARIES_TO_LINK ${libnetwork}
                      ${libstats}
  )
endforeach()
