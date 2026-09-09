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
  LIBNAME lr-wpan
  SOURCE_FILES
    helper/lr-wpan-helper.cc
    model/lr-wpan-csmaca.cc
    model/lr-wpan-error-model.cc
    model/lr-wpan-fields.cc
    model/lr-wpan-interference-helper.cc
    model/lr-wpan-lqi-tag.cc
    model/lr-wpan-mac-header.cc
    model/lr-wpan-mac-pl-headers.cc
    model/lr-wpan-mac-trailer.cc
    model/lr-wpan-mac.cc
    model/lr-wpan-net-device.cc
    model/lr-wpan-phy.cc
    model/lr-wpan-spectrum-signal-parameters.cc
    model/lr-wpan-spectrum-value-helper.cc
  HEADER_FILES
    helper/lr-wpan-helper.h
    model/lr-wpan-constants.h
    model/lr-wpan-csmaca.h
    model/lr-wpan-error-model.h
    model/lr-wpan-fields.h
    model/lr-wpan-interference-helper.h
    model/lr-wpan-lqi-tag.h
    model/lr-wpan-mac-header.h
    model/lr-wpan-mac-pl-headers.h
    model/lr-wpan-mac-trailer.h
    model/lr-wpan-mac.h
    model/lr-wpan-net-device.h
    model/lr-wpan-phy.h
    model/lr-wpan-spectrum-signal-parameters.h
    model/lr-wpan-spectrum-value-helper.h
  LIBRARIES_TO_LINK
    ${libnetwork}
    ${libcore}
    ${libmobility}
    ${libspectrum}
    ${libpropagation}
  TEST_SOURCES
    test/lr-wpan-ack-test.cc
    test/lr-wpan-cca-test.cc
    test/lr-wpan-collision-test.cc
    test/lr-wpan-ed-test.cc
    test/lr-wpan-error-model-test.cc
    test/lr-wpan-packet-test.cc
    test/lr-wpan-pd-plme-sap-test.cc
    test/lr-wpan-spectrum-value-helper-test.cc
    test/lr-wpan-ifs-test.cc
    test/lr-wpan-slotted-csmaca-test.cc
    test/lr-wpan-mac-test.cc
)
