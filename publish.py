"""
Automate publishing liblathe to https://pypi.org/
"""

import os
import subprocess
import shutil
import re

VERSIONFILE = 'liblathe/version.py'

version_line = open(VERSIONFILE).read()
version_re = r"^__version__ = ['\"]([^'\"]*)['\"]"
match = re.search(version_re, version_line, re.M)
if match:
    version = match.group(1)
else:
    raise RuntimeError("Could not find version in '%s'" % VERSIONFILE)

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
os.system("python setup.py sdist")

# install twine
os.system("pip install twine")

if mode == "0" or mode == "1":
    # upload the file to the selected index
    if testing:
        os.system("twine upload --repository testpypi dist/*")
    else:
        os.system("twine upload --repository pypi dist/*")

__dir__ = os.path.dirname(__file__)
dist = os.path.join(__dir__, "/dist")
egginfo = os.path.join(__dir__, "liblathe.egg-info")
clearBuildFiles = input("clear build files? y/n: ")

if clearBuildFiles.upper() == "Y":
    if os.path.exists(dist):
        print('removing', dist)
        shutil.rmtree(dist)
    if os.path.exists(egginfo):
        print('removing', egginfo)
        shutil.rmtree(egginfo)
