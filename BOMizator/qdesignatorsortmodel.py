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
from .headers import headers
import re

class QDesignatorSortModel(QtGui.QSortFilterProxyModel):
    """ Reimplements sorting of the treeview such, that designator and
    values numbers are properly sorted according to 'normal'
    perception. Hence U1, U2, U3 and not U1, U10, U11 as by default.
    """

    def __init__(self, parent=None):
        """ creates headers object used for comparison
        """
        super(QDesignatorSortModel, self).__init__(parent)
        self.header = headers()

    def getText(self, left):
        """ returns text from the modelindex data
        """
        return left.model().itemFromIndex(left).text()

    def getDesignatorNumber(self, designator):
        """ parses given designator and returns tuple (alphas, digit),
        which are then used for comparison. Allowed combinations:
        <multiletter_designator><number><extension>, where
        multiletter_designator is only alphas, number is 0-9 and
        extension can be whatever. Hence following is still allowed:
        Q12_a, but following is not allowed: Q_a12
        """
        # for this we use simple search, assuming that there is only
        # one number in the entire designator, and the designator is
        # unique. Saying this we can search regular expression and
        # extract beginning, number and ending
        pre, dig, post = re.findall('^([A-Za-z]+)(\d+)(.*)', designator)[0]
        # first we match joned beginning and end, which are textual
        return (pre+post, int(dig))

    def compareDesignators(self, left, right):
        """ parses numbers from designators and returns which of them
        is larger
        """
        strs1, dig1 = self.getDesignatorNumber(self.getText(left))
        strs2, dig2 = self.getDesignatorNumber(self.getText(right))

        # if strings differ, return their difference:
        if strs1 != strs2:
            return strs1 < strs2

        # if strings are the same, compare _numerically_ the results
        return dig1 < dig2

    def lessThan(self, left, right):
        """ makes comparison of two numbers/strings. We have to detect
        numbers in these things. The items given are modelindices
        """
        # having modelindices we can grab the text and check for
        # results depending of _column_.
        # if column is designator, we parse the data as
        # <chars><number> and sort according to number as integer
        if left.column() == self.header.get_column(
                self.header.DESIGNATOR):
            return self.compareDesignators(left, right)

        # all other cases just simple textual comparison
        return self.getText(left) < self.getText(right)
