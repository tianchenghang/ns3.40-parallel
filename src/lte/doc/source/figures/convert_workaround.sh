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

mkdir TempOutput
for f in *.dia; do
	echo "converting - $f"
	s=${f%.dia}
	dia --export $s.eps $f
	mv $s.eps TempOutput
done

cd TempOutput
mkdir PNG
for f in *.eps; do
	echo "converting - $f"
	s=${f%.eps}
	convert $f $s.png
	mv $s.png PNG
done
