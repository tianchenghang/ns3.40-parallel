cmake_minimum_required(VERSION 3.16)
project(ieg VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

set(IEG_SOURCES
  src/file_resolver.cpp
  src/validator.cpp
  src/crypto.cpp
  src/csv_parser.cpp
  src/c_api.cpp
)

add_library(ieg_lib STATIC ${IEG_SOURCES})
target_include_directories(ieg_lib PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)

add_library(ieg_shared SHARED ${IEG_SOURCES})
target_include_directories(ieg_shared PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/include)
set_target_properties(ieg_shared PROPERTIES
  OUTPUT_NAME ieg
  CXX_VISIBILITY_PRESET hidden
  VISIBILITY_INLINES_HIDDEN ON
)

add_executable(ieg src/main.cpp)
target_link_libraries(ieg PRIVATE ieg_lib)

# clang-format target
find_program(CLANG_FORMAT clang-format)
if(CLANG_FORMAT)
  file(GLOB_RECURSE IEG_ALL_SOURCES
    ${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp
    ${CMAKE_CURRENT_SOURCE_DIR}/include/*.h
  )
  add_custom_target(format
    COMMAND ${CLANG_FORMAT} -i -style=LLVM ${IEG_ALL_SOURCES}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Running clang-format"
  )
  add_custom_target(format-check
    COMMAND ${CLANG_FORMAT} --dry-run --Werror -style=LLVM ${IEG_ALL_SOURCES}
    WORKING_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR}
    COMMENT "Checking clang-format"
  )
endif()
