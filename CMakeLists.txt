cmake_minimum_required(VERSION 3.16)
project(sfrs_gem_tpc_fc_sim VERSION 0.1.0 LANGUAGES CXX)

find_package(Garfield CONFIG REQUIRED)
add_executable(tpc-field src/main.cpp)
target_compile_features(tpc-field PRIVATE cxx_std_17)
target_link_libraries(tpc-field PRIVATE Garfield::Garfield)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(tpc-field PRIVATE -Wall -Wextra -Wpedantic)
endif()

include(CTest)
if(BUILD_TESTING)
  find_package(Python3 REQUIRED COMPONENTS Interpreter)
  add_test(NAME uniform-field-validation
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tests/check_uniform.py"
      "$<TARGET_FILE:tpc-field>" "${CMAKE_CURRENT_SOURCE_DIR}/config/uniform.cfg")
  add_test(NAME elmer-import-validation
    COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tests/check_elmer.py"
      "$<TARGET_FILE:tpc-field>")
endif()
