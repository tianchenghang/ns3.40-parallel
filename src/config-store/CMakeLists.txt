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

if(${GTK3_FOUND})
  set(gtk3_sources
      model/display-functions.cc
      model/gtk-config-store.cc
      model/model-node-creator.cc
      model/model-typeid-creator.cc
  )

  set(gtk3_headers
      model/gtk-config-store.h
  )
  set(gtk_libraries
      ${GTK3_LIBRARIES}
  )
  if(${NS3_PIP_PACKAGING})
    # In case we are packaging ns-3, leave gtk symbols undefined and pray for
    # the linker to find the correct libraries locally
    set(gtk_libraries
        -Wl,--allow-shlib-undefined
    )
  endif()
  if(${GCC})
    add_definitions(-Wno-parentheses)
  endif()
endif()

if(${LIBXML2_FOUND})
  set(xml2_sources
      model/xml-config.cc
  )
  set(xml2_libraries
      ${LIBXML2_LIBRARIES}
  )
endif()

build_lib(
  LIBNAME config-store
  SOURCE_FILES
    ${gtk3_sources}
    ${xml2_sources}
    model/attribute-default-iterator.cc
    model/attribute-iterator.cc
    model/config-store.cc
    model/file-config.cc
    model/raw-text-config.cc
  HEADER_FILES
    ${gtk3_headers}
    model/file-config.h
    model/config-store.h
  LIBRARIES_TO_LINK
    ${libcore}
    ${libnetwork}
    ${xml2_libraries}
    ${gtk_libraries}
)
