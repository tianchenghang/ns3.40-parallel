#!/bin/bash
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

ip link add br-left type bridge
ip link add br-right type bridge
ip tuntap add mode tap tap-left
ip tuntap add mode tap tap-right
ip link set tap-left promisc on up
ip link set tap-right promisc on up
ip link set dev tap-left master br-left
ip link set dev br-left up
ip link set dev tap-right master br-right
ip link set dev br-right up
# Note:  you also need to have loaded br_netfilter module
# ('modprobe br_netfilter') to enable /proc/sys/net/bridge
pushd /proc/sys/net/bridge
for f in bridge-nf-*; do echo 0 >$f; done
popd
# lxc-create now requires a template parameter, such as '-t ubuntu'
lxc-create -n left -t ubuntu -f lxc-left.conf
lxc-create -n right -t ubuntu -f lxc-right.conf
# Start both containers
lxc-start -n left -d
lxc-start -n right -d
