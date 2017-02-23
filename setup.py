#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='farnellBOM',
      version = '0.1',
      packages = ['farnellBOM',],
      description = "KiCad BOM CSV to Farnell linker",
      author = 'David Belohrad',
      author_email = 'david.belohrad@cern.ch',
      install_requires = [],
      scripts=['bin/farnellBOM', ]
      )
