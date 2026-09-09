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

set(NS3_WITH_OPENFLOW
    ""
    CACHE PATH
          "Build with Openflow support"
)
set(NS3_OPENFLOW
    "OFF"
    CACHE INTERNAL
          "ON if Openflow is found in NS3_WITH_OPENFLOW"
)

find_external_library(
  DEPENDENCY_NAME openflow
  HEADER_NAME openflow.h
  LIBRARY_NAME openflow
  SEARCH_PATHS ${NS3_WITH_OPENFLOW}
)

if((NOT
    openflow_FOUND)
   AND (NOT
        ${openflow_FOUND})
   AND (NOT
        ${NS3_FETCH_OPTIONAL_COMPONENTS})
)
  message(
    ${HIGHLIGHTED_STATUS}
    "Skipping src/openflow"
  )
  return()
endif()

if(${NS3_FETCH_OPTIONAL_COMPONENTS})
  set(openflow_LIBRARIES
      openflow
  )
endif()

check_include_file_cxx(
  boost/static_assert.hpp
  BOOST_STATIC_ASSERT
)
if(NOT
   BOOST_STATIC_ASSERT
)
  message(STATUS "Openflow requires Boost static_assert.hpp")
  return()
endif()

include_directories(${openflow_INCLUDE_DIRS})
add_definitions(
  -DNS3_OPENFLOW
  -DENABLE_OPENFLOW
)
set(NS3_OPENFLOW
    "ON"
    CACHE INTERNAL
          "ON if Openflow is found in NS3_WITH_OPENFLOW"
)

if(${GCC})
  add_compile_options(-Wno-stringop-truncation) # This option does not exist in
                                                # CLANG
elseif(${CLANG})
  add_compile_options(-Wno-reserved-user-defined-literal)
endif()

build_lib(
  LIBNAME openflow
  SOURCE_FILES
    helper/openflow-switch-helper.cc
    model/openflow-interface.cc
    model/openflow-switch-net-device.cc
  HEADER_FILES
    helper/openflow-switch-helper.h
    model/openflow-interface.h
    model/openflow-switch-net-device.h
  LIBRARIES_TO_LINK ${libinternet}
                    ${openflow_LIBRARIES}
  TEST_SOURCES test/openflow-switch-test-suite.cc
)
