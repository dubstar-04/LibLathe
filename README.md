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

Native C++ types live in the `liblathe` namespace, for example `liblathe::Point`.
Python module and class names are unchanged. Rebuild all five native extensions
together when updating the native headers.

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

The [native stock tests](tests/native/stock_preview.cpp) cover stock subtraction,
boundary export and randomized occupancy checks. Build/run instructions are in
the file header.

## Design

Part profiles are lines and arcs in X (radius) and Z (axis). The C++ geometry
core is exposed to Python with pybind11. Shared geometry facilities include
tool-footprint defeaturing, signed-distance offsets, adaptive sampling and
sweep validation.

Tool outlines use coordinates relative to the caller's chosen tool datum.
The caller supplies the physical orientation and coordinate frame; generated
paths position that datum.

See [ARCHITECTURE.md](ARCHITECTURE.md) for design details and trade-offs, and
the [tooling manual](docs/source/pages/liblathe_tooling.rst) for coordinate
conventions and tool geometry.

## Remaining-stock guide

An advisory 2D preview shows predicted material remaining after generated cuts.
It does not change toolpaths or verify clearance.
See the [remaining-stock documentation](docs/source/pages/remaining_stock.rst).

## Limitations

Generated geometry, toolpaths and stock previews are experimental, not machining
approval. They do not certify complete machine, holder or fixture clearance,
travel from an unknown initial position, or machining safety. The caller must
validate tool setup, cutting parameters and postprocessed output for the machine.

## Links
* Docs: https://liblathe.readthedocs.io/en/latest
* CNC: https://en.wikipedia.org/wiki/Numerical_control
* GCode: https://en.wikipedia.org/wiki/G-code
* PyPi: https://pypi.org/project/liblathe/
