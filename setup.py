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
      include_package_data=True,
      data_files=[('BOMizator', ['BOMizator/BOMLinker.ui', ]),
                  ('BOMizator/suppliers', ['BOMizator/suppliers/radiospares.py',
                                         'BOMizator/suppliers/farnell.py'])],
      entry_points={
          'gui_scripts': [
              'bomizator = BOMizator.__main__:main'
              ]
      })
