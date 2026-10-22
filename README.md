# LibLathe [![Python package](https://github.com/dubstar-04/LibLathe/workflows/Python%20package/badge.svg?branch=master)](https://github.com/dubstar-04/LibLathe/actions) [![codecov](https://codecov.io/gh/dubstar-04/LibLathe/branch/master/graph/badge.svg?token=08V04GX1FK)](https://codecov.io/gh/dubstar-04/LibLathe/branch/master/) [![PyPI](https://img.shields.io/pypi/v/liblathe)](https://pypi.org/project/liblathe/) ![Python versions](https://img.shields.io/pypi/pyversions/liblathe)

LibLathe is an opensource standalone python library for generating turning paths and gcode for use with cnc lathes.

| :warning: WARNING: LibLathe is currently experimental / Proof of concept and only suitable for testing. |

## Installation
Installing liblathe from PYPI
```
pip install liblathe
```

Local install for testing
```
pip install .
```

:warning: Some systems require that packages are system installed. Liblathe can be installed for development purposes.
Note: This may break your system
```
pip install . --break-system-packages
pip uninstall liblathe --break-system-packages
```

## Build
Liblathe is a python library with a C++ core. Liblathe core can be compiled and tested inplace using the following steps:
```
cd Liblathe
cmake .
make
```

Local testing
```
python3 ./examples/defeature_example.py
```

## Tests

After building, run the Python suite with `pytest --ignore=extern`, as used by
the test workflows. These tests exercise the compiled C++ core through Python.

The [native memory driver](tests/native/quadtree_memory.cpp) is an optional
diagnostic for investigating C++ memory issues, not a required test or CI step.
Its header contains the manual build and sanitizer instructions.

## Design
Part profiles are lines and arcs in X (radius) and Z (axis). LibLathe plans cuts in two geometry steps:

1. **Defeature:** the tool is moved along the part and only the area it can actually reach is kept, removing features that can't be turned, such as undercuts.
2. **Offset:** a signed distance field (SDF) gives the distance from any point to the profile. A quadtree samples it, refining only near the target distance. Points at that distance are collected, ordered and simplified with the Ramer-Douglas-Peucker (RDP) algorithm into the offset path.

The operations (face, rough, profile and part-off) combine these steps into toolpaths and gcode. The geometry core is C++ exposed to Python with pybind11.

The SDF uses the profile closed back to X = 0: sign and distance include the
same boundary. Artificial closing edges do not generate offset candidates;
faces explicitly included in the profile remain eligible. The existing
start-Z clip is retained. In LibLathe's plotted view, Z is horizontal and X
increases downward from the centreline.

See [ARCHITECTURE.md](ARCHITECTURE.md) for the trade-offs and alternative approaches.

## Examples
### Facing:
![Facing Example](https://github.com/dubstar-04/LibLathe/blob/master/docs/source/LL_static/images/FacingOp.jpeg)

### Roughing:
![Roughing Example](https://github.com/dubstar-04/LibLathe/blob/master/docs/source/LL_static/images/RoughingOp.jpeg)

### Profiling:
![Profiling Example](https://github.com/dubstar-04/LibLathe/blob/master/docs/source/LL_static/images/ProfilingOp.jpeg)

### Parting:
![Parting Example](https://github.com/dubstar-04/LibLathe/blob/master/docs/source/LL_static/images/PartingOp.jpeg)

## Links
* Docs: https://liblathe.readthedocs.io/en/latest
* CNC: https://en.wikipedia.org/wiki/Numerical_control
* GCode: https://en.wikipedia.org/wiki/G-code
* PyPi: https://pypi.org/project/liblathe/
