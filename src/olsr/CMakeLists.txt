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

build_lib(
  LIBNAME olsr
  SOURCE_FILES
    helper/olsr-helper.cc
    model/olsr-header.cc
    model/olsr-routing-protocol.cc
    model/olsr-state.cc
  HEADER_FILES
    helper/olsr-helper.h
    model/olsr-header.h
    model/olsr-repositories.h
    model/olsr-routing-protocol.h
    model/olsr-state.h
  LIBRARIES_TO_LINK ${libinternet}
  TEST_SOURCES
    test/regression-test-suite.cc
    test/bug780-test.cc
    test/hello-regression-test.cc
    test/olsr-header-test-suite.cc
    test/olsr-routing-protocol-test-suite.cc
    test/tc-regression-test.cc
)
