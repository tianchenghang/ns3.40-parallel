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
    ("adaptive-red-tests --testNumber=1", "True", "True"),
    ("adaptive-red-tests --testNumber=2", "True", "True"),
    ("adaptive-red-tests --testNumber=3", "True", "True"),
    ("adaptive-red-tests --testNumber=4", "True", "True"),
    ("adaptive-red-tests --testNumber=6", "True", "True"),
    ("adaptive-red-tests --testNumber=7", "True", "True"),
    ("adaptive-red-tests --testNumber=8", "True", "True"),
    ("adaptive-red-tests --testNumber=9", "True", "True"),
    ("adaptive-red-tests --testNumber=10", "True", "True"),
    ("adaptive-red-tests --testNumber=11", "True", "True"),
    ("adaptive-red-tests --testNumber=12", "True", "True"),
    ("adaptive-red-tests --testNumber=13", "True", "True"),
    ("adaptive-red-tests --testNumber=14", "True", "True"),
    ("adaptive-red-tests --testNumber=15", "True", "True"),
    (
        "codel-vs-pfifo-asymmetric --routerWanQueueDiscType=PfifoFast --simDuration=10",
        "True",
        "True",
    ),
    (
        "codel-vs-pfifo-asymmetric --routerWanQueueDiscType=CoDel --simDuration=10",
        "True",
        "False",
    ),
    (
        "codel-vs-pfifo-basic-test --queueDiscType=PfifoFast --simDuration=10",
        "True",
        "False",
    ),
    (
        "codel-vs-pfifo-basic-test --queueDiscType=CoDel --simDuration=10",
        "True",
        "False",
    ),
    ("pfifo-vs-red --queueDiscType=PfifoFast", "True", "True"),
    ("pfifo-vs-red --queueDiscType=PfifoFast --modeBytes=1", "True", "False"),
    ("pfifo-vs-red --queueDiscType=RED", "True", "True"),
    ("pfifo-vs-red --queueDiscType=RED --modeBytes=1", "True", "False"),
    ("red-tests --testNumber=1", "True", "True"),
    ("red-tests --testNumber=3", "True", "False"),
    ("red-tests --testNumber=4", "True", "False"),
    ("red-tests --testNumber=5", "True", "False"),
    ("red-vs-ared --queueDiscType=RED", "True", "True"),
    ("red-vs-ared --queueDiscType=RED --modeBytes=true", "True", "False"),
    ("red-vs-ared --queueDiscType=ARED", "True", "True"),
    ("red-vs-ared --queueDiscType=ARED --modeBytes=true", "True", "False"),
]

# A list of Python examples to run in order to ensure that they remain
# runnable over time.  Each tuple in the list contains
#
#     (example_name, do_run).
#
# See test.py for more information.
python_examples = []
