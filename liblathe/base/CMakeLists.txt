cmake_minimum_required(VERSION 2.8.12)
pybind11_add_module(sdf sdf.cpp)
pybind11_add_module(quadtree quadtree.cpp)
pybind11_add_module(point point.cpp)