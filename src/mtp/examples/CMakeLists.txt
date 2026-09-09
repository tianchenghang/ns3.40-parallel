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

build_lib_example(
  NAME simple-mtp
  SOURCE_FILES simple-mtp.cc
  LIBRARIES_TO_LINK
    ${libmtp}
    ${libpoint-to-point}
    ${libinternet}
    ${libnix-vector-routing}
    ${libapplications}
)

build_lib_example(
  NAME fat-tree-mtp
  SOURCE_FILES fat-tree-mtp.cc
  LIBRARIES_TO_LINK
    ${libmtp}
    ${libpoint-to-point}
    ${libinternet}
    ${libnix-vector-routing}
    ${libapplications}
    ${libflow-monitor}
)
