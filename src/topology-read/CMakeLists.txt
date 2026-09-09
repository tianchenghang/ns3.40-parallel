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
  LIBNAME topology-read
  SOURCE_FILES
    helper/topology-reader-helper.cc
    model/inet-topology-reader.cc
    model/orbis-topology-reader.cc
    model/rocketfuel-topology-reader.cc
    model/topology-reader.cc
  HEADER_FILES
    helper/topology-reader-helper.h
    model/inet-topology-reader.h
    model/orbis-topology-reader.h
    model/rocketfuel-topology-reader.h
    model/topology-reader.h
  LIBRARIES_TO_LINK ${libnetwork}
  TEST_SOURCES test/rocketfuel-topology-reader-test-suite.cc
)
