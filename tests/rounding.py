#!/usr/bin/env python3
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
Unit test for sorter
"""
import unittest
from BOMizator.roundingpolicy import roundingPolicy


class TestStringMethods(unittest.TestCase):

    def testZeroIsZero(self):
        b = roundingPolicy()(0)
        self.assertEqual(b, 0)

    def testOneInOne(self):
        b = roundingPolicy()(1)
        self.assertEqual(b, 1)

    def testBaseOne(self):
        # base one should always return the same number
        for i in range(20):
            b = roundingPolicy()(i)
            self.assertEqual(b, i)

    def giveBase(self, a, b):
        """ returns generator giving correct rounding policy
        """
        return roundingPolicy((a, b))

    def testBaseFive(self):
        # base of five should return 0 = 0, 1,2,3,4,5 = 5
        # 6,7,8,9,10=10
        self.assertEqual(self.giveBase(5, 0)(0), 0)
        self.assertEqual(self.giveBase(5, 0)(1), 5)
        self.assertEqual(self.giveBase(5, 0)(2), 5)
        self.assertEqual(self.giveBase(5, 0)(3), 5)
        self.assertEqual(self.giveBase(5, 0)(4), 5)
        self.assertEqual(self.giveBase(5, 0)(5), 5)
        self.assertEqual(self.giveBase(5, 0)(6), 10)
        self.assertEqual(self.giveBase(5, 0)(7), 10)
        self.assertEqual(self.giveBase(5, 0)(8), 10)
        self.assertEqual(self.giveBase(5, 0)(9), 10)
        self.assertEqual(self.giveBase(5, 0)(10), 10)

    def testBaseTwo(self):
        # base of five should return 0 = 0
        # 1, 2 = 2
        # 3, 4 = 4

        self.assertEqual(self.giveBase(2, 0)(0), 0)
        self.assertEqual(self.giveBase(2, 0)(1), 2)
        self.assertEqual(self.giveBase(2, 0)(2), 2)
        self.assertEqual(self.giveBase(2, 0)(3), 4)
        self.assertEqual(self.giveBase(2, 0)(4), 4)
        self.assertEqual(self.giveBase(2, 0)(5), 6)
        self.assertEqual(self.giveBase(2, 0)(6), 6)

    def testBase500(self):
        self.assertEqual(self.giveBase(5, 2)(0), 0)
        for i in range(1, 500):
            self.assertEqual(
                self.giveBase(5, 2)(i),
                500)
        self.assertEqual(self.giveBase(5, 2)(501),
                         1000)




if __name__ == '__main__':
    unittest.main()
