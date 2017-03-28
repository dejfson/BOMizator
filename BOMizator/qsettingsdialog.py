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
Implements settings dialog box
"""

from PyQt5 import QtWidgets, uic, QtCore
import os
import imp
import fnmatch

localpath = os.path.dirname(os.path.realpath(__file__))
loaded_dialog = uic.loadUiType(os.path.join(localpath,
                                            "settingsDialog.ui"))[0]


class QSettingsDialog(QtWidgets.QDialog, loaded_dialog):
    """ settings dialog box, takes care about selection of the cache
    """

    def __init__(self, settings, parent=None, flags=QtCore.Qt.WindowFlags()):
        super(QSettingsDialog, self).__init__(parent, flags)
        self.settings = settings
        self.setupUi(self)

        self.settingsChooseComponentCache.clicked.connect(self.getCacheFile)

        # preload the stuff from the settings file
        componentsCacheFile = self.settings.value(
            "componentsCacheFile",
            '',
            str)
        self.settingsComponentCache.setText(componentsCacheFile)

        matches = []
        for root, dirnames, filenames in os.walk(localpath):
            for filename in fnmatch.filter(filenames, 'cache*access.py'):
                matches.append(os.path.join(root, filename))
        print("Following accesses found ", matches)

        inserted = []
        # fill in combo box, taking possible sources. use their
        # filenames as identifiers
        for plugin in matches:
            info = imp.load_source('', plugin).DEFAULT_CLASS
            if info:
                data = os.path.split(plugin)[-1]
                inserted.append(data)
                self.settingsCacheAccessType.addItem(
                    info().name(),
                    data)

        # load all of them and their default names. If do not exist,
        # do not take them into consideration
        # load the access type. !CASE SENSITIVE!
        componentsAccessType = self.settings.value(
            "componentsAccessType",
            "cachefileaccess.py",
            str)
        # find which index it is
        ci = list(filter(lambda plg:
                         plg[1].find(componentsAccessType) != -1,
                         enumerate(inserted)))
        self.settingsCacheAccessType.setCurrentIndex(ci[0][0])

    def getCacheFile(self):
        """ opens file dialog box asking user to get the cache file.
        """
        cacheFile, _ = QtWidgets.QFileDialog.getOpenFileName(self,
                                                             "Select\
 the components cache file",
                                                             '',
                                                             "Generic\
 component cache (*.bmc)")
        if cacheFile:
            self.settingsComponentCache.setText(cacheFile)
