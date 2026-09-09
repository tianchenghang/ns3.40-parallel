#!/usr/bin/env bash
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

set -euo pipefail

git ls-files -z \
	'*.h' '*.c' \
	'*.hh' '*.cc' \
	'*.hpp' '*.cpp' \
	'*.hxx' '*.cxx' \
	'*.h++' '*.c++' |
	xargs -0 -r clang-format -i

# pip install ruff
uv run ruff format ./

# go install mvdan.cc/sh/v3/cmd/shfmt@latest
git ls-files -z '*.sh' |
	xargs -0 -r shfmt -l -w
