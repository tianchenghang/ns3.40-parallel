#!/usr/bin/env python3
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


import re
import subprocess

ccache_misses_line = subprocess.check_output(["ccache", "--print-stats"]).decode()
ccache_misses = int(re.findall("cache_miss(.*)", ccache_misses_line)[0])
print(ccache_misses)
