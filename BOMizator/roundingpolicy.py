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
Class taking care about rounding policy for given item.
"""


class roundingPolicy(object):
    """ takes input integer number, and rounds it according to a
    selected policy, which is defined as two numbers: 1,2,5 and then
    power-of-ten multiplicator. Hence (2, 3) = rounding to nearest
    1000. Note that this is not mathematical rounding. This rounding
    function _always returns value greated than original number_
    """

    def __init__(self, rp=(1, 0)):
        """ default rounding policy is unitary
        """
        self.rp = rp
        self.setBase()

    def setBase(self):
        """ based on contructor RP the base is returned. RP is tuple
        of (basenumber, power)
        """
        self.base = self.rp[0]*pow(10, self.rp[1])

    def myround(self, x, base=5):
        # http://stackoverflow.com/questions/2272149/round-to-5-or-other-number-in-python
        d, m = divmod(x, base)
        if m == 0:
            return d * base
        else:
            return (d + 1) * base

    def __call__(self, value):
        return self.myround(value, self.base)
