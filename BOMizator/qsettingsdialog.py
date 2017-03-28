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

localpath = os.path.dirname(os.path.realpath(__file__))
loaded_dialog = uic.loadUiType(os.path.join(localpath,
                                         "settingsDialog.ui"))[0]


class cacheExceptionImplement(Exception):
    pass


class cacheIOAccess(object):
    """ defines base class for cache access. Does nothing except of
    implementation of basic methods
    """

    def init(self, fname):
        self.filename = fname

    def load(self):
        """ generic load function
        """
        raise cacheExceptionImplement("Not implemented")

    def save(self):
        """ generic save function
        """
        raise cacheExceptionImplement("Not implemented")


class cacheFileAccess(cacheIOAccess):
    pass


class cacheGitAccess(cacheIOAccess):
    pass


class QSettingsDialog(QtWidgets.QDialog, loaded_dialog):
    """ settings dialog box, takes care about selection of the cache
    """

    def __init__(self, settings, parent=None, flags=QtCore.Qt.WindowFlags()):
        super(QSettingsDialog, self).__init__(parent, flags)
        self.settings = settings
        self.setupUi(self)

        self.settingsChooseComponentCache.clicked.connect(self.getCacheFile)
        self.settingsCacheAccessType.addItem("File", cacheFileAccess)
        self.settingsCacheAccessType.addItem("Git", cacheGitAccess)

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
