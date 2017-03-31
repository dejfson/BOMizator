#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 David Belohrad
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA  02110-1301, USA.
#
# You can dowload a copy of the GNU General Public License here:
# http://www.gnu.org/licenses/gpl.txt
#
# Author: David Belohrad
# Email:  david.belohrad@cern.ch
#

"""
Setuptools script for bomizator
"""

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
      data_files=[('BOMizator', ['BOMizator/BOMLinker.ui', ])],
      scripts=['bin/bomizator', ])
      entry_points={
          'gui_scripts': [
              'bomizator = BOMizator.__main__:main'
              ]
      })
