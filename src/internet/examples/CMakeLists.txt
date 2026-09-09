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
  NAME main-simple
  SOURCE_FILES main-simple.cc
  LIBRARIES_TO_LINK
    ${libnetwork}
    ${libinternet}
    ${libapplications}
)

build_lib_example(
  NAME neighbor-cache-example
  SOURCE_FILES neighbor-cache-example.cc
  LIBRARIES_TO_LINK
    ${libapplications}
    ${libcsma}
    ${libinternet}
    ${libnetwork}
)

build_lib_example(
  NAME neighbor-cache-dynamic
  SOURCE_FILES neighbor-cache-dynamic.cc
  LIBRARIES_TO_LINK
    ${libcsma}
    ${libinternet}
    ${libnetwork}
)
