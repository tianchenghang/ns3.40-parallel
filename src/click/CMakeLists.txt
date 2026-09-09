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

set(NS3_WITH_CLICK
    ""
    CACHE PATH
          "Build with click support"
)
set(NS3_CLICK
    "OFF"
    CACHE INTERNAL
          "ON if Click is found in NS3_WITH_CLICK"
)

find_external_library(
  DEPENDENCY_NAME click
  HEADER_NAME simclick.h
  LIBRARY_NAMES nsclick
                click
  PATH_SUFFIXES userlevel
                ns
  SEARCH_PATHS ${NS3_WITH_CLICK}
)

if((NOT
    click_FOUND)
   AND (NOT
        ${click_FOUND})
   AND (NOT
        ${NS3_FETCH_OPTIONAL_COMPONENTS})
)
  message(
    ${HIGHLIGHTED_STATUS}
    "Skipping src/click"
  )
  return()
endif()

if(${NS3_FETCH_OPTIONAL_COMPONENTS})
  set(click_LIBRARIES
      click
      nsclick
  )
endif()

include_directories(${click_INCLUDE_DIRS})
set(NS3_CLICK
    "ON"
    CACHE INTERNAL
          "ON if Click is found in NS3_WITH_CLICK"
)
add_definitions(-DNS3_CLICK)

build_lib(
  LIBNAME click
  SOURCE_FILES
    helper/click-internet-stack-helper.cc
    model/ipv4-click-routing.cc
    model/ipv4-l3-click-protocol.cc
  HEADER_FILES
    helper/click-internet-stack-helper.h
    model/ipv4-click-routing.h
    model/ipv4-l3-click-protocol.h
  LIBRARIES_TO_LINK
    ${libcore}
    ${libnetwork}
    ${libinternet}
    ${click_LIBRARIES}
  TEST_SOURCES test/ipv4-click-routing-test.cc
)
