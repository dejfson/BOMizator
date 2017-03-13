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
provides convenience functions for declaration of headers for item models
"""
from operator import itemgetter


class headerbase(object):
    """ class defining convenience functions to access models headers
    """
    def __init__(self):
        self.HEADER = {}

    def getHeaders(self):
        """ returns list of headers sorted by columns
        """
        namecol = map(lambda c: (c[0], c[1]['column']), self.HEADER.items())
        namecol = sorted(namecol, key=itemgetter(1))
        names = map(lambda c: c[0], namecol)
        return list(names)

    def getColumns(self, collist):
        """ returns unsorted list of columns identified by collist names
        """
        return map(lambda item: self.HEADER[item]['column'], collist)

    def getColumn(self, columnname):
        """ returns column number if given a name
        """
        return self.HEADER[columnname]['column']

    def __len__(self):
        """ returns number of headers defined in this class
        """
        return len(self.HEADER)

    def getColumnName(self, column):
        """ returns name of the column, uniqueness in column
        definitions is expected (so no columns with the same number in
        self.HEADER)
        """
        try:
            a = filter(lambda c: self.HEADER[c]['column'] == column,
                       self.HEADER)
            return list(a)[0]
        except IndexError:
            # sometimes column == -1 when model is not able to
            # identify which column we're sitting on. in this case we
            # return empty string
            raise KeyError

    def getFlags(self, column):
        """ for specific column we return QTreeView flags appropriate
        for that column. The flags are part of the HEADER dictionary
        and allow to specify which columns are droppable, and which
        are read only
        """
        return self.HEADER[self.getColumnName(column)]['flags']
