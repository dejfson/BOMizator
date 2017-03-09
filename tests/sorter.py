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
from BOMizator.qdesignatorcomparator import QDesignatorComparator
from BOMizator.qdesignatorcomparator import InvalidDesignator


class TestStringMethods(unittest.TestCase):

    def testOrdinarySorting(self):
        a = ['Z9', 'A1', 'Q10', 'Q11', 'Q1', 'Q2']
        b = sorted(a, key=QDesignatorComparator())
        c = ','.join(b)
        self.assertEqual(c, 'A1,Q1,Q2,Q10,Q11,Z9')

    def testDesignatorNumberTooLarge(self):
        a = ['Z10000', ]
        with self.assertRaises(InvalidDesignator):
            sorted(a, key=QDesignatorComparator())

if __name__ == '__main__':
    unittest.main()
