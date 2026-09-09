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
  LIBNAME energy
  SOURCE_FILES
    helper/basic-energy-harvester-helper.cc
    helper/basic-energy-source-helper.cc
    helper/energy-harvester-container.cc
    helper/energy-harvester-helper.cc
    helper/energy-model-helper.cc
    helper/energy-source-container.cc
    helper/generic-battery-model-helper.cc
    helper/li-ion-energy-source-helper.cc
    helper/rv-battery-model-helper.cc
    model/basic-energy-harvester.cc
    model/basic-energy-source.cc
    model/device-energy-model-container.cc
    model/device-energy-model.cc
    model/energy-harvester.cc
    model/energy-source.cc
    model/generic-battery-model.cc
    model/li-ion-energy-source.cc
    model/rv-battery-model.cc
    model/simple-device-energy-model.cc
  HEADER_FILES
    helper/basic-energy-harvester-helper.h
    helper/basic-energy-source-helper.h
    helper/energy-harvester-container.h
    helper/energy-harvester-helper.h
    helper/energy-model-helper.h
    helper/energy-source-container.h
    helper/generic-battery-model-helper.h
    helper/li-ion-energy-source-helper.h
    helper/rv-battery-model-helper.h
    model/basic-energy-harvester.h
    model/basic-energy-source.h
    model/device-energy-model-container.h
    model/device-energy-model.h
    model/energy-harvester.h
    model/energy-source.h
    model/generic-battery-model.h
    model/li-ion-energy-source.h
    model/rv-battery-model.h
    model/simple-device-energy-model.h
  LIBRARIES_TO_LINK ${libnetwork}
  TEST_SOURCES test/basic-energy-harvester-test.cc
               test/li-ion-energy-source-test.cc
)
