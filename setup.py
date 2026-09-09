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

import cmake_build_extension
import setuptools
import sys
import sysconfig

setuptools.setup(
    cmdclass=dict(build_ext=cmake_build_extension.BuildExtension),
    packages=["ns", "visualizer"],
    package_dir={
        "ns": "./build-support/pip-wheel/ns",
        "visualizer": "./build-support/pip-wheel/visualizer",
    },
    ext_modules=[
        cmake_build_extension.CMakeExtension(
            name="BuildAndInstall",
            install_prefix="ns3",
            cmake_configure_options=[
                "-DCMAKE_BUILD_TYPE:STRING=release",
                "-DNS3_ASSERT:BOOL=ON",
                "-DNS3_LOG:BOOL=ON",
                "-DNS3_WARNINGS_AS_ERRORS:BOOL=OFF",
                "-DNS3_PYTHON_BINDINGS:BOOL=ON",
                "-DNS3_BINDINGS_INSTALL_DIR:STRING=INSTALL_PREFIX",
                "-DNS3_FETCH_OPTIONAL_COMPONENTS:BOOL=ON",
                "-DNS3_PIP_PACKAGING:BOOL=ON",
                "-DNS3_USE_LIB64:BOOL=ON",
                # Make CMake find python components from the currently running python
                # https://catherineh.github.io/programming/2021/11/16/python-binary-distributions-whls-with-c17-cmake-auditwheel-and-manylinux
                f"-DPython3_LIBRARY_DIRS={sysconfig.get_config_var('LIBDIR')}",
                f"-DPython3_INCLUDE_DIRS={sysconfig.get_config_var('INCLUDEPY')}",
                f"-DPython3_EXECUTABLE={sys.executable}",
            ],
        ),
    ],
)
