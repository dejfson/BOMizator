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
implements base class for the I/O access to the components cache
"""


class cacheExceptionImplement(Exception):
    pass


class cacheIOAccess(object):
    """ defines base class for cache access. Does nothing except of
    implementation of basic methods
    """

    def __init__(self, fname=None):
        self.filename = fname

    def load(self):
        """ generic load function
        """
        raise cacheExceptionImplement("Not implemented")

    def validate(self):
        """ not implemented, but should return True if fname is valid
        to perform load/save operations on it
        """
        raise cacheExceptionImplement("Not implemented")

    def create(self, fname):
        """ responsible for creation of a completely new IO
        """
        raise cacheExceptionImplement("Not implemented")

    def save(self):
        """ generic save function
        """
        raise cacheExceptionImplement("Not implemented")

    def name(self):
        raise cacheExceptionImplement("Not implemented")


# do not declare the default class name, as this is purely virtual
# implementation
DEFAULT_CLASS = None
