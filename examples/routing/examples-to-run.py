#! /usr/bin/env python3
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


# A list of C++ examples to run in order to ensure that they remain
# buildable and runnable over time.  Each tuple in the list contains
#
#     (example_name, do_run, do_valgrind_run).
#
# See test.py for more information.
cpp_examples = [
    ("dynamic-global-routing", "True", "True"),
    ("global-injection-slash32", "True", "True"),
    ("global-routing-slash32", "True", "True"),
    ("mixed-global-routing", "True", "True"),
    ("simple-alternate-routing", "True", "True"),
    ("simple-global-routing", "True", "True"),
    ("simple-routing-ping6", "True", "True"),
    ("static-routing-slash32", "True", "True"),
]

# A list of Python examples to run in order to ensure that they remain
# runnable over time.  Each tuple in the list contains
#
#     (example_name, do_run).
#
# See test.py for more information.
python_examples = [
    ("simple-routing-ping6.py", "True"),
]
