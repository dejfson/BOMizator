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
Farnell webpages search engine
"""


class radiospares(object):
    """ defines web search interface for uk.farnell.com.
    """

    def __init__(self):
        self.name = "RADIOSPARES"

    def parseURL(self, urltext):
        """ parses URL and extract the data from radiospares item
        """

        # for the moment not implemented
        # @TODO implement radiospares parseURL
        raise KeyError

    def getShortcut(self):
        """ returns shortcut
        """
        return "R"

    def getUrl(self, searchtext):
        """ returns URL of farnell, which triggers searching for a
        specific component or name.
        """
        return "http://fr.rs-online.com/web/zr/?searchTerm=%s" % (searchtext)

DEFAULT_CLASS = radiospares
