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
  LIBNAME antenna
  SOURCE_FILES
    model/angles.cc
    model/antenna-model.cc
    model/cosine-antenna-model.cc
    model/isotropic-antenna-model.cc
    model/parabolic-antenna-model.cc
    model/phased-array-model.cc
    model/three-gpp-antenna-model.cc
    model/uniform-planar-array.cc
  HEADER_FILES
    model/angles.h
    model/antenna-model.h
    model/cosine-antenna-model.h
    model/isotropic-antenna-model.h
    model/parabolic-antenna-model.h
    model/phased-array-model.h
    model/three-gpp-antenna-model.h
    model/uniform-planar-array.h
  LIBRARIES_TO_LINK ${libcore}
  TEST_SOURCES
    test/test-angles.cc
    test/test-degrees-radians.cc
    test/test-isotropic-antenna.cc
    test/test-cosine-antenna.cc
    test/test-parabolic-antenna.cc
    test/test-uniform-planar-array.cc
)
