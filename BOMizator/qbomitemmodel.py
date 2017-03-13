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
Implements model for BOM treeView, which displays the data grouped by
supplier and components grouped by reference number rather than
designators. This is the view, which allows to easily come out with
bill of material usable to directly order the components
"""

from PyQt4 import QtGui


class QBOMItemModel(QtGui.QStandardItemModel):
    """ provides model for BOM data
    """
    def __init__(self, sourceData, parent=None):
        super(QBOMItemModel, self).__init__(parent)
        self.SCH = sourceData
        # the point here: we generate a model,which has left-most set
        # of designators, followed by multiply, add
        sorted_header = self.header.getBOMHeaders()
        self.setHorizontalHeaderLabels(sorted_header)
