cmake_minimum_required(VERSION 3.20)
project(mlir_analysis_docs LANGUAGES C CXX)
find_package(MLIR REQUIRED CONFIG)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
add_executable(inspect-analysis inspect.cpp)
target_include_directories(inspect-analysis SYSTEM PRIVATE ${LLVM_INCLUDE_DIRS} ${MLIR_INCLUDE_DIRS})
add_definitions(${LLVM_DEFINITIONS})
if(NOT LLVM_ENABLE_RTTI)
  target_compile_options(inspect-analysis PRIVATE -fno-rtti)
endif()
target_link_libraries(inspect-analysis PRIVATE MLIRParser MLIRAnalysis MLIRPass
  MLIRArithDialect MLIRFuncDialect MLIRSCFDialect MLIRControlFlowDialect
  MLIRMemRefDialect MLIRIR MLIRSupport)
