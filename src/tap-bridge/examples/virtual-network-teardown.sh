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

lxc-stop -n left
lxc-stop -n right
lxc-destroy -n left
lxc-destroy -n right
ip link set dev br-left down
ip link set dev br-right down
ip link set dev tap-left nomaster
ip link set dev tap-right nomaster
ip link del br-left
ip link del br-right
ip link set dev tap-left down
ip link set dev tap-right down
ip tuntap del mode tap tap-left
ip tuntap del mode tap tap-right
