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
  LIBNAME traffic-control
  SOURCE_FILES
    helper/queue-disc-container.cc
    helper/traffic-control-helper.cc
    model/cobalt-queue-disc.cc
    model/codel-queue-disc.cc
    model/fifo-queue-disc.cc
    model/fq-cobalt-queue-disc.cc
    model/fq-codel-queue-disc.cc
    model/fq-pie-queue-disc.cc
    model/mq-queue-disc.cc
    model/packet-filter.cc
    model/pfifo-fast-queue-disc.cc
    model/pie-queue-disc.cc
    model/prio-queue-disc.cc
    model/queue-disc.cc
    model/red-queue-disc.cc
    model/tbf-queue-disc.cc
    model/traffic-control-layer.cc
  HEADER_FILES
    helper/queue-disc-container.h
    helper/traffic-control-helper.h
    model/cobalt-queue-disc.h
    model/codel-queue-disc.h
    model/fifo-queue-disc.h
    model/fq-cobalt-queue-disc.h
    model/fq-codel-queue-disc.h
    model/fq-pie-queue-disc.h
    model/mq-queue-disc.h
    model/packet-filter.h
    model/pfifo-fast-queue-disc.h
    model/pie-queue-disc.h
    model/prio-queue-disc.h
    model/queue-disc.h
    model/red-queue-disc.h
    model/tbf-queue-disc.h
    model/traffic-control-layer.h
  LIBRARIES_TO_LINK
    ${libnetwork}
    ${libcore}
  TEST_SOURCES
    test/adaptive-red-queue-disc-test-suite.cc
    test/cobalt-queue-disc-test-suite.cc
    test/codel-queue-disc-test-suite.cc
    test/fifo-queue-disc-test-suite.cc
    test/pie-queue-disc-test-suite.cc
    test/prio-queue-disc-test-suite.cc
    test/queue-disc-traces-test-suite.cc
    test/red-queue-disc-test-suite.cc
    test/tbf-queue-disc-test-suite.cc
    test/tc-flow-control-test-suite.cc
)
