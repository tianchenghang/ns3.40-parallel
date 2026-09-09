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
    lr-wpan-data
    lr-wpan-mlme
    lr-wpan-packet-print
    lr-wpan-phy-test
    lr-wpan-ed-scan
    lr-wpan-active-scan
    lr-wpan-orphan-scan
)

foreach(
  example
  ${base_examples}
)
  build_lib_example(
    NAME ${example}
    SOURCE_FILES ${example}.cc
    LIBRARIES_TO_LINK ${liblr-wpan}
  )
endforeach()

build_lib_example(
  NAME lr-wpan-error-distance-plot
  SOURCE_FILES lr-wpan-error-distance-plot.cc
  LIBRARIES_TO_LINK ${liblr-wpan}
                    ${libstats}
)

build_lib_example(
  NAME lr-wpan-error-model-plot
  SOURCE_FILES lr-wpan-error-model-plot.cc
  LIBRARIES_TO_LINK ${liblr-wpan}
                    ${libstats}
)

build_lib_example(
  NAME lr-wpan-bootstrap
  SOURCE_FILES lr-wpan-bootstrap.cc
  LIBRARIES_TO_LINK ${liblr-wpan}
                    ${libnetanim}
)

build_lib_example(
  NAME lr-wpan-per-plot
  SOURCE_FILES lr-wpan-per-plot.cc
  LIBRARIES_TO_LINK ${liblr-wpan}
                    ${libstats}
)
