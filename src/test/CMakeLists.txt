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

set(dsr_sources)

# cmake-format: off
if((dsr IN_LIST ns3-all-enabled-modules)
    AND (uan IN_LIST ns3-all-enabled-modules)
    AND (olsr IN_LIST ns3-all-enabled-modules)
    AND (lte IN_LIST ns3-all-enabled-modules))
  set(dsr_sources traced/traced-callback-typedef-test-suite.cc)
endif()
# cmake-format: on

set(application_sources)
set(csma_sources)
set(wifi_sources)
if(applications
   IN_LIST
   ns3-all-enabled-modules
)
  if(point-to-point
     IN_LIST
     ns3-all-enabled-modules
  )
    # cmake-format: off
    set(applications_sources
        ns3tcp/ns3tcp-loss-test-suite.cc
        ns3tcp/ns3tcp-no-delay-test-suite.cc
        ns3tcp/ns3tcp-socket-test-suite.cc
        ns3tcp/ns3tcp-state-test-suite.cc
    )
    # cmake-format: on
  endif()
  if(wifi
     IN_LIST
     ns3-all-enabled-modules
  )
    set(wifi_sources
        ns3wifi/wifi-issue-211-test-suite.cc
        ns3wifi/wifi-ac-mapping-test-suite.cc
        ns3wifi/wifi-msdu-aggregator-test-suite.cc
    )
  endif()
  if((csma-layout
      IN_LIST
      ns3-all-enabled-modules
     )
     AND (internet-apps
          IN_LIST
          ns3-all-enabled-modules
         )
  )
    set(csma_sources
        csma-system-test-suite.cc
    )
  endif()
endif()

set(internet_sources)
if(internet
   IN_LIST
   ns3-all-enabled-modules
)
  set(internet_sources
      ns3tcp/ns3tcp-socket-writer.cc
  )
endif()

set(network_sources)
if(network
   IN_LIST
   ns3-all-enabled-modules
)
  set(network_sources
      traced/traced-value-callback-typedef-test-suite.cc
  )
endif()

set(traffic-control_sources)
if(traffic-control
   IN_LIST
   ns3-all-enabled-modules
)
  set(traffic-control_sources
      ns3tc/fq-cobalt-queue-disc-test-suite.cc
      ns3tc/fq-codel-queue-disc-test-suite.cc
      ns3tc/fq-pie-queue-disc-test-suite.cc
      ns3tc/pfifo-fast-queue-disc-test-suite.cc
  )
endif()

add_library(
  ${libtest}
  OBJECT
  ${PROJECT_SOURCE_DIR}/build-support/empty.cc # empty source file if only
  # libcore is enabled
  ${applications_sources}
  ${csma_sources}
  ${dsr_sources}
  ${internet_sources}
  ${network_sources}
  ${traffic-control_sources}
  ${wifi_sources}
)

add_dependencies(
  ${libtest}
  copy_all_headers
)
