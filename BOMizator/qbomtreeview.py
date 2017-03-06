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
overloaded QTreeView to provide functionality of moving cursors
horizontally than vertically
"""

from PyQt4 import QtGui, QtCore


class QBOMTreeView(QtGui.QTreeView):
    """ implements movecursor to keep editting of rows as pleasant as
    it can be
    """

    def moveCursor(self, cursorAction, modifiers):
        if cursorAction == QtGui.QAbstractItemView.MoveNext:
            index = self.currentIndex()
            if index.isValid():
                if index.column()+1 < self.model().columnCount():
                    return index.sibling(index.row(), index.column()+1)
                elif index.row()+1 < self.model().rowCount(index.parent()):
                    return index.sibling(index.row()+1, 0)
                else:
                    return QtCore.QModelIndex()
        elif cursorAction == QtGui.QAbstractItemView.MovePrevious:
            index = self.currentIndex()
            if index.isValid():
                if index.column() >= 1:
                    return index.sibling(index.row(), index.column()-1)
                elif index.row() >= 1:
                    return index.sibling(index.row()-1,
                                         self.model().columnCount()-1)
                else:
                    return QtCore.QModelIndex()
        super(QBOMTreeView, self).moveCursor(cursorAction, modifiers)
