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
from PyQt4 import QtGui, uic, QtCore
from sch_parser import sch_parser
from supplier_selector import supplier_selector
import webbrowser
from headers import headers

localpath = os.path.dirname(os.path.realpath(__file__))
form_class = uic.loadUiType(os.path.join(localpath, "BOMLinker.ui"))[0]


class QDropStandardItemModel(QtGui.QStandardItemModel):
    """ redefines standard item model to support drop actions
    """
    def __init__(self, parent):
        super(QDropStandardItemModel, self).__init__(parent)
        # get all sellers filters
        self.suppliers = supplier_selector()
        # for convenience to query the selection
        self.header = headers()

    def getSelectedRows(self):
        """ returns tuple of rows, which are selected. This is done by
        looking through the rows and columns and detecting
        selections. Unfortunately the author (me) did not find any
        more intelligent method how to do it
        """
        a = []
        for index in self.parent().selectedIndexes():
            a.append(index.row())
        a = set(a)
        return a

    def dropMimeData(self, data, action, row, column, treeparent):
        """ takes care of data modifications. The data _must contain_
        URL from the web pages of one of the pages supported by
        plugins. This is verified against the suppliers object, which
        returns correctly parsed data.
        """
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        # note: the row and column needs a bit of explication. It
        # always returns -1 in both. And that's because we're using
        # QTreeView, and row/column shows _where in parent we need to
        # insert the data_. But in fact, we want to _replace the
        # parent_ by our data. Respectively we need to replace data in
        # appropriate row and _many_ columns, depending on whether a
        # single item is selected, or multiple items (in terms of
        # designators) are selected. Following command returns
        # dictionary of all found items
        parsed_data = self.suppliers.parse_URL(data.text())
        # first we find all items, which are selected. we are only
        # interested in rows, as those are determining what
        # designators are used.
        rows = self.getSelectedRows()
        # and with all selected rows we distinguish, whether we have
        # dropped the data into selected rows. If so, we will
        # overwritte all the information in _each row_. If however the
        # drop destination is outside of the selection, we only
        # replace given row
        if treeparent.row() in rows:
            replace_in_rows = rows
        else:
            replace_in_rows = [treeparent.row(), ]

        # now the data replacement. EACH ITEM HAS ITS OWN MODELINDEX
        # and we get the modelindices from parent. Do for each of them
        for row in replace_in_rows:
            # walk through each parsed item, and change the data
            for key, value in parsed_data.items():
                self.setData(
                    self.index(row,
                               self.header.get_column(key)),
                    value)
        QtGui.QApplication.restoreOverrideCursor()
        return True

    def mimeTypes(self):
        """ This class accepts only text/plain drops, hence this
        function sets up the correct mimetype
        """
        types = QtCore.QStringList()
        types.append('text/plain')
        return types

    def flags(self, index):
        """ according to which column we have cursor on, this field

        returns flags for it. Some are editable, droppable, some are
        read only
        """

        # keep default flags
        defaultFlags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

        # if manufacturer, mfgno, datasheet, these are editable as
        # well
        try:
            defaultFlags |= self.header.get_flags(index.column())
        except KeyError:
            # index.column() can be -1 depending on what we're
            # pointing on. In this case we leave default flags as they are
            pass

        return defaultFlags


class BOMizator(QtGui.QMainWindow, form_class):
    def __init__(self, parent=None):
        """ Constructing small window
        """
        QtGui.QMainWindow.__init__(self, parent)
        self.setupUi(self)

        self.BOM = []

        # load and parse all the components from the project
        self.SCH = sch_parser(sys.argv[1])
        self.SCH.parse_components()

        self.model = QDropStandardItemModel(self.treeView)
        # get header object
        self.header = headers()

        sorted_header = self.header.get_headers()
        self.model.setHorizontalHeaderLabels(sorted_header)

        # having headers we might deploy the data into the multicolumn
        # view. We need to collect all the data:
        for itemData in self.SCH.BOM():
            line = map(QtGui.QStandardItem, list(itemData))
            # some modifications to items
            # 1) designator, library part and footprint are immutable
            for i in self.header.get_columns([self.header.DESIGNATOR,
                                              self.header.LIBREF,
                                              self.header.VALUE,
                                              self.header.FOOTPRINT]):
                line[i].setEditable(False)

            self.model.appendRow(line)
        # and put the model into the place
        self.treeView.setModel(self.model)

        # as the model is filled with the data, we can resize columns
        for i in xrange(len(self.header)):
            self.treeView.resizeColumnToContents(i)

        # @TODO re-enable maximized
        self.showMaximized()
        # connect signals to treeView so we can invoke search engines
        self.treeView.doubleClicked.connect(self.tree_doubleclick)
        # register accepting drops
        self.treeView.setAcceptDrops(True)
        self.treeView.setDropIndicatorShown(True)
        # and register custom context menu, which will be used as
        # 'filtering' to select correcly chosen indices
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.openMenu)

    def openMenu(self, position):
        """ opens context menu. Context menu is basically a
        right-click on any cell requested. The column and row is
        parsed, and depending of which column was used to select the
        context menu contains appropriate filter offers. In case of
        clicking over datasheet it opens the datasheet in the
        browser. In case of libref it can choose the same components
        etc...
        """
        indexes = self.treeView.selectedIndexes()

        if len(indexes) < 1:
            return

        # some more validation: if datasheet clicked, we display 'open
        # datasheet' menu. But only single one is allowed at time
        if len(indexes) == 1 and\
           indexes[0].column() ==\
           self.header.get_column(self.header.DATASHEET):
            # datasheet is 'easy'. We parse the datasheets (they might
            # be multiple, semicolon separated) and construct the menu
            # out of them
            datasheets = indexes[0].text().split(";")
            menu = QtGui.QMenu()

            for i in datasheets:
                menu.addAction(self.tr("Open %s" % (i,)))

            menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def open_datasheet(self):
        """ opens the browser with datasheet
        """
        pass

    def open_search_browser(self, searchtext):
        """ This function calls default plugin to supply the web
        search string for a given text. This one is then used to open
        a browser window with searched item. Now, searching does not
        mean at all that the component will be found straight away. It
        just means that a page with search resuls will open, and user
        it responsible to look for a specific component further.
        """
        url = self.model.suppliers.search_for_component(searchtext)
        # now fire the web browser with this page opened
        b = webbrowser.get('firefox')
        b.open(url, new=0, autoraise=True)

    def tree_doubleclick(self, index):
        """ when user doubleclicks item, we search for it in farnel
        (or later whatever else) web pages. this requires a lot of
        fiddling as the component search enginer for each seller are
        different. Index is the type QModelIndex
        """
        # we process only columns libref and value as those are used
        # to search (most of the time)
        if index.column() in self.header.get_columns([self.header.LIBREF,
                                                      self.header.VALUE]):

            item = self.model.item(index.row(), index.column())
            strData = item.data(0).toPyObject()
            # this is what we're going to look after
            self.open_search_browser(str(strData))
        # if column is datasheet and there is actually something, open
        # the link in the browser.
        # @TODO doubleclick opens datasheet if available (or context menu)
        # elif index.column() == HEADER['Datasheet']:
        #     strData = item.data(0).toPyObject()
        #     if strData != '':
        #         b = webbrowser.get('firefox')
        #         b.open(strData, new=0, autoraise=True)


def main():
    """
    Main application body
    """

    app = QtGui.QApplication(sys.argv)
    myWindow = BOMizator(None)
    myWindow.show()
    app.exec_()