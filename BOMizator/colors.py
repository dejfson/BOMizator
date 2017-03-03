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
Some generic constants to define colorset
"""

# define ansi terminal colorset


class colors(object):
    """defines ANSI colors for pretty print
    """
    COLOROK = "\033[92m"
    COLORWARN = "\033[93m"
    COLORFAIL = "\033[91m"
    COLORNUL = "\033[0m"
    COLORINFO = '\033[94m'

    def printColor(self, color, string):
        """ prints the text on the console using ANSI colors
        """
        print(color +
              string +
              self.COLORNUL)

    def printFail(self, string):
        """ prints test in using failure color
        """
        self.printColor(self.COLORFAIL,
                        string)

    def printWarn(self, string):
        self.printColor(self.COLORWARN,
                        string)

    def printInfo(self, string):
        self.printColor(self.COLORINFO,
                        string)

    def printOK(self, string):
        self.printColor(self.COLOROK,
                        string)
