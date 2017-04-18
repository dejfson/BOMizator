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
implements common access to web pages browsing
"""
import webbrowser


class browser_interface(object):

    def openBrowser(self, page):
        """ opens the browser with datasheet
        """
        # now fire the web browser with this page opened
        # this is list of browsers in the list of
        # 'preferences'. Konqueror has troubles to display octopart
        browsers = ['firefox', 'google-chrome', 'windows-default']
        while True:
            brw = browsers.pop(0)
            if not brw:
                raise webbrowser.Error("Cound not locate runnable browser")
            try:
                b = webbrowser.get(brw)
                b.open(page, new=0, autoraise=True)
                return
            except webbrowser.Error:
                pass
