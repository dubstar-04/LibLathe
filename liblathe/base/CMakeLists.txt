cmake_minimum_required(VERSION 3.5)
# pybind11_add_module(sdf sdf.cpp)

pybind11_add_module(quadtree quadtree_py.cpp quadtree.cpp point.cpp)
pybind11_add_module(point point_py.cpp point.cpp)
pybind11_add_module(boundbox boundbox_py.cpp boundbox.cpp point.cpp)
pybind11_add_module(segment segment_py.cpp segment.cpp boundbox.cpp point.cpp)
pybind11_add_module(segmentgroup segmentgroup_py.cpp segmentgroup.cpp segment.cpp boundbox.cpp point.cpp)


