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

set(3RD_PARTY_FIND_PROGRAM_HINTS
    # find_program HINTS for Doxygen
    # https://gitlab.kitware.com/cmake/cmake/-/blob/master/Modules/FindDoxygen.cmake
    "[HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\doxygen_is1;Inno Setup: App Path]/bin"
    /Applications/Doxygen.app/Contents/Resources
    /Applications/Doxygen.app/Contents/MacOS
    /Applications/Utilities/Doxygen.app/Contents/Resources
    /Applications/Utilities/Doxygen.app/Contents/MacOS
    # find_program HINTS for Dia
    # https://gitlab.kitware.com/cmake/cmake/-/blob/master/Modules/FindDoxygen.cmake
    "$ENV{ProgramFiles}/Dia"
    "$ENV{ProgramFiles\(x86\)}/Dia"
    # find_program HINTS for Graphviz
    # https://gitlab.kitware.com/cmake/cmake/-/blob/master/Modules/FindDoxygen.cmake
    "$ENV{ProgramFiles}/ATT/Graphviz/bin"
    "C:/Program Files/ATT/Graphviz/bin"
    "[HKEY_LOCAL_MACHINE\\SOFTWARE\\ATT\\Graphviz;InstallPath]/bin"
    /Applications/Graphviz.app/Contents/MacOS
    /Applications/Utilities/Graphviz.app/Contents/MacOS
)
