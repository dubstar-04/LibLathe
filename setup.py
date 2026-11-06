import re
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup
import os

__dir__ = os.path.dirname(__file__)
version_file = os.path.join(__dir__, "liblathe/version.py")
liblathe_path = os.path.join(__dir__, "liblathe")
liblathe_path = os.path.abspath(liblathe_path)

version_line = open(version_file).read()
version_re = r"^__version__ = ['\"]([^'\"]*)['\"]"
match = re.search(version_re, version_line, re.M)
if match:
    version = match.group(1)
else:
    raise RuntimeError("Could not find version in '%s'" % version_file)

with open(os.path.join(__dir__, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Use one language level so Linux, macOS and Windows compilers agree
CXX_STD = 14

point = Pybind11Extension('liblathe.base.point',
                          ['liblathe/base/point_py.cpp',
                           'liblathe/base/point.cpp'],
                          cxx_std=CXX_STD)

boundbox = Pybind11Extension('liblathe.base.boundbox',
                             ['liblathe/base/boundbox_py.cpp',
                              'liblathe/base/boundbox.cpp',
                              'liblathe/base/point.cpp'],
                             cxx_std=CXX_STD)

segment = Pybind11Extension('liblathe.base.segment',
                            ['liblathe/base/segment_py.cpp',
                             'liblathe/base/segment.cpp',
                             'liblathe/base/point.cpp',
                             'liblathe/base/boundbox.cpp'],
                            cxx_std=CXX_STD)

segmentgroup = Pybind11Extension('liblathe.base.segmentgroup',
                                 ['liblathe/base/segmentgroup_py.cpp',
                                  'liblathe/base/segmentgroup.cpp',
                                  'liblathe/base/point.cpp',
                                  'liblathe/base/boundbox.cpp',
                                  'liblathe/base/segment.cpp',
                                  'liblathe/base/quadtree.cpp'],
                                 cxx_std=CXX_STD)

quadtree = Pybind11Extension('liblathe.base.quadtree',
                             ['liblathe/base/quadtree_py.cpp',
                              'liblathe/base/quadtree.cpp',
                              'liblathe/base/boundbox.cpp',
                              'liblathe/base/point.cpp',
                              'liblathe/base/segment.cpp',
                              'liblathe/base/segmentgroup.cpp'],
                             cxx_std=CXX_STD)

setup(
    name='liblathe',
    version=version,
    description='Python library for generating lathe paths and gcode ',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/dubstar-04/LibLathe',
    author='Daniel Wood',
    author_email='s.d.wood.82@googlemail.com',
    license='GPL2',
    keywords="lathe turning CAD CAM CNC",
    packages=['liblathe', "liblathe/op", "liblathe/tool", "liblathe/gcode"],
    python_requires='>=3.10',
    install_requires=['pillow'],
    ext_modules=[point, boundbox, segment, segmentgroup, quadtree],

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
        'Programming Language :: Python :: 3.14',
    ],
)
