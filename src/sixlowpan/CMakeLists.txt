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
      test/sixlowpan-examples-test-suite.cc
  )
endif()

build_lib(
  LIBNAME sixlowpan
  SOURCE_FILES
    helper/sixlowpan-helper.cc
    model/sixlowpan-header.cc
    model/sixlowpan-net-device.cc
  HEADER_FILES
    helper/sixlowpan-helper.h
    model/sixlowpan-header.h
    model/sixlowpan-net-device.h
  LIBRARIES_TO_LINK
    ${libinternet}
  TEST_SOURCES
    ${example_as_test_suite}
    test/mock-net-device.cc
    test/sixlowpan-fragmentation-test.cc
    test/sixlowpan-hc1-test.cc
    test/sixlowpan-iphc-stateful-test.cc
    test/sixlowpan-iphc-test.cc
)
