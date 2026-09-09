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

set(NS3_WITH_BRITE
    ""
    CACHE PATH
          "Build with brite support"
)
set(NS3_BRITE
    "OFF"
    CACHE INTERNAL
          "ON if Brite is found in NS3_WITH_BRITE"
)

find_external_library(
  DEPENDENCY_NAME brite
  HEADER_NAME Brite.h
  LIBRARY_NAME brite
  SEARCH_PATHS ${NS3_WITH_BRITE}
)

if((NOT
    brite_FOUND)
   AND (NOT
        ${brite_FOUND})
   AND (NOT
        ${NS3_FETCH_OPTIONAL_COMPONENTS})
)
  message(
    ${HIGHLIGHTED_STATUS}
    "Skipping src/brite"
  )
  return()
endif()

if(${NS3_FETCH_OPTIONAL_COMPONENTS})
  set(brite_LIBRARIES
      brite
  )
endif()

# Only process module if include folder and library have been found
include_directories(${brite_INCLUDE_DIRS})
set(NS3_BRITE
    "ON"
    CACHE INTERNAL
          "ON if Brite is found in NS3_WITH_BRITE"
)

build_lib(
  LIBNAME brite
  SOURCE_FILES helper/brite-topology-helper.cc
  HEADER_FILES helper/brite-topology-helper.h
  LIBRARIES_TO_LINK
    ${libnetwork}
    ${libcore}
    ${libinternet}
    ${libpoint-to-point}
    ${brite_LIBRARIES}
  TEST_SOURCES test/brite-test-topology.cc
)
