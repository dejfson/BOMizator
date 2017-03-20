#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(name='BOMizator',
      version='0.1',
      packages=['BOMizator', ],
      description="KiCad BOM to suppliers linker",
      author='David Belohrad',
      author_email='david.belohrad@cern.ch',
      install_requires=['bs4', 'urllib3', 'html5lib', 'PyQt5'],
      scripts=['bin/bomizator', ])
