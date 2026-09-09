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
    ("star", "True", "True"),
    ("tcp-large-transfer", "True", "True"),
    ("tcp-star-server", "True", "True"),
    ("tcp-variants-comparison", "True", "True"),
    (
        "tcp-validation --firstTcpType=dctcp --linkRate=50Mbps --baseRtt=10ms --queueUseEcn=1 --stopTime=15s --validate=dctcp-10ms",
        "True",
        "True",
    ),
    (
        "tcp-validation --firstTcpType=dctcp --linkRate=50Mbps --baseRtt=80ms --queueUseEcn=1 --stopTime=40s --validate=dctcp-80ms",
        "True",
        "True",
    ),
    (
        "tcp-validation --firstTcpType=cubic --linkRate=50Mbps --baseRtt=50ms --queueUseEcn=0 --stopTime=20s --validate=cubic-50ms-no-ecn",
        "True",
        "True",
    ),
    (
        "tcp-validation --firstTcpType=cubic --linkRate=50Mbps --baseRtt=50ms --queueUseEcn=1 --stopTime=20s --validate=cubic-50ms-ecn",
        "True",
        "True",
    ),
]

# A list of Python examples to run in order to ensure that they remain
# runnable over time.  Each tuple in the list contains
#
#     (example_name, do_run).
#
# See test.py for more information.
python_examples = []
