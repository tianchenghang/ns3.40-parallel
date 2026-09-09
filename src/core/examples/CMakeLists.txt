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
    assert-example
    command-line-example
    fatal-example
    hash-example
    length-example
    main-callback
    main-ptr
    sample-log-time-format
    sample-random-variable
    sample-random-variable-stream
    sample-show-progress
    sample-simulator
    system-path-examples
    test-string-value-formatting
)

foreach(
  example
  ${base_examples}
)
  build_lib_example(
    NAME ${example}
    SOURCE_FILES ${example}.cc
    LIBRARIES_TO_LINK ${libcore}
  )
endforeach()

build_lib_example(
  NAME main-random-variable-stream
  SOURCE_FILES main-random-variable-stream.cc
  LIBRARIES_TO_LINK
    ${libcore}
    ${libconfig-store}
    ${libstats}
)

if(${ENABLE_BUILD_VERSION})
  build_lib_example(
    NAME build-version-example
    SOURCE_FILES build-version-example.cc
    LIBRARIES_TO_LINK ${libcore}
  )
endif()

build_lib_example(
  NAME main-test-sync
  SOURCE_FILES main-test-sync.cc
  LIBRARIES_TO_LINK ${libnetwork}
)

build_lib_example(
  NAME empirical-random-variable-example
  SOURCE_FILES empirical-random-variable-example.cc
  LIBRARIES_TO_LINK ${libcore}
                    ${libflow-monitor}
)

build_lib_example(
  NAME log-example
  SOURCE_FILES log-example.cc
  LIBRARIES_TO_LINK ${libcore}
                    ${libnetwork}
)
