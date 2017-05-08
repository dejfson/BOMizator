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
import shutil
from BOMizator.qnewcomponentscachedialog import QNewComponentsCacheDialog
import logging

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
        self.newCache.clicked.connect(self.makeNewCache)
        self.logger = logging.getLogger('bomizator')

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

    def showConcernDialog(self):
        """ opens dialog with information and asks for a filename for
        the new cache
        """
        msg = QNewComponentsCacheDialog(self)
        retval = msg.exec_()
        if retval:
            # now we ask for a filename
            projdir, _ = QtWidgets.\
                         QFileDialog.\
                         getSaveFileName(self,
                                         "New Components cache",
                                         '',
                                         "Components cache (*.bmc)")
            if projdir and not os.path.splitext(projdir)[-1]:
                projdir += ".bmc"
            return (projdir,
                    msg.copyCurrentCache.checkState() == QtCore.Qt.Checked)
        # return empty stuff
        return ('', '')

    def makeNewCache(self):
        """ informs user about how to do, and then creates a new
        cache. If all OK, fills-in the dialog box with new cache
        """
        newcache, makeCopy = self.showConcernDialog()
        self.generateCache(newcache, makeCopy)

    def generateCache(self, fname, copyold):
        """ makes a new cache either by copying the current one, or by
        generating a new one (empty)
        """
        try:
            if copyold:
                shutil.copyfile(
                    self.settingsComponentCache.text(),
                    fname)
                self.logger.info("Copied current components class into a\
 newly generated new components class: %s" % (fname, ))
                self.settingsComponentCache.setText(fname)
                return

        except FileNotFoundError:
            self.logger.error("The original components cache filename\
 does not exist, hence cannot be copied. Generating empty cache instead.")

        # either failure as user selected some 'actual' cache which
        # does not exist, or we create new empty one
        with open(fname, "wt") as f:
            f.write("{}")
        self.logger.info("Generated new components\
 class in %s" % (fname, ))
        self.settingsComponentCache.setText(fname)

    def getCacheFile(self):
        """ opens file dialog box asking user to get the cache
        file. We're using savefilename as this one permits to create
        new file, whereas openfile only requests files existing (and
        the cache might not exist
        """
        name = "Select the components cache file"
        options = QtWidgets.QFileDialog.DontUseNativeDialog |\
                  QtWidgets.QFileDialog.DontConfirmOverwrite
        xfilt = "Generic component cache (*.bmc)"
        cacheFile, _ = QtWidgets.\
                       QFileDialog.getSaveFileName(self,
                                                   name,
                                                   '',
                                                   xfilt,
                                                   '',
                                                   options)
        if cacheFile:
            # append extension if not defined
            if cacheFile and not os.path.splitext(cacheFile)[-1]:
                cacheFile += ".bmc"
            self.settingsComponentCache.setText(cacheFile)
