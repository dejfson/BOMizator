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
This application takes as the input the CSV bill-of-material file
generated by KiCad PCBNEW tool. It displays all the components in the
table. By clicking on read-only table items (value, manufacturer,
footprint) a default browser is launched, which searches for a
clicked keyword on the pages of farnell. This can be used to fast
search the farnell ordering codes. The application supports drag-drop
functionality, hence if user selects the farnell ordering code, it can
be dragged to the application to a specific column. This is a
hack-style tool, which allows the PCB designer to quickly search for
manufacturer part independently of the values of the libraries.
"""

import sys
import os
from PyQt4 import QtGui, uic
import csv
from sch_parser import sch_parser


localpath = os.path.dirname(os.path.realpath(__file__))
form_class = uic.loadUiType(os.path.join(localpath, "BOMLinker.ui"))[0]


class BOMLinker(QtGui.QMainWindow, form_class):
    def __init__(self, parent=None):
        """ Constructing small window
        """
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.BOM = []

        # load and parse all the components from the project
        self.SCH = sch_parser(sys.argv[1])
        self.SCH.parse_components()

        # standard headers for the treeview
        self.header = ["Designator",
                       "Reference",
                       "Manufacturer",
                       "Mfr. no",
                       "Datasheet"]
        self.model = QtGui.QStandardItemModel(self.treeView)
        self.model.setHorizontalHeaderLabels(self.header)

        # having headers we might deploy the data into the multicolumn
        # view. We need to collect all the data:
        for itemData in self.SCH.BOM():
            self.model.appendRow(map(
                QtGui.QStandardItem, list(itemData)))
        # and put the model into the place
        self.treeView.setModel(self.model)

        # as the model is filled with the data, we can resize columns
        for i in xrange(len(self.header)):
            self.treeView.resizeColumnToContents(i)

        self.showMaximized()

def main():
    """
    Main application body
    """

    app = QtGui.QApplication(sys.argv)
    myWindow = BOMLinker(None)
    myWindow.show()
    app.exec_()
