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


class headers(headerbase):
    # this class declares how to display the data. First text
    # references to assure that all parties are talking the same
    # dictionary keys
    DESIGNATOR = "Designator"
    DESIGNATORS = "Designators"
    MULTIPLYFACTOR = "Multiplier"
    ADDFACTOR = "Adder"
    LIBREF = "LibRef"
    VALUE = "Value"
    FOOTPRINT = "Footprint"
    MANUFACTURER = "Manufacturer"
    MFRNO = "Mfr. no"
    SUPPLIER = "Supplier"
    SUPPNO = "Supplier no"
    DATASHEET = "Datasheet"
    TOTAL = "Total"
    POLICY = "Rounding Policy"

    # list defining names of all columns which uniquely identify the
    # component
    UNIQUEITEM = [LIBREF,
                  VALUE,
                  FOOTPRINT]

    # this list defines all items which are added by user
    USERITEMS = [MANUFACTURER,
                 MFRNO,
                 SUPPLIER,
                 SUPPNO,
                 DATASHEET]

    # itemenabled is the enable/disable flag associated with a
    # particular modelindex. We can get the info about it just by
    # calling data
    ItemEnabled = QtCore.Qt.UserRole + 1

    # this header is used for
    BOMHEADER = {DESIGNATORS: {"column": 0,
                               "flags": QtCore.Qt.NoItemFlags},
                 MULTIPLYFACTOR: {"column": 1,
                                  "flags": QtCore.Qt.ItemIsEditable},
                 ADDFACTOR: {"column": 2,
                             "flags": QtCore.Qt.ItemIsEditable},
                 TOTAL: {"column": 3,
                         "flags": QtCore.Qt.NoItemFlags},
                 SUPPNO: {"column": 4,
                          "flags": QtCore.Qt.ItemIsEditable},
                 LIBREF: {"column": 5,
                          "flags": QtCore.Qt.NoItemFlags},
                 VALUE: {"column": 6,
                         "flags": QtCore.Qt.NoItemFlags},
                 MANUFACTURER: {"column": 7,
                                "flags": QtCore.Qt.NoItemFlags},
                 MFRNO: {"column": 8,
                         "flags": QtCore.Qt.NoItemFlags},
                 DATASHEET: {"column": 9,
                             "flags": QtCore.Qt.NoItemFlags}}

    def __init__(self):
        super(headers, self).__init__()
        # now definition of view properties in QListView. Column
        # identifies how the columns should be sorted in the QTreeView
        self.HEADER = {self.DESIGNATOR: {"column": 0,
                                         "flags": QtCore.Qt.ItemIsDropEnabled},
                       self.LIBREF: {"column": 1,
                                     "flags": QtCore.Qt.NoItemFlags},
                       self.VALUE: {"column": 2,
                                    "flags": QtCore.Qt.NoItemFlags},
                       self.FOOTPRINT: {"column": 3,
                                        "flags": QtCore.Qt.NoItemFlags},
                       self.MANUFACTURER: {"column": 4,
                                           "flags": QtCore.Qt.ItemIsEditable},
                       self.MFRNO: {"column": 5,
                                    "flags": QtCore.Qt.ItemIsEditable},
                       self.SUPPLIER: {"column": 6,
                                       "flags": QtCore.Qt.ItemIsEditable},
                       self.SUPPNO: {"column": 7,
                                     "flags": QtCore.Qt.ItemIsEditable},
                       self.DATASHEET: {"column": 8,
                                        "flags": QtCore.Qt.ItemIsEditable}}
