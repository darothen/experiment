#!/usr/bin/env python

import os
import warnings

from setuptools import setup, find_packages

DESCRIPTION = "Organizing numerical model experiment output"
LONG_DESCRIPTION = """\
**Experiment** is designed to make it easier to ingest and process the sort of repeated simulations with numerical models that are used in many different fields of science. Although initially designed/intended for use with climate model output archived on desk in hierarchical folders containing NetCDF_ output, it's designed to be more flexible and useful for other applications.

The core functionality of Experiment are:

1. Ingest model output that has been organized to reflect the design of the experiment which produed it
2. Use metadata to align data/output across the experimental design
3. Process data using lazy and out-of-core toolkits to simplify analysis
4. Provide multiple backends for reading datasets (hierarchical folders, databases, etc) of different datatypes (NetCDF_, CSV, binary, etc)

.. _NetCDF: http://www.unidata.ucar.edu/software/netcdf

"""

DISTNAME = "experiment"
AUTHOR = "Daniel Rothenberg"
AUTHOR_EMAIL = "darothen@mit.edu"
URL = ""
LICENSE = "MIT"
DOWNLOAD_URL = "https://github.com/darothen/experiment/"

CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'License :: OSI Approved :: MIT License',
    'Operating System :: OS Independent',
    'Intended Audience :: Science/Research',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3.5',
    'Topic :: Scientific/Engineering',

]

MAJOR = 0
MINOR = 0
MICRO = 1
VERSION = "{}.{}.{}".format(MAJOR, MINOR, MICRO)
DEV = True


# Correct versioning with git info if DEV
if DEV:
    import subprocess

    pipe = subprocess.Popen(
        ['git', "describe", "--always", "--match", "v[0-9]*"],
        stdout=subprocess.PIPE)
    so, err = pipe.communicate()

    if pipe.returncode != 0:
        # no git or something wrong with git (not in dir?)
        warnings.warn("WARNING: Couldn't identify git revision, using generic version string")
        VERSION += ".dev"
    else:
        git_rev = so.strip()
        git_rev = git_rev.decode('ascii') # necessary for Python >= 3

        VERSION += ".dev-{}".format(git_rev)

def _write_version_file():

    fn = os.path.join(os.path.dirname(__file__), 'pyrcel', 'version.py')

    version_str = dedent("""
        __version__ = '{}'
        """)

    # Write version file
    with open(fn, 'w') as version_file:
        version_file.write(version_str.format(VERSION))

# Write version and install
_write_version_file()

setup(
    name = DISTNAME,
    author = AUTHOR,
    author_email = AUTHOR_EMAIL,
    maintainer = AUTHOR,
    maintainer_email = AUTHOR_EMAIL,
    description = DESCRIPTION,
    long_description = LONG_DESCRIPTION,
    license = LICENSE,
    url = URL,
    version = VERSION,
    download_url = DOWNLOAD_URL,

    packages = find_packages(),
    package_data = [],

    classifiers = CLASSIFIERS
)
