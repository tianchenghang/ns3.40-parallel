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
  LIBNAME dsdv
  SOURCE_FILES
    helper/dsdv-helper.cc
    model/dsdv-packet-queue.cc
    model/dsdv-packet.cc
    model/dsdv-routing-protocol.cc
    model/dsdv-rtable.cc
  HEADER_FILES
    helper/dsdv-helper.h
    model/dsdv-packet-queue.h
    model/dsdv-packet.h
    model/dsdv-routing-protocol.h
    model/dsdv-rtable.h
  LIBRARIES_TO_LINK ${libinternet}
  TEST_SOURCES test/dsdv-testcase.cc
)
