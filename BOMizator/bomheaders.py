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
Class of constants
"""
from PyQt5 import QtCore
from .headerbase import headerbase


class bomheaders(headerbase):
    # this class declares how to display the data. First text
    # references to assure that all parties are talking the same
    # dictionary keys
    DESIGNATORS = "Designators"
    MULTIPLYFACTOR = "Multiplier"
    ADDFACTOR = "Adder"
    LIBREF = "LibRef"
    VALUE = "Value"
    MANUFACTURER = "Manufacturer"
    MFRNO = "Mfr. no"
    SUPPLIER = "Supplier"
    SUPPNO = "Supplier no"
    DATASHEET = "Datasheet"
    TOTAL = "Total"
    POLICY = "Rounding Policy"

    # itemenabled is the enable/disable flag associated with a
    # particular modelindex. We can get the info about it just by
    # calling data
    ItemIsSupplier = QtCore.Qt.UserRole + 2

    def __init__(self):
        """ fills in the header structure and handles treatment of headers
        """
        super(bomheaders, self).__init__()
        # now definition of view properties in QListView. Column
        # identifies how the columns should be sorted in the QTreeView
        self.HEADER = {self.DESIGNATORS: {"column": 0,
                                          "flags": QtCore.Qt.NoItemFlags},
                       self.MULTIPLYFACTOR: {"column": 1,
                                             "flags": QtCore.Qt.ItemIsEditable},
                       self.ADDFACTOR: {"column": 2,
                                        "flags": QtCore.Qt.ItemIsEditable},
                       self.TOTAL: {"column": 3,
                                    "flags": QtCore.Qt.ItemIsEditable},
                       self.SUPPNO: {"column": 4,
                                     "flags": QtCore.Qt.NoItemFlags},
                       self.LIBREF: {"column": 5,
                                     "flags": QtCore.Qt.NoItemFlags},
                       self.VALUE: {"column": 6,
                                    "flags": QtCore.Qt.NoItemFlags},
                       self.MANUFACTURER: {"column": 7,
                                           "flags": QtCore.Qt.NoItemFlags},
                       self.MFRNO: {"column": 8,
                                    "flags": QtCore.Qt.NoItemFlags},
                       self.DATASHEET: {"column": 9,
                                        "flags": QtCore.Qt.NoItemFlags}}
