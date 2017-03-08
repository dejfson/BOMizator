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
Implements custom sorting to take into account designators
"""

from PyQt4 import QtGui, QtCore
from collections import defaultdict
from .headers import headers
from .supplier_selector import supplier_selector
from .colors import colors
import re
import sys
import hashlib
import json


class QDesignatorSortModel(QtGui.QSortFilterProxyModel):
    """ Reimplements sorting of the treeview such, that designator and
    values numbers are properly sorted according to 'normal'
    perception. Hence U1, U2, U3 and not U1, U10, U11 as by default.
    """

    # signal informing that a component was added into the cache. To
    # be cached in app to store the cache appropriately
    addedComponentIntoCache = QtCore.pyqtSignal()
    # this signal is emitted when user drops data into the
    # rows. Dictionary of affected components is passed through this
    # signal to the application so the data can be appropriately handled
    componentsDataChanged = QtCore.pyqtSignal(list, dict)

    def __init__(self, parent=None, componentsCache={}):
        """ creates headers object used for comparison. The parent
        identifies the treeView. componentsCache is a dictionary (it
        is defaultdict of defaultdicts), which identifies each dropped
        component out of libref/value/footprint such, that it can be
        reusable. Point of all this is, that when user drops in place
        a component from a supplier, he might use this component for
        any other _same_ component in the future. Hence if dropped,
        the component cache is storing libref/value/footprint wrt
        (mfg, mfgno, supplier, supplierno, datasheet) such, that next
        time user requests the context menu, this component is offered
        from cache if exists. When the component cache is taken care
        of by user (git repo e.g.), then during the time a component
        library is made. It is however up to user to keep the
        components database correct as no further formal verification
        can be done. This is a desirable feature of a hardware
        engineer :) (at least me as the author)
        """
        super(QDesignatorSortModel, self).__init__(parent)
        self.header = headers()
        # get all sellers filters
        self.suppliers = supplier_selector()
        self.componentsCache = componentsCache

    def clearAssignments(self):
        """ all selected rows data get cleared. This will only remove
        the information from the list, but the component cache stays
        intact (hence once component entered into the component cache,
        it will not be removed unless cache is updated externally)
        """
        rows = self.getSelectedRows()
        # get the data out of those indices
        colidx = list(self.header.getColumns(self.header.USERITEMS))
        for row in rows:
            for col in colidx:
                self.setData(self.index(row, col), "")

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
        toSelect = []
        for row in range(self.rowCount()):
            # get indices of all columns
            items = []
            for col, value in filt.items():
                idx = self.index(row, int(col))
                idxval = self.itemData(idx)[QtCore.Qt.DisplayRole]
                if idxval == value:
                    # this condition fits, we can add it into items:
                    items.append(idx)
            # here if all conditions are satisfied, then items length
            # should be the same as dict length:
            if len(items) == len(filt):
                # we have those items, we can set them selected
                toSelect += items
        return toSelect

    def getText(self, left, isProxied=False):
        """ returns text from the modelindex data. If isProxied is
        true, the left modelindex is corresponding proxy
        modelindex. if isProxied is false, then left modelindex is the
        modelindex of QStandardItemModel (instead of proxy)
        """
        if isProxied:
            idsrc = self.mapToSource(left)
        else:
            idsrc = left
        return idsrc.model().itemFromIndex(idsrc).text()

    def getDesignatorNumber(self, designator):
        """ parses given designator and returns tuple (alphas, digit),
        which are then used for comparison. Allowed combinations:
        <multiletter_designator><number><extension>, where
        multiletter_designator is only alphas, number is 0-9 and
        extension can be whatever. Hence following is still allowed:
        Q12_a, but following is not allowed: Q_a12
        """
        if designator.find("?") != -1:
            # this is failure as it means that the schematic was not
            # properly annotated
            colors().printFail(
                "DESIGN IS NOT PROPERLY ANNOTATED, FOUND DESIGNATOR " +
                designator +
                " PLEASE ANNOTATE FIRST THE SCHEMATIC")
            # this is fatal and we cannot continue
            sys.exit(-1)
        # for this we use simple search, assuming that there is only
        # one number in the entire designator, and the designator is
        # unique. Saying this we can search regular expression and
        # extract beginning, number and ending
        pre, dig, post = re.findall('^([A-Za-z]+)(\d+)(.*)', designator)[0]
        # first we match joned beginning and end, which are textual
        return (pre+post, int(dig))

    def compareDesignators(self, left, right):
        """ parses numbers from designators and returns which of them
        is larger
        """
        strs1, dig1 = self.getDesignatorNumber(self.getText(left))
        strs2, dig2 = self.getDesignatorNumber(self.getText(right))

        # if strings differ, return their difference:
        if strs1 != strs2:
            return strs1 < strs2

        # if strings are the same, compare _numerically_ the results
        return dig1 < dig2

    def lessThan(self, left, right):
        """ makes comparison of two numbers/strings. We have to detect
        numbers in these things. The items given are modelindices
        """
        # having modelindices we can grab the text and check for
        # results depending of _column_.
        # if column is designator, we parse the data as
        # <chars><number> and sort according to number as integer
        if left.column() == self.header.getColumn(
                self.header.DESIGNATOR):
            return self.compareDesignators(left, right)

        # all other cases just simple textual comparison
        return self.getText(left) < self.getText(right)

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
            # if the index is disabled, we cannot do anything else with it
            # (so dropping will not work, editting neigher)
            srIx = self.mapToSource(index)
            srData = srIx.model().itemData(srIx)[self.header.ItemEnabled]
            if not srData:
                # item is disabled, return as no further actions are allowed
                return defaultFlags

            defaultFlags |= self.header.getFlags(index.column())
        except (KeyError, AttributeError):
            # index.column() can be -1 depending on what we're
            # pointing on. In this case we leave default flags as they are
            pass
        return defaultFlags

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

    def manuallyEnteredData(self, idsrc):
        """when user manually enters data into the model, we get its
        index (treeview index, not proxy index). This has to be used
        to update the data wrt designators. The index returned is the
        one of _MODEL_, not proxy
        """

        # a = self.mapFromSource(self.index(idsrc.row(),
        #                                   self.header.getColumn(
        #                                       self.header.DESIGNATOR)))

        # print(self.getText(a),idsrc.text())
        print("MANUAL ENTER")


    def getItemData(self, getAll=False):
        """ returns list of dictionaries containing the data from
        currently selected items. Second parameter specifies whether
        we should get all the rows (entire bom), or just selected portion
        """
        if not getAll:
            rows = self.getSelectedRows()
        else:
            rows = range(self.rowCount())

        collector = []
        for row in rows:
            # for each row we pick all the column data
            allCols = self.header.HEADER.keys()
            # map modelindexes
            allIdx = map(lambda cl: self.index(row, cl),
                         self.header.getColumns(allCols))
            # list all the texts in the same order as allCols
            allTxt = map(lambda idx: self.getText(idx, True), allIdx)
            # zip into dictionary with proper names
            allItem = dict(zip(allCols, allTxt))
            collector.append(allItem)
        return collector

    def selectionUnique(self):
        """ returns unique component libref/value/footprint if the
        current selection (i.e. libref/value/footprint) resolves in
        unique single component. This is used e.g. for looking into
        component cache. If the selection is not unique, none is returned
        """
        rows = self.getSelectedRows()
        # get the data out of those indices
        collector = defaultdict(list)
        # we need to convert iterator to list otherwise it cannot be
        # used in the loop
        colidx = list(self.header.getColumns(self.header.UNIQUEITEM))
        for row in rows:
            for icol in colidx:
                # get source index (remember, we are only proxy)
                txt = self.getText(self.index(row, icol), True)
                collector[icol].append(txt)
        # collected data get converted into sets, hence it will
        # erase all common parts
        # this will make (column, set) assignment such, that if
        # all the components selected are the same, it will result
        # in exactly 1 element in the list for each column
        c = list(map(lambda itext: (itext[0], set(itext[1])),
                     collector.items()))
        # so we filter the columns which have more than one
        # element
        moreOne = list(filter(lambda item: len(item[1]) != 1, c))
        # and if the list is _empty_, that is good as we can use
        # mapping. Note that c variable contains _set_ and not
        # list.
        if moreOne == []:
            # this is unique component, we can pop each item from set
            # to create simple dictionary
            a = dict(map(lambda dkey: (dkey[0], dkey[1].pop()), c))
            # so a is dictionary of e.g. this type:
            # {1: 'GRJ188R70J225KE11D', 2: 'GRJ188R70J225KE11D', 3:
            # 'Capacitors_SMD:C_0603'}
            # key is column name as defined in headers, we return
            # libref/value/footprint as unique identifier of the component
            return a
        return None

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
        # dictionary of all found items. We check here against the
        # instance, as dropMimeData is used as well by a direct
        # call when getting the data from the component cache as
        # the treatment is exactly the same, except that 'data' in
        # case of direct call contain already parsed data from the
        # component cache dictionary
        if isinstance(data, QtCore.QMimeData):
            parsed_data = self.suppliers.parse_URL(data.text())
        else:
            # get the data directly as this function was called
            # from context menu selection
            parsed_data = data

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
            # many items selected
            replace_in_rows = rows
        else:
            # only single item selected
            replace_in_rows = [treeparent.row(), ]

        # get the data out of those indices
        collector = defaultdict(list)
        colidx = self.header.getColumns(self.header.UNIQUEITEM)
        # list of affected designators
        affectedDesignators = []
        # now the data replacement. EACH ITEM HAS ITS OWN MODELINDEX
        # and we get the modelindices from parent. Do for each of them
        for row in replace_in_rows:
            # walk through each parsed item, and change the data
            for key, value in parsed_data.items():
                self.setData(
                    self.index(row,
                               self.header.getColumn(key)),
                    value)
            affectedDesignators.append(self.getText(
                self.index(row,
                           self.header.getColumn(
                               self.header.DESIGNATOR)), True))
            # the point with rows is, that we need to collect
            # libref/value/footprint for each selected row, as it
            # they are the same for the entire selection, we are
            # eligible to write down the component selection _into
            # the component cache_ to be reused for the next
            # time. This can be done only if the selection of the
            # component is unique otherwise we would make a mess
            # in the database
            for icol in colidx:
                # get source index (remember, we are only proxy)
                txt = self.getText(self.index(row, icol), True)
                collector[icol].append(txt)
        # collected data get converted into sets, hence it will
        # erase all common parts
        # this will make (column, set) assignment such, that if
        # all the components selected are the same, it will result
        # in exactly 1 element in the list for each column
        c = list(map(lambda itext: (itext[0], set(itext[1])),
                 collector.items()))
        # so we filter the columns which have more than one
        # element
        moreOne = list(filter(lambda item: len(item[1]) != 1, c))
        # and if the list is _empty_, that is good as we can use
        # mapping
        if moreOne:
            self.colors.printInfo("""Cannot store the dropped component\
 into the component cache, because the selection does not resolve in\
 unique LIBREF/VALUE/FOOTPRINT.""")
        else:
            # this is defaultdict of defaultdict, we can add
            # components into such dictionary even if they are not
            # created
            cmpn = dict(c)
            cls = list(self.header.getColumns(self.header.UNIQUEITEM))
            # we need to convert set back to list
            cnm = list(map(lambda idx: list(cmpn[idx])[0], cls))
            # Particular problem here
            # is that we need to detect duplicates in the
            # component mfg/no/ref/supplier. this is best done by
            # introducing unique key from parsed data, hash seems
            # to be OK. We add this hash as a separate dictionary
            # key (additional layer) so we're sure that if the
            # hash exists, the component of the same properties is
            # already entered and we ignore it
            cmphash = hashlib.md5(
                json.dumps(parsed_data,
                           sort_keys=True).encode("utf-8")).hexdigest()
            # now we need to generate all the sub-keys if they do not
            # exist. Before a defautdict generating defaultdict was
            # used, but this got hell to debug as anytime one tried to
            # read a key, it was created. this is not really what we
            # want, hence following generates the dictionary structure:
            if not cnm[0] in self.componentsCache:
                self.componentsCache[cnm[0]] = {}
            if not cnm[1] in self.componentsCache[cnm[0]]:
                self.componentsCache[cnm[0]][cnm[1]] = {}
            if not cnm[2] in self.componentsCache[cnm[0]][cnm[1]]:
                self.componentsCache[cnm[0]][cnm[1]][cnm[2]] = {}
            # and now if the component is unique and used for the
            # first time the hash is not found, however no keyerror is risen
            hashes = self.componentsCache[cnm[0]][cnm[1]][cnm[2]]
            if cmphash not in hashes.keys():
                # store in the component database
                self.componentsCache[cnm[0]]\
                    [cnm[1]]\
                    [cnm[2]]\
                    [cmphash] = parsed_data
                # and inform upper
                self.addedComponentIntoCache.emit()
                print("This component is used for first time,\
 writing into the component cache")

        # emit the change so upstream knows that we have just changed
        # components data. Problem are 'affectedDesignators', as
        # theoretically they should contain list of designators. In
        # fact in multichannel designs one designator can represent
        # multiple designators as a single text. we need to explode
        # those to basic elements and then regenerate affected
        # designators

        # this will explode all sub-designators from
        parsed = map(lambda x:
                     x.replace(' ', '').split(','),
                     affectedDesignators)
        # flatten all the designators
        flatten = [val for sublist in parsed for val in sublist]
        self.componentsDataChanged.emit(flatten,
                                        parsed_data)
        QtGui.QApplication.restoreOverrideCursor()
        return True
