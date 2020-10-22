import re
from setuptools import setup
import warnings
import sys
from os import path

if sys.version_info[:3] < (3, 5, 0):
    warnings.warn("liblathe does not support versions below "
                  "Python 3.5.0", RuntimeWarning)

VERSIONFILE = 'liblathe/version.py'

version_line = open(VERSIONFILE).read()
version_re = r"^__version__ = ['\"]([^'\"]*)['\"]"
match = re.search(version_re, version_line, re.M)
if match:
    version = match.group(1)
else:
    raise RuntimeError("Could not find version in '%s'" % VERSIONFILE)

this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

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
    packages=['liblathe'],
    install_requires=['pillow'],

    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
)
