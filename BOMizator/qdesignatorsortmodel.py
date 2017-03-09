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
Implements custom sorting to take into account designators
"""

from PyQt4 import QtGui
from .qdesignatorcomparator import QDesignatorComparator


class QDesignatorSortModel(QtGui.QSortFilterProxyModel):
    """ Reimplements sorting of the treeview such, that designator and
    values numbers are properly sorted according to 'normal'
    perception. Hence U1, U2, U3 and not U1, U10, U11 as by default.
    """

    def __init__(self, designatorColumn=0, parent=None):
        """ sorting proxy assures that designators are correctly
        sorted. For this give a column number, which contains
        designators. This is to identify whether ordinary sorting or
        string sorting has to be done
        """
        super(QDesignatorSortModel, self).__init__(parent)
        self.comparator = QDesignatorComparator()
        self.column = designatorColumn

    def lessThan(self, left, right):
        """ makes comparison of two numbers/strings. We have to detect
        numbers in these things. The items given are modelindices IN
        PROXY, hence have to be translated to proper model. The
        left/right might be identified as QModexIndex as well, in this
        case we translate them to appropriate data strings
        """
        # left and right can contain multiple designators separated
        # comma. If this is the case, we consider for comparison only
        # the first designator as it is expected that the others are
        # in the order of sorting already put as keys
        a = left.data().split(",")[0]
        b = right.data().split(",")[0]
        desigs = list(map(
            self.comparator.getNormalisedDesignator,
            [a, b]))
        # all other cases just simple textual comparison
        print(desigs)
        return desigs[0] < desigs[1]
