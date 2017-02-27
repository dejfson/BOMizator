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

from PyQt4 import QtCore


class farnell(object):
    """ defines web search interface for uk.farnell.com.
    """

    def __init__(self):
        self.name = "FARNELL"

    def get_url(self, searchtext):
        """ returns URL of farnell, which triggers searching for a
        specific component or name.
        """
        return "http://uk.farnell.com/webapp/\
wcs/stores/servlet/Search?st=%s" % (searchtext,)

    def parse_URL(self, urltext):
        """ From GIVEN URL (web pages) parses all the data to resolve
        the component. Farnell is relatively easy to do. Here is the
        typical URL, self-explanatory. NOTE THAT ALL OBJECTS ARE
        RETURNED AS QSTRINGS AND NOT ORDINARY PYTHON STRINGS
        (convenience). Fortunately FARNELL is very consistent about it
        (thank you guys), hence it can be used to parse all what we need
        http://uk.farnell.com/multicomp/mj-179ph/socket-low-voltage-12vdc-4a/dp/1737246?ost=MJ-179PH&searchView=table&iscrfnonsku=false
        """

        try:
            realpart = urltext.split("?")[0]
            # from the real part we need to abstract the parameters:
            header,\
                nothing,\
                site,\
                manufacturer,\
                reference,\
                description,\
                deep,\
                partnum = realpart.split("/")
            # series of checks: site has to contain farnell:
            if not site.contains("FARNELL", QtCore.Qt.CaseInsensitive):
                raise KeyError

            # deep has to contain DP:
            if not deep.contains("DP", QtCore.Qt.CaseInsensitive):
                raise KeyError
            # the most problematic is to dig out the datasheet for the
            # component. This is not part of the URL and for this we need
            # to actually fetch and parse the page. For the moment
            # 'nothing'
            datasheet = QtCore.QString('')
            # return properly formed tuple:(Manufacturer, Mfg. reference,
            # Supplier, Supplier reference, datasheet)
            data = (manufacturer, reference,
                    QtCore.QString("FARNELL"), partnum, datasheet)
            return map(QtCore.QString.toUpper, data)
        except ValueError:
            # ValueError is risen when not enouth data to split the
            # header. In this case this is probably not an URL we're
            # looking for, so skipping
            raise KeyError

DEFAULT_CLASS = farnell
