#!/usr/bin/env python
# -*- coding: utf-8 -*-

import io
import os
from setuptools import find_packages, setup

# Package meta-data.
NAME = 'Filo Blu Service Project'
DESCRIPTION = 'Filo Blu Service: database connector and processing of patients messages.'
URL = 'https://github.com/Nico-Curti/FiloBlu'
EMAIL = 'nico.curti2@unibo.it'
AUTHOR = ['Nico Curti', 'Andrea Ciardiello', 'Stefano Giagu']
REQUIRES_PYTHON = '>=3.5'
VERSION = None
KEYWORDS = "query windows-service"

# What packages are required for this module to be executed?
def get_requires():
  with open('requirements.txt', 'r') as f:
    requirements = f.read()
  return list(filter(lambda x: x != '', requirements.split()))

# What packages are optional?
EXTRAS = {
  'tests': [],
}


here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
  with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = '\n' + f.read()
except FileNotFoundError:
  long_description = DESCRIPTION

# Load the package's __version__.py module as a dictionary.
about = {}
if not VERSION:
  with open(os.path.join(here, 'FiloBlu', '__version__.py')) as f:
    exec(f.read(), about)
else:
  about['__version__'] = VERSION

# Where the magic happens:
setup(
  name=NAME,
  version=about['__version__'],
  description=DESCRIPTION,
  long_description=long_description,
  long_description_content_type='text/markdown',
  author=AUTHOR,
  author_email=EMAIL,
  maintainer=AUTHOR,
  maintainer_email=EMAIL,
  python_requires=REQUIRES_PYTHON,
  url=URL,
  download_url=URL,
  keywords=KEYWORDS,
  packages=find_packages(include=['FiloBlu', 'FiloBlu.*'], exclude=('wip', 'data',)),
  install_requires=get_requires(),
  extras_require=EXTRAS,
  include_package_data=True,
  license='MIT "Expat" License (Copyright (c) 2019: Nico Curti)',
  platforms='any',
  classifiers=[
    'License :: OSI Approved :: MIT "Expat" License',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: Implementation :: CPython',
    'Programming Language :: Python :: Implementation :: PyPy'
  ],
)
