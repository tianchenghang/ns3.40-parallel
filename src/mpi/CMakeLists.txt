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

set(example_as_test_suite)
if(${ENABLE_EXAMPLES})
  set(example_as_test_suite
      test/mpi-test-suite.cc
  )
endif()

if(${ENABLE_MTP})
  build_lib(
    LIBNAME mpi
    SOURCE_FILES
      model/distributed-simulator-impl.cc
      model/granted-time-window-mpi-interface.cc
      model/hybrid-simulator-impl.cc
      model/mpi-interface.cc
      model/mpi-receiver.cc
      model/null-message-mpi-interface.cc
      model/null-message-simulator-impl.cc
      model/parallel-communication-interface.h
      model/remote-channel-bundle-manager.cc
      model/remote-channel-bundle.cc
    HEADER_FILES
      model/mpi-interface.h
      model/mpi-receiver.h
      model/parallel-communication-interface.h
    LIBRARIES_TO_LINK
      ${libcore}
      ${libnetwork}
      ${libmtp}
      ${MPI_CXX_LIBRARIES}
    TEST_SOURCES ${example_as_test_suite}
  )
else()
  build_lib(
    LIBNAME mpi
    SOURCE_FILES
      model/distributed-simulator-impl.cc
      model/granted-time-window-mpi-interface.cc
      model/mpi-interface.cc
      model/mpi-receiver.cc
      model/null-message-mpi-interface.cc
      model/null-message-simulator-impl.cc
      model/parallel-communication-interface.h
      model/remote-channel-bundle-manager.cc
      model/remote-channel-bundle.cc
    HEADER_FILES
      model/mpi-interface.h
      model/mpi-receiver.h
      model/parallel-communication-interface.h
    LIBRARIES_TO_LINK
      ${libcore}
      ${libnetwork}
      ${MPI_CXX_LIBRARIES}
    TEST_SOURCES ${example_as_test_suite}
  )
endif()
