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
Implements model for BOM treeView, which displays the data grouped by
supplier and components grouped by reference number rather than
designators. This is the view, which allows to easily come out with
bill of material usable to directly order the components
"""

from PyQt4 import QtGui, QtCore
import pickle
import textwrap
from itertools import count
from .bomheaders import bomheaders
from .qdesignatorcomparator import QDesignatorComparator

class QBOMItemModel(QtGui.QStandardItemModel):
    """ provides model for BOM data
    """
    def __init__(self, sourceData, hideComponents, parent=None):
        super(QBOMItemModel, self).__init__(parent)
        self.SCH = sourceData
        self.SCH.globalMultiplierModified.connect(self.updateGlobalMultiplier)
        # the point here: we generate a model,which has left-most set
        # of designators, followed by multiply, add
        self.header = bomheaders()
        self.fillModel(hideComponents)

    def makeDesignatorsText(self, desigs):
        """ from set of designators fabricates text of maximum 40
        characters split on boundary of words
        """
        x = textwrap.TextWrapper(width=40,
                                 break_on_hyphens=True)

        ls = sorted(list(desigs), key=QDesignatorComparator())
        txt = ', '.join(ls)
        return '\n'.join(x.wrap(txt))

    def getTotal(self, cdata):
        """ given component data this function returns amount of
        elements required to give proper amount of components to
        order. This is done by calculating amount of designators,
        multiplying by local multiplier, multiplying by global
        multiplier and adding the 'adder' part. THEN ROUNDING TO
        NEAREST x takes place depending of rounding policy
        """
        numDesigs = len(cdata[self.header.DESIGNATORS])
        totalSimple = numDesigs *\
                      int(cdata[self.header.MULTIPLYFACTOR]) *\
                      self.SCH.getGlobalMultiplier() +\
                      int(cdata[self.header.ADDFACTOR])
        # total simple is now passed through the rounding effect. This
        # depends on components 'RoundingPolicy'.
        # generally roundingpolicy = 0 -> direct number, for each 1+
        # we do like with money:
        # @TODO implement rounding policy
        rp = [0, 2, 5, 10, 20, 50, 100]
        return totalSimple

    def updateGlobalMultiplier(self):
        """
        called whenever underlying SCH changes the multiplier. this
        happens when GUI requires to change the multiplier. We
        re-insert new data into total sums as this is the value which changes
        """
        cdata = {}
        # this is top-level with supplier
        for supplier in range(self.rowCount()):
            # and sub parsing
            index = self.index(supplier, 0)
            try:
                for row in range(40):
                    for item in [self.header.DESIGNATORS,
                                 self.header.MULTIPLYFACTOR,
                                 self.header.ADDFACTOR]:
                        idx = index.child(row, self.header.getColumn(item))
                        if not idx.isValid():
                            raise ValueError
                        cdata[item] = idx.data()
                    # need to convert-back the designators to
                    # 'standard' form to be able to determine how many
                    # we have
                    desigs = cdata[self.header.DESIGNATORS]
                    cdata[self.header.DESIGNATORS] = desigs.split(",")
                    # these fake data can calculate new totals
                    newtot = self.getTotal(cdata)
                    # and now we have to set the data into total
                    self.setData(
                        index.child(row, self.header.getColumn(
                            self.header.TOTAL)),
                        str(newtot))
            except ValueError:
                pass

        print(cdata)
        print("updating global multiplier view")

    def fillModel(self, hideComponents):
        """ based on input data the model is filled with the
        data. *DISABLED ITEMS ARE IGNORED* during production if
        hideComponents is set to true.
        """

        # now we need to crunch the data. First we get composed a
        # dictionary consisting of two data sets: the schematic loaded
        # from the schematic data, and _our one loaded from bmz
        # file. The one we're interested in is the dictionary with
        # values of multiplications and general items settings, which
        # cannot be stored as a part of sch, as they are not related
        # to this anyhow.
        allComps = self.SCH.getCollectedComponents()
        # this we use just in case we need to investigate on the data
        # with open('/tmp/components.pickle', 'wb') as handle:
        #     pickle.dump(allComps, handle,
        # protocol=pickle.HIGHEST_PROTOCOL)
        self.clear()
        sorted_header = list(self.header.getHeaders())

        for supplier in allComps:
            supprow = QtGui.QStandardItem(supplier)
            self.appendRow(supprow)
            for ordercode in allComps[supplier]:
                row = []
                cdata = allComps[supplier][ordercode]
                for column in sorted_header:
                    # designator column is a concatenated list of
                    # designators
                    if column == self.header.DESIGNATORS:
                        data = self.makeDesignatorsText(cdata[column])
                    elif column == self.header.TOTAL:
                        # total is a value recalculated on the fly
                        # from number of designators, multipliers and
                        # total multiplicator
                        data = "%d" % (self.getTotal(cdata))
                    elif column == "RoundingPolicy":
                        # this one is ignored as it only concerns
                        # calculation of total
                        continue
                    elif column in [self.header.ADDFACTOR,
                                    self.header.MULTIPLYFACTOR]:
                        # these are integers, convert to numeric
                        data = "%d" % (cdata[column])
                    elif column == self.header.SUPPNO:
                        # this is different item:
                        data = ordercode
                    else:
                        # all other elements are simple texts
                        data = cdata[column]
                    row.append(data)

                rowdata = list(map(QtGui.QStandardItem, row))

                supprow.appendRow(rowdata)

        sorted_header = self.header.getHeaders()
        self.setHorizontalHeaderLabels(sorted_header)

    def flags(self, index):
        """ according to which column we have cursor on, this field

        returns flags for it. Some are editable, droppable, some are
        read only
        """

        # keep default flags
        defaultFlags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled
        defaultFlags |= self.header.getFlags(index.column())
        return defaultFlags
