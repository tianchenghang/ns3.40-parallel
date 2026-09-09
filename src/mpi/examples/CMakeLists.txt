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

link_libraries(${MPI_CXX_LIBRARIES})

set(base_examples
    simple-distributed
    simple-distributed-mpi-comm
    nms-p2p-nix-distributed
    simple-distributed-empty-node
)

foreach(
  example
  ${base_examples}
)
  build_lib_example(
    NAME ${example}
    SOURCE_FILES ${example}.cc
                 mpi-test-fixtures.cc
    LIBRARIES_TO_LINK
      ${libmpi}
      ${libpoint-to-point}
      ${libinternet}
      ${libnix-vector-routing}
      ${libapplications}
  )
endforeach()

build_lib_example(
  NAME third-distributed
  SOURCE_FILES third-distributed.cc
               mpi-test-fixtures.cc
  LIBRARIES_TO_LINK
    ${libmpi}
    ${libpoint-to-point}
    ${libinternet}
    ${libmobility}
    ${libwifi}
    ${libcsma}
    ${libapplications}
)

build_lib_example(
  NAME fat-tree-mpi
  SOURCE_FILES fat-tree-mpi.cc
  LIBRARIES_TO_LINK
  ${libmpi}
  ${libpoint-to-point}
  ${libinternet}
  ${libnix-vector-routing}
  ${libapplications}
  ${libflow-monitor}
)

if(${ENABLE_MTP})
  build_lib_example(
    NAME simple-hybrid
    SOURCE_FILES simple-hybrid.cc
                 mpi-test-fixtures.cc
    LIBRARIES_TO_LINK
    ${libmpi}
    ${libpoint-to-point}
    ${libinternet}
    ${libnix-vector-routing}
    ${libapplications}
    ${libmtp}
  )

  build_lib_example(
    NAME fat-tree-hybrid
    SOURCE_FILES fat-tree-hybrid.cc
    LIBRARIES_TO_LINK
    ${libmpi}
    ${libmtp}
    ${libpoint-to-point}
    ${libinternet}
    ${libnix-vector-routing}
    ${libapplications}
    ${libflow-monitor}
  )
endif()