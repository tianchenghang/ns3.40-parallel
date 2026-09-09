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

# CMake find_package() Module for Sphinx documentation generator
# http://sphinx-doc.org/
#
# Example usage:
#
# find_package(Sphinx)
#
# If successful the following variables will be defined SPHINX_FOUND
# SPHINX_EXECUTABLE

find_program(
  SPHINX_EXECUTABLE NAMES sphinx-build sphinx-build2
  DOC "Path to sphinx-build executable"
)

# Handle REQUIRED and QUIET arguments this will also set SPHINX_FOUND to true if
# SPHINX_EXECUTABLE exists
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(
  Sphinx "Failed to locate sphinx-build executable" SPHINX_EXECUTABLE
)

# Provide options for controlling different types of output
option(SPHINX_OUTPUT_HTML "Output standalone HTML files" ON)
option(SPHINX_OUTPUT_MAN "Output man pages" ON)

option(SPHINX_WARNINGS_AS_ERRORS
       "When building documentation treat warnings as errors" ON
)
