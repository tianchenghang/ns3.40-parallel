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

if(${ENABLE_EXAMPLES})
  subdirlist(examples_to_build ${CMAKE_CURRENT_SOURCE_DIR})

  # Process subdirectories
  foreach(examplefolder ${examples_to_build})
    if(NOT (EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/${examplefolder}/CMakeLists.txt))
      continue()
    endif()
    add_subdirectory(${examplefolder})

    set(ns3-example-folders
        "${examplefolder};${ns3-example-folders}"
        CACHE INTERNAL "list of example folders"
    )
  endforeach()
endif()

scan_python_examples(${CMAKE_CURRENT_SOURCE_DIR})
