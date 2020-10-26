"""
Automate publishing liblathe to https://pypi.org/
"""

import os
<<<<<<< HEAD
import subprocess
import shutil
import re

VERSIONFILE = 'liblathe/version.py'

version_line = open(VERSIONFILE).read()
=======
import shutil
import re

__dir__ = os.path.dirname(__file__)

# cd to the liblathe directory
os.chdir(__dir__)
version_file = os.path.join(__dir__, "liblathe/version.py")

version_line = open(version_file).read()
>>>>>>> b473a59d85cf841661d94656f4ad7f0b36deb94c
version_re = r"^__version__ = ['\"]([^'\"]*)['\"]"
match = re.search(version_re, version_line, re.M)
if match:
    version = match.group(1)
else:
<<<<<<< HEAD
    raise RuntimeError("Could not find version in '%s'" % VERSIONFILE)
=======
    raise RuntimeError("Could not find version in '%s'" % version_file)
>>>>>>> b473a59d85cf841661d94656f4ad7f0b36deb94c

current_branch = os.popen("git branch --show-current").read().strip()
commit_count = os.popen("git rev-list --count master").read().strip()
origin_commit_count = os.popen("git rev-list --count origin master").read().strip()
print('git branch:', current_branch, 'rev:', commit_count, 'origin rev:', origin_commit_count)

mode = input("Select a mode 0 = testing, 1 = production 2 = dryrun:")
if mode == "0" or mode == "2":
    testing = True
elif mode == "1":
    testing = False
else:
    raise RuntimeError("unknown mode selected")

if mode != "2":
    if current_branch != "master":
        raise RuntimeError("incorrect branch. please check out master")

    if commit_count != origin_commit_count:
        raise RuntimeError("branch out of date")

version_check = input("build at version: '%s' y/n: " % version)

if version_check.upper() == "N":
    raise RuntimeError("version check rejected")
elif version_check.upper() == "Y":
    pass
else:
    raise RuntimeError("version check failed, unknown response")

# create the python package
<<<<<<< HEAD
os.system("python setup.py sdist")

# install twine
os.system("pip install twine")
=======
setup_file = os.path.join(__dir__, "setup.py")
os.system("python %s sdist" % setup_file)

# install twine
os.system("pip3 install twine")
>>>>>>> b473a59d85cf841661d94656f4ad7f0b36deb94c

if mode == "0" or mode == "1":
    # upload the file to the selected index
    if testing:
<<<<<<< HEAD
        os.system("twine upload --repository testpypi dist/*")
    else:
        os.system("twine upload --repository pypi dist/*")

__dir__ = os.path.dirname(__file__)
dist = os.path.join(__dir__, "/dist")
=======
        print('publish to https://test.pypi.org/')
        os.system("python -m twine upload --repository testpypi dist/*")
    else:
        print('publish to https://pypi.org/')
        os.system("python -m twine upload --repository pypi dist/*")


dist = os.path.join(__dir__, "dist")
>>>>>>> b473a59d85cf841661d94656f4ad7f0b36deb94c
egginfo = os.path.join(__dir__, "liblathe.egg-info")
clearBuildFiles = input("clear build files? y/n: ")

if clearBuildFiles.upper() == "Y":
    if os.path.exists(dist):
        print('removing', dist)
        shutil.rmtree(dist)
    if os.path.exists(egginfo):
        print('removing', egginfo)
        shutil.rmtree(egginfo)
