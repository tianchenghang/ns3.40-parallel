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

# Create a custom library
add_library(
  scratch-nested-subdir-lib
  lib/scratch-nested-subdir-library-source.cc
)

# Link the custom library to the scratch executable
build_exec(
  EXECNAME scratch-nested-subdir-executable
  SOURCE_FILES scratch-nested-subdir-executable.cc
  LIBRARIES_TO_LINK scratch-nested-subdir-lib
                    ${libcore}
  # use "${ns3-libs}" "${ns3-contrib-libs}" in case you want to link to all
  # enabled modules
  EXECUTABLE_DIRECTORY_PATH ${CMAKE_OUTPUT_DIRECTORY}/scratch/nested-subdir
)
