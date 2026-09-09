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
  NAME interference-pattern
  SOURCE_FILES interference-pattern/mygym.cc
  interference-pattern/sim.cc
  LIBRARIES_TO_LINK
  ${libcore}
  ${libinternet}
  ${libopengym}
  ${libwifi}
)

build_lib_example(
  NAME linear-mesh
  SOURCE_FILES linear-mesh/sim.cc
  LIBRARIES_TO_LINK
  ${libapplications}
  ${libcore}
  ${libinternet}
  ${libopengym}
  ${libwifi}
)

build_lib_example(
  NAME linear-mesh-2
  SOURCE_FILES linear-mesh-2/sim.cc
  linear-mesh-2/mygym.cc
  LIBRARIES_TO_LINK
  ${libapplications}
  ${libcore}
  ${libinternet}
  ${libopengym}
  ${libwifi}
)

build_lib_example(
  NAME opengym
  SOURCE_FILES opengym/sim.cc
  LIBRARIES_TO_LINK
  ${libcore}
  ${libopengym}
)

build_lib_example(
  NAME opengym-2
  SOURCE_FILES opengym-2/sim.cc
  opengym-2/mygym.cc
  LIBRARIES_TO_LINK
  ${libcore}
  ${libopengym}
)

build_lib_example(
  NAME rl-tcp
  SOURCE_FILES rl-tcp/sim.cc
  rl-tcp/tcp-rl-env.cc
  rl-tcp/tcp-rl.cc
  LIBRARIES_TO_LINK
  ${libapplications}
  ${libcore}
  ${libflow-monitor}
  ${libinternet}
  ${libopengym}
  ${libpoint-to-point-layout}
  ${libptp}
)

build_lib_example(
  NAME swift-tcp
  SOURCE_FILES swift-tcp/sim.cc
  swift-tcp/tcp-swift-env.cc
  swift-tcp/tcp-swift.cc
  rl-tcp/tcp-rl-env.cc
  rl-tcp/tcp-rl.cc
  LIBRARIES_TO_LINK
  ${libapplications}
  ${libcore}
  ${libflow-monitor}
  ${libinternet}
  ${libopengym}
  ${libpoint-to-point-layout}
  ${libptp}
  ${libmtp}
)
