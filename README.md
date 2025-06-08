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

