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
  LIBNAME bridge
  SOURCE_FILES
    helper/bridge-helper.cc
    model/bridge-channel.cc
    model/bridge-net-device.cc
  HEADER_FILES
    helper/bridge-helper.h
    model/bridge-channel.h
    model/bridge-net-device.h
  LIBRARIES_TO_LINK ${libnetwork}
  TEST_SOURCES ${test_sources}
)
