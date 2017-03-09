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
Implements class taking care of correct comparison between two designators
"""

import re


class InvalidDesignator(Exception):
    pass


class QDesignatorComparator(object):
    """ simple class taking two designators and doing comparison based
    on the number in the designator
    """

    def __call__(self, desig):
        """ explodes designator into the number and item, and returns
        recalculated integer such, that the designators will be
        correctly sorted
        """
        return self.getNormalisedDesignator(desig)

    def getNormalisedDesignator(self, desig):
        """ returns designator normalised for comparison
        """
        # decompose to string and number. Let's say, that the number
        # goes from 0 to 9999 as designator count. If not, then we
        # raise invalid designator
        strs1, dig1 = self.getDesignatorNumber(desig)
        if dig1 > 9999:
            print("Error")
            raise InvalidDesignator("Designator numeric value cannot\
 exceed 9999")
        # now the easy method how to accomplish this is just to round
        # the digit correctly to 5 digits and add to string and return
        # it
        return strs1 + "%05d" % (dig1)

    def getDesignatorNumber(self, designator):
        """ parses given designator and returns tuple (alphas, digit),
        which are then used for comparison. Allowed combinations:
        <multiletter_designator><number><extension>, where
        multiletter_designator is only alphas, number is 0-9 and
        extension can be whatever. Hence following is still allowed:
        Q12_a, but following is not allowed: Q_a12
        """
        if designator.find("?") != -1:
            raise InvalidDesignator()
        # for this we use simple search, assuming that there is only
        # one number in the entire designator, and the designator is
        # unique. Saying this we can search regular expression and
        # extract beginning, number and ending
        pre, dig, post = re.findall('^([A-Za-z]+)(\d+)(.*)', designator)[0]
        # first we match joned beginning and end, which are textual
        return (pre+post, int(dig))
