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
Implements item model for the treeView
"""

from PyQt4 import QtGui, QtCore
from .supplier_selector import supplier_selector
from .headers import headers


class QDropStandardItemModel(QtGui.QStandardItemModel):
    """ redefines standard item model to support drop actions
    """
    def __init__(self, parent=None):
        super(QDropStandardItemModel, self).__init__(parent)
        # get all sellers filters
        self.suppliers = supplier_selector()
        # for convenience to query the selection
        self.header = headers()

    def setSelectionFilter(self, filt):
        """ Runs through all the rows in the data, checks if
        appropriate columns have the same data as those specified in
        filters, and if so, the all filter cells are 'selected'. This
        works over the default sorting, hence all rows are always
        searched. filt is a dictionary containing key = column, value
        = data which have to be present in a given column. Function
        returns list of modelindexes which should be selected as they
        match the filter
        """
        # list of modelindexes to be set selected in treeview
        to_select = []
        for row in range(self.rowCount()):
            # get indices of all columns
            items = []
            for col, value in filt.items():
                idx = self.index(row, int(col))
                item = self.itemFromIndex(idx)
                if item.text() == value:
                    # this condition fits, we can add it into items:
                    items.append(idx)
            # here if all conditions are satisfied, then items length
            # should be the same as dict length:
            if len(items) == len(filt):
                # we have those items, we can set them selected
                to_select += items
        return to_select

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
        try:
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
        except KeyError:
            pass
        QtGui.QApplication.restoreOverrideCursor()
        return True

    def mimeTypes(self):
        """ This class accepts only text/plain drops, hence this
        function sets up the correct mimetype
        """
        return ['text/plain', ]

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
