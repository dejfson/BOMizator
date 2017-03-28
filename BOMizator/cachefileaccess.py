#!/usr/bin/env python
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
implements FILE access to the cache. Hence load/save operations over
the cache file
"""
from BOMizator.cacheioaccess import cacheIOAccess
import os
import json


class cacheFileAccess(cacheIOAccess):

    def __init__(self, fname=None):
        super(cacheFileAccess, self).__init__(fname)

    def __str__(self):
        return "file " + self.filename

    def validate(self):
        """ file access validation returns true if the file exists
        """
        return os.path.isfile(self.filename)

    def load(self):
        """ loads and returns the cache from the file
        """
        # load the complete dictionary if exists. (either in
        # project directory, or if generally specified)
        try:
            with open(self.filename) as data_file:
                componentsCache = json.load(data_file)
        except FileNotFoundError:
            componentsCache = {}
        return componentsCache

    def save(self, data):
        """ saves the cache to the disk
        """
        with open(self.filename, 'wt') as outfile:
            json.dump(data, outfile)

    def name(self):
        return "File"


DEFAULT_CLASS = cacheFileAccess
