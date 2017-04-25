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
implements functionality of components cache dialog
"""
import os
from functools import partial
from PyQt5 import uic, QtWidgets, QtCore, QtGui
from BOMizator.headers import headers
from BOMizator.qbomcomponentscache import QBOMComponentCache
from BOMizator.cachefileaccess import cacheFileAccess
from BOMizator.browser_interface import browser_interface
from BOMizator.qnewcomponentscachedialog import QNewComponentsCacheDialog


localpath = os.path.dirname(os.path.realpath(__file__))
loaded_dialog = uic.loadUiType(os.path.join(localpath,
                                            "componentsCacheDialog.ui"))[0]

class QComponentsCacheDialog(QtWidgets.QDialog, loaded_dialog):
    """ settings dialog box, takes care about selection of the cache
    """

    def __init__(self, cache, parent=None, flags=QtCore.Qt.WindowFlags()):
        super(QComponentsCacheDialog, self).__init__(parent, flags)
        self.setupUi(self)
        self.showMaximized()
        self.cCache = cache
        self.header = headers()
        self.isModified = False
        self.model = QtGui.QStandardItemModel(self)

        # fill in the treewidget with appropriate data
        self.fillModel(cache.getCache())
        self.importButton.clicked.connect(self.importAnother)
        self.deleteButton.clicked.connect(self.deleteItems)
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.openContextMenu)
        self.newButton.clicked.connect(self.newCache)
        # we keep through the list of detected components
        # so cache can know what to delete
        self.deletedComponents = []

    def showConcernDialog(self):
        msg = QNewComponentsCacheDialog(self)
        retval = msg.exec_()
        if retval == QtWidgets.QMessageBox.Ok:
            print("value of pressed message box button:", retval)

    def newCache(self):
        """ informs user about how to do, and then creates a new
        cache. If all OK, fills-in the dialog box with new cache
        """
        self.showConcernDialog()

    def getSelectedRows(self):
        """ returns list of selected rows
        """
        rows = []
        for row in self.treeView.selectedIndexes():
            rows.append(row.row())
        unique = set(rows)
        return list(unique)

    def openContextMenu(self, position):
        """ opens context menu when right clicked
        """
        rows = self.getSelectedRows()
        if len(rows) == 1:
            # exactly one item selected, we can display datasheet if
            # required
            i = self.model.index(rows[0], 0)
            libref, value, footprint, key = self.model.data(i,
                                                            QtCore.Qt.UserRole)
            comp = list(self.components[libref][value][footprint].values())[0]
            print(comp)

            if comp[self.header.DATASHEET]:
                menu = QtWidgets.QMenu(self)
                datasheet = comp[self.header.DATASHEET]
                open_action = menu.addAction(
                    self.tr("Open %s" % (datasheet, )))
                open_action.triggered.connect(partial(self.openBrowser,
                                                      datasheet))
                menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def openBrowser(self, url):
        """ opens browser interface
        """
        browser_interface().openBrowser(url)

    def deleteItems(self):
        """ deletes selected items from the copy of the components
        cache.
        """
        sels = self.treeView.selectedIndexes()
        for i in filter(lambda ix: ix.column() == 0, sels):
            libref, value, footprint, key = self.model.data(i,
                                                            QtCore.Qt.UserRole)
            self.deletedComponents.append([libref,
                                           value,
                                           footprint,
                                           key])
            # deleting key including non-empty items:
            self.components[libref][value][footprint].pop(key)
            # now pop all empty branches of this
            if not self.components[libref][value][footprint]:
                self.components[libref][value].pop(footprint)
            if not self.components[libref][value]:
                self.components[libref].pop(value)
            if not self.components[libref]:
                self.components.pop(libref)
            self.isModified = True

        if self.isModified:
            self.fillModel(self.components)

    def fillModel(self, cc):
        """ given cache dictionary cc this function fills in the treeView
        """
        self.model.clear()
        hx = [self.header.LIBREF,
              self.header.VALUE,
              self.header.FOOTPRINT] + self.header.USERITEMS
        self.model.setHorizontalHeaderLabels(hx)
        # now we run through the cache and generate all the indices:
        for libref in cc.keys():
            for value in cc[libref].keys():
                for footprint in cc[libref][value].keys():
                    for key, imt in cc[libref][value][footprint].items():
                        # for each key we make column number and add
                        # it as row
                        txt = [libref, value, footprint, ]
                        # follow up unique items:
                        rest = list(map(lambda it:
                                        imt[it],
                                        self.header.USERITEMS))
                        # for each item we add the dictionary keys
                        # such, that it permits easy deletion
                        row = list(map(QtGui.QStandardItem, txt+rest))
                        for it in row:
                            it.setData([libref,
                                        value,
                                        footprint,
                                        key],
                                       QtCore.Qt.UserRole)
                        self.model.appendRow(row)
        # WE HAVE TO WORK OVER DICTIONARY COPY TO AVOID MODIFICATION
        # OF ORIGINAL DICTIONARY - JUST IN CASE SOMEONE PRESSES CANCEL
        # BUTTON ON THIS DIALOG BOX
        self.components = cc.copy()
        self.treeView.setModel(self.model)
        self.treeView.setSortingEnabled(True)
        self.treeView.sortByColumn(2, QtCore.Qt.AscendingOrder)
        for i in range(len(hx)):
            self.treeView.resizeColumnToContents(i)

    def makeKey(self, cm, nk):
        """ makes in cm dictionary a new key identified by tuple
        (libref, value, footprint). If that key already exists,
        nothing happens. In any case this function assures, that
        dict-of-dict-of... key exists into depth given by length of nk
        """
        cdir = cm
        for subitem in nk:
            if subitem not in cdir.keys():
                cdir[subitem] = {}
            cdir = cdir[subitem]

    def importAnother(self):
        """ asks for filename of other cache and merges the caches together
        """
        name = "Open BOMizator components cache"
        fil = "BOMizator components cache (*.bmc)"
        cc, _ = QtWidgets.QFileDialog.\
            getOpenFileName(self,
                            name,
                            '',
                            fil)
        if not cc:
            return

        # load the new cache,
        nc = QBOMComponentCache(cacheFileAccess(cc))
        nd = nc.getCache()
        # now let's browse through the new dictionary and add the keys
        # providing that they are unique. No component must be
        # inserted twice under the same
        for libref in nd.keys():
            for value in nd[libref].keys():
                for footprint in nd[libref][value].keys():
                    for ckey, cval in nd[libref][value][footprint].items():
                        # each component is identified as this:
                        self.makeKey(self.components, [libref,
                                                       value,
                                                       footprint])

                        if ckey not in self.components[libref]\
                           [value][footprint].keys():
                            # we append that key
                            self.components[libref]\
                                [value][footprint][ckey] = cval
                            self.isModified = True
        # having all the values merged we need to re-fill again the
        # entire data
        self.fillModel(self.components)
