cmake_minimum_required(VERSION 2.8.12)
project(liblathe)

find_package(PythonInterp REQUIRED)
include_directories(${PYTHON_INCLUDE_DIRS})

add_subdirectory(extern/pybind11)
add_subdirectory(liblathe/base)
