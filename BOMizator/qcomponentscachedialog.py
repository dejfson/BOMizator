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
from PyQt5 import uic, QtWidgets, QtCore, QtGui
from .headers import headers


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

        self.model = QtGui.QStandardItemModel(self)

        # fill in the treewidget with appropriate data
        cc = cache.getCache()
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

                        row = list(map(QtGui.QStandardItem, txt+rest))
                        self.model.appendRow(row)

        # and let's setup headers names

        self.model.setHorizontalHeaderLabels([
            self.header.LIBREF,
            self.header.VALUE,
            self.header.FOOTPRINT] + self.header.USERITEMS)

        self.treeView.setModel(self.model)
