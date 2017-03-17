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
import textwrap
from .bomheaders import bomheaders
from .qdesignatorcomparator import QDesignatorComparator
from .colors import colors
from .roundingpolicy import roundingPolicy


class QBOMItemModel(QtGui.QStandardItemModel):
    """ provides model for BOM data
    """

    modelModified = QtCore.pyqtSignal(bool)

    def __init__(self, sourceData, hideComponents, parent=None):
        super(QBOMItemModel, self).__init__(parent)
        self.SCH = sourceData
        self.SCH.globalMultiplierModified.connect(self.updateGlobalMultiplier)
        # the point here: we generate a model,which has left-most set
        # of designators, followed by multiply, add
        self.header = bomheaders()
        self.fillModel(hideComponents)
        # following variable specifies, whether when total is setup by
        # hand, it should be treated as 'ultimate overrride' of the total
        self.ignoreTotalWrite = False
        self.ignoreCellChanges = False
        # hook when cell data changed by some model editing. This
        # should perform SCH write
        self.itemChanged.connect(self.cellDataChanged)

    def updateBOMData(self, indexes, supp, ocode, data):
        """ calls default schematic parser to update the data, in
        addition triggers for the the specific indexes recalculation
        of the total values if ocode means changing the rounding policy
        """
        self.SCH.updateBOMData(supp, ocode, data)
        # the way how we update is that we trigger cell data change on
        # e.g. multiply factor for each selected item. We read the
        # value and return the same one by setting its value. This
        # should trigger cellDataChanged for specific item
        mults = filter(lambda ix: ix.column() == self.header.getColumn(
            self.header.MULTIPLYFACTOR), indexes)
        for mul in mults:
            self.cellDataChanged(self.itemFromIndex(mul))

    def cellDataChanged(self, item):
        """ called when user changes the data in editable rows
        """
        if self.ignoreCellChanges:
            return
        # we need to find for this particular item the guy who has
        # reference number and the name. Supplier is always parent (if
        # user changes in supplier, nothing will be done
        supplier = item.parent().text()
        # new data are clear as well
        newdata = item.text()
        # here's trouble: the data in the same row have to be
        # accessed, but it cannot be done through the model, but
        # through the sibling of our item
        ordercode = item.index().sibling(item.row(), self.header.getColumn(
            self.header.SUPPNO)).data()
        desig = item.index().sibling(item.row(), self.header.getColumn(
            self.header.DESIGNATORS)).data()

        # gathered all the data, we have to write them down into sch:
        colname = self.header.getColumnName(item.column())
        # the biggest problem - how to get data from given column
        self.SCH.updateBOMData(supplier,
                               ordercode,
                               {colname: newdata})
        # if our change resolves in change of multiplier or adder, we
        # have to recalculate as well the total (as there are 2
        # options: any change in mul/add will result in total update,
        # any manual override of total erases the content of mul/add)
        if colname in [self.header.MULTIPLYFACTOR,
                       self.header.ADDFACTOR]:
            colors().printInfo("Readjusting total for %s" % (desig, ))
            # so here we are if manually entered values into
            # mult/add. In this case we recalculate total no matter if
            # prevously entered total manually. It might be, that one
            # of those is not properly defined, then we have to feed
            # them by default values
            idx = item.index().sibling(item.row(),
                                       self.header.getColumn(
                                           self.header.MULTIPLYFACTOR))
            try:
                mf = int(idx.data())
            except ValueError:
                # first we setup default value. This will trigger
                # calling this cell again
                self.itemFromIndex(idx).setText("1")
                return
            idx = item.index().sibling(item.row(),
                                       self.header.getColumn(
                                           self.header.ADDFACTOR))
            try:
                af = int(idx.data())
            except ValueError:
                # setup the other value. These two exceptions will be
                # only done when total was prevously entered manually
                self.itemFromIndex(idx).setText("0")
                return

            # recalculate new total according to those two
            # values. Only if mult/add are valid numbers (and if they
            # are not - because the total was entered manually - the
            # two exceptions above assure their correct
            # filling). Having those two numbers and designators we
            # can calculate automatically the totals
            ax = self.SCH.getBOMData(supplier, ordercode)
            print(ax)
            newtotal = self.calculateTotal(len(desig.split(",")),
                                           mf,
                                           af,
                                           policy=(ax[self.header.POLICY],
                                                   0))
            # IGNORE CELL CHANGES HERE OTHERWISE WE WOULD CREATE
            # INFINITE LOOP
            self.ignoreCellChanges = True
            self.SCH.updateBOMData(supplier,
                                   ordercode,
                                   {self.header.TOTAL: newtotal})
            ii = item.index().sibling(item.row(),
                                      self.header.getColumn(
                                          self.header.TOTAL))
            daa = self.itemFromIndex(ii)
            daa.setText(str(newtotal))
            self.ignoreCellChanges = False

        elif colname == self.header.TOTAL and not self.ignoreTotalWrite:
            colors().printInfo("Clearing out mul/add for %s" % (desig,
        ))
            for colname in [self.header.MULTIPLYFACTOR,
                            self.header.ADDFACTOR]:
                # following line clears out mul/add factors and in
                # addition it triggers change of the undelying model
                loidxname = self.header.getColumn(colname)
                loidx = item.index().sibling(item.row(), loidxname)
                daa = self.itemFromIndex(loidx)
                # this we have to do manually without re-calling the
                # cell again (otherwise we would over-write the
                # mult/add by a new number)
                self.ignoreCellChanges = True
                self.SCH.updateBOMData(supplier,
                                       ordercode,
                                       {self.header.MULTIPLYFACTOR: "",
                                        self.header.ADDFACTOR: ""})
                daa.setText("")
                self.ignoreCellChanges = False

        self.modelModified.emit(True)

    def makeDesignatorsText(self, desigs):
        """ from set of designators fabricates text of maximum 40
        characters split on boundary of words
        """
        x = textwrap.TextWrapper(width=40,
                                 break_on_hyphens=True)

        ls = sorted(list(desigs), key=QDesignatorComparator())
        txt = ', '.join(ls)
        return '\n'.join(x.wrap(txt))

    def calculateTotal(self, numdesigs, multiply, add, policy=(1, 0)):
        """ returns integer number corresponding to total amount of
        components. takes into account policy
        """
        a = numdesigs *\
            multiply *\
            self.SCH.getGlobalMultiplier() +\
            add
        return roundingPolicy(policy)(a)

    def getTotal(self, cdata):
        """ given component data this function returns amount of
        elements required to give proper amount of components to
        order. This is done by calculating amount of designators,
        multiplying by local multiplier, multiplying by global
        multiplier and adding the 'adder' part. THEN ROUNDING TO
        NEAREST x takes place depending of rounding policy
        """

        numDesigs = len(cdata[self.header.DESIGNATORS])
        # if multiply and add factors are empty, skip recalculation of
        # this one, as it was entered manually
        try:
            a = int(cdata[self.header.MULTIPLYFACTOR])
            b = int(cdata[self.header.ADDFACTOR])
        except ValueError:
            # this goes wrong then mult/add are empty
            return cdata[self.header.TOTAL]

        return self.calculateTotal(numDesigs,
                                   a,
                                   b,
                                   (cdata[self.header.POLICY], 0))

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
            rows = self.rowCount(index)
            for row in range(rows):
                # get the number
                suppno = index.child(row, self.header.getColumn(
                    self.header.SUPPNO)).data()
                desigs = index.child(row, self.header.getColumn(
                    self.header.DESIGNATORS)).data()
                # having all the data for particular component we
                # can recalculate the total
                bomdata = self.SCH.getBOMData(index.data(), suppno)
                cdata = bomdata.copy()
                cdata[self.header.DESIGNATORS] = desigs.split(",")
                # these fake data can calculate new totals
                newtot = self.getTotal(cdata)
                # problem with setting data here is, that we do not
                # want to clearout the local mult/add because we're
                # not entering the data manually, but we just want to
                # update globally using _mult/add_, so we temporarily
                # disable cell data storage
                self.ignoreTotalWrite = True
                # and now we have to set the data into total
                # calling set data invoke celldatachanged, hence
                # there's a place where the value gets propagated
                # into the data structure
                self.setData(
                    index.child(row, self.header.getColumn(
                        self.header.TOTAL)),
                    str(newtot))
                self.ignoreTotalWrite = False
                self.modelModified.emit(True)

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
            # this one is special, we have to pull out the entire row
            supprow = [QtGui.QStandardItem(supplier), ]
            for i in range(len(self.header)):
                supprow += [QtGui.QStandardItem(), ]
            # modify parameters:
            for coitem in supprow:
                # identify this row as supplier row (hence no data of
                # mult/add and is read-only)
                coitem.setData(True, self.header.ItemIsSupplier)
                coitem.setForeground(QtGui.QColor('white'))
                coitem.setBackground(QtGui.QColor('black'))

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
                        if cdata[self.header.TOTAL] == -1:
                            # initial state is -1, we recalculate
                            # (until first save)
                            colors().printInfo("Automatically\
 calculating first total for %s" % (self.makeDesignatorsText(
     cdata[self.header.DESIGNATORS])))
                            newtotal = self.getTotal(cdata)
                            data = "%s" % str(newtotal)
                            # and we need to store this value in the
                            # sch.
                            self.SCH.updateBOMData(supplier,
                                                   ordercode,
                                                   {self.header.TOTAL:
                                                    newtotal})
                            self.modelModified.emit(True)
                        else:
                            data = "%s" % (str(cdata[self.header.TOTAL]))
                    elif column == "RoundingPolicy":
                        # this one is ignored as it only concerns
                        # calculation of total and it is not displayed
                        continue
                    elif column in [self.header.ADDFACTOR,
                                    self.header.MULTIPLYFACTOR]:
                        # these are integers, convert to numeric
                        data = cdata[column]
                    elif column == self.header.SUPPNO:
                        # this is different item:
                        data = ordercode
                    else:
                        # all other elements are simple texts
                        data = cdata[column]
                    row.append(data)

                rowdata = list(map(QtGui.QStandardItem, row))
                # first item from the row is the parent
                supprow[0].appendRow(rowdata)

        sorted_header = self.header.getHeaders()
        self.setHorizontalHeaderLabels(sorted_header)

    def flags(self, index):
        """ according to which column we have cursor on, this field

        returns flags for it. Some are editable, droppable, some are
        read only
        """

        # keep default flags
        defaultFlags = QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEnabled

        # now we have to find, whether the index concerns the row with
        # manufacturer. if so, then it is not editable, in all other
        # cases we return default flags per 'normal' item
        if not self.itemFromIndex(
                index.sibling(0, 0)).data(
                    self.header.ItemIsSupplier):
            defaultFlags |= self.header.getFlags(index.column())
        return defaultFlags
