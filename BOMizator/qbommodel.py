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
Implements bill-of-material model
"""

from PyQt5 import QtGui, QtCore, QtWidgets
import hashlib
import json
from collections import defaultdict
from .supplier_selector import supplier_selector
from .headers import headers
from .suppexceptions import ComponentParsingFailed
import logging


class QBOMModel(QtGui.QStandardItemModel):
    """ reimplementation of standard item model to get the data load
    structure.
    """

    """ signal emitted when user shifts the data into a cell from the
    web browser. The information cannot be processed directly, but has
    to be processed by parent, as this one should take care about what
    data and where to store them. Typically is that user drops data
    into already selected cell, which means that they are copied to
    all selected cells. Unfortunately information about who is
    selected is not available in the model, but in
    treeview. Information contained is the dropped string parsed into
    dictionary parameters of
    supplier/supplierno/manufacturer/manufacturer_no/datasheet, which
    can be used to setup the information in the cell. Further returned
    row and column of where drop happened
    """
    droppedData = QtCore.pyqtSignal(dict, int, int)

    """ signal informing that a component was added into the cache. To
    be cached in app to store the cache appropriately """
    addedComponentIntoCache = QtCore.pyqtSignal()

    """ modelModified is emitted whenever model data change (=True) or
    when the model gets saved (=False)
    """
    modelModified = QtCore.pyqtSignal(bool)

    """ emitted when enable/disable on particular components is issued
    """
    enabledComponents = QtCore.pyqtSignal(int)

    def __init__(self, projectData=None,
                 componentsCache={},
                 parent=None):
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
        super(QBOMModel, self).__init__(parent)
        self.logger = logging.getLogger('bomizator')
        self.componentsCache = componentsCache
        self.SCH = projectData
        self.setModified(False)
        self.header = headers()
        # get all sellers filters
        self.suppliers = supplier_selector()
        self.componentsCache = componentsCache

        sorted_header = self.header.getHeaders()
        self.setHorizontalHeaderLabels(sorted_header)

        # hook when cell data changed by some model editing. This
        # should perform SCH write
        self.itemChanged.connect(self.cellDataChanged)

    def getPlugins(self):
        """ returns list of identified plugins of suppliers as read
        from the plugins directory. Each list item is a tuple saying
        (<shortcut string>, <pluginname>. Example: [('F',
        "FARNELL"),]. This can be used to get quick action on
        searching just by choosing proper shortcut. Note that MAP
        ITERATOR is returned.
        """
        spl = self.suppliers.getPlugins()
        return zip(
            map(self.suppliers.getShortcut, spl),
            spl)

    def setDefaultPlugin(self, plg):
        """ sets new default search plugin
        """
        self.suppliers.setDefaultPlugin(plg)

    def getDesignator(self, row):
        """ takes row in MODEL perspective and returns string
        identifying designator for that particular row. Designator is
        a string, which MAY contain multiple designators when
        hierarchical design involved
        """
        return self.itemFromIndex(self.index(row,
                                             self.header.getColumn(
                                                 self.header.DESIGNATOR)))

    def isModified(self):
        """ returns true if the model was modified and not saved
        """
        return self.modified

    def cellDataChanged(self, item):
        """ Any data change in the model (e.g. by calling setData, or
        by manually typing the data into editable columns) will emit
        signal, which we intercept here. The item is the _new value_
        of the item in the data structure. We modify here components
        definitions such, that the newly entered data will match the
        underlying component data. the data item is in MODEL
        space. Unfortunately standard item model does not allow to
        identify what _exactly_ changed, so we have to always operate
        on all data
        """
        # the way how we change the data is that we modify the
        # underlying schematic components dictionary
        colname = self.header.getColumnName(item.column())
        desigItem = self.getDesignator(item.row())
        # first update the enable/disable designator of the given
        # component.
        self.SCH.enableDesignator(desigItem.text(),
                                  item.data(self.header.ItemEnabled))
        self.SCH.updateComponents(
            [desigItem.text(), ],
            {colname: item.text()})
        self.setModified(True)

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
            srData = index.model().itemData(index)[self.header.ItemEnabled]
            if not srData:
                # item is disabled, return as no further actions are allowed
                return defaultFlags

            defaultFlags |= self.header.getFlags(index.column())
        except (KeyError, AttributeError):
            # index.column() can be -1 depending on what we're
            # pointing on. In this case we leave default flags as they are
            pass
        return defaultFlags

    def enableItems(self, stidems, enable=True):
        """ info whether item is disabled or enabled is stored in user
        role, as we do not want to disable the item completely (that's
        because when disabled, it is not selectable any more). This
        function takes all the stitems and enables, disables
        them. This is done by setting role of BOMizator.ItemEnabled on
        a particular index. NOTE THAT THIS FUNCTION HAS TO BE ALWAYS
        CALLED FOR ALL STDITEMS FROM A ROW AS WE WANT TO DISABLE THE
        COMPONENTS BY ROWS. Function returns the original list.
        """
        for xi in stidems:
            # we enable the line
            xi.setData(enable, self.header.ItemEnabled)
            if enable:
                xi.setForeground(QtGui.QColor('black'))
            else:
                xi.setForeground(QtGui.QColor('gray'))
        return stidems

    def setModified(self, xmodified):
        """ sets modification flag and emits modelModified when any
        change happens
        """
        try:
            announce = False
            if self.modified != xmodified:
                announce = True
            self.modified = xmodified
        except AttributeError:
            self.modified = xmodified
            announce = True

        if announce:
            self.modelModified.emit(xmodified)

    def fillModel(self, disabledDesignators=[],
                  hideDisabled=False):
        """ Fills in the model based on textual representation
                  (schParser) and hides/does not hide components,
                  which are marked as disabled.
        """
        # clearout the model
        self.removeRows(0, self.rowCount())
        # having headers we might deploy the data into the multicolumn
        # view. We need to collect all the data:
        for designatorKey in self.SCH.BOM():

            component = self.SCH.getComponent(designatorKey)
            # each component can have multiple designators. That
            # because when hierarchical schematics are used, the
            # components share the same definition, but using AR
            # attribute they get more designators as the same
            # component is used in multiple sheets. Hence we have to
            # iterate over the designators and pull each of them
            # separately to the table. NOTE THAT THIS CREATES TROUBLES
            # FOR BOM, AS USER MIGHT WANT TO SPECIFY FOR DIFFERENT
            # CHANNELS DIFFERENT VALUE COMPONENTS. Typically this
            # might be e.g. gains in channel amplifiers. In this model
            # it will allow such change, but the problem is that KICAD
            # does not recognize those as two separate components, but
            # one component having link to two designators. HENCE
            # EXPORTED SCH WILL ONLY CONTAIN THE VALUE WHICH IS SAVED
            # AS LAST. For the moment I do not think that this has
            # some simple solution, as that's the way kicad handles
            # those. Hence we will display BOTH DESIGNATORS AT THE
            # SAME TIME IN THE DESIGNATOR COLUMN TO SHOW UP THAT THIS
            # SITUATION HAPPENS
            desiline = component.copy()
            # normalised designator is printed out in designator
            # column. This one is a join of sorted designators.
            desiline[self.header.DESIGNATOR] = designatorKey

            line = map(QtGui.QStandardItem,
                       list(map(lambda c:
                                desiline[c],
                                self.header.getHeaders())))
            # set all items to be enabled by default
            columns = self.header.getColumns([self.header.DESIGNATOR,
                                              self.header.LIBREF,
                                              self.header.VALUE,
                                              self.header.FOOTPRINT])
            editable = filter(lambda item: item in columns, line)
            map(lambda ei: ei.setEditable(False), editable)
            # depending if designator is disabled/enabled we set it up
            shat = list(line)
            enabled = True
            if shat[0].text() in disabledDesignators:
                enabled = False
            # sets disabled all the data rows
            dataload = self.enableItems(shat, enabled)
            # now, if we want to see the disabled items in the menu:
            if (not hideDisabled and not enabled) or enabled:
                self.appendRow(dataload)

    def getItemData(self, rows):
        """ returns list of dictionaries containing the data from
        currently selected items. Second parameter specifies whether
        we should get all the rows (entire bom), or just selected
        portion. List of number of rows in MODEL is expected to
        identify data to fetch
        """

        collector = []
        for row in rows:
            # for each row we pick all the column data
            allCols = self.header.HEADER.keys()
            # map modelindexes
            allIdx = map(lambda cl: self.index(row, cl),
                         self.header.getColumns(allCols))
            # list all the texts in the same order as allCols
            allTxt = map(lambda idx: self.data(idx), allIdx)
            # zip into dictionary with proper names
            allItem = dict(zip(allCols, allTxt))
            collector.append(allItem)
        return collector

    def getComponent(self, desig):
        return self.SCH.getComponent(desig)

    def selectionUnique(self, rows):
        """ returns unique component libref/value/footprint if the
        current selection (i.e. libref/value/footprint) resolves in
        unique single component. This is used e.g. for looking into
        component cache. If the selection is not unique, none is
        returned. rows is a list of rows IN MODEL mapping (hence not proxy)
        """
        # get the data out of those indices
        collector = defaultdict(list)
        # we need to convert iterator to list otherwise it cannot be
        # used in the loop
        colidx = list(self.header.getColumns(self.header.UNIQUEITEM))
        for row in rows:
            for icol in colidx:
                # get source index (remember, we are only proxy)
                txt = self.data(self.index(row, icol))
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

    def setSelectionFilter(self, filt):
        """ Runs through all the rows in the data, checks if
        appropriate columns have the same data as those specified in
        filters, and if so, the all filter cells are 'selected'. This
        works over the default sorting, hence all rows are always
        searched. filt is a dictionary containing key = column, value
        = data which have to be present in a given column. Function
        returns list of modelindexes which should be selected as they
        match the filter. RETURNED INDIXES ARE IN MODEL SPACE
        """
        # list of modelindexes to be set selected in treeview
        toSelect = []
        for row in range(self.rowCount()):
            # get indices of all columns
            items = []
            for col, value in filt.items():
                idx = self.index(row, int(col))
                idxval = self.data(idx, QtCore.Qt.DisplayRole)
                if idxval == value:
                    # this condition fits, we can add it into items:
                    items.append(idx)
            # here if all conditions are satisfied, then items length
            # should be the same as dict length:
            if len(items) == len(filt):
                # we have those items, we can set them selected
                toSelect += items
        return toSelect

    def clearAssignments(self, rows):
        """ all selected rows data get cleared. This will only remove
        the information from the list, but the component cache stays
        intact (hence once component entered into the component cache,
        it will not be removed unless cache is updated
        externally). ROWS IS A LIST OF ROWS TO AFFECT IN MODEL VIEW
        """
        # get the data out of those indices
        colidx = list(self.header.getColumns(self.header.USERITEMS))
        for row in rows:
            # apply only for enabled items:
            if self.data(self.index(row,
                                    self.header.getColumn(
                                        self.header.DESIGNATOR)),
                         self.header.ItemEnabled):
                for col in colidx:
                    self.setData(self.index(row, col), "")

    def dropMimeData(self, data, action, row, column, treeparent):
        """ takes care of data modifications. The data _must contain_
        URL from the web pages of one of the pages supported by
        plugins. This is verified against the suppliers object, which
        returns correctly parsed data. The function emits droppedData
        with first argument being dictionary of values dropped into a cell
        """

        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            textstr = self.suppliers.parseURL(data.text())
            self.droppedData.emit(
                textstr,
                treeparent.row(),
                treeparent.column())
            ret = True
        except ComponentParsingFailed as e:
            self.logger.critical(str(e))
            ret = False
        finally:
            QtWidgets.QApplication.restoreOverrideCursor()
        return ret

    def updateModelData(self, replace_in_rows, parsed_data):
        """ takes the input parsed_data and updates all the rows of
        the model to contain data from parsed_data. Parsed_data is
        dictionary of header:value to be updated. Rows is a list of
        affected rows IN MODEL VIEW (ours)
        """

        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)

        # get the data out of those indices
        collector = defaultdict(list)
        colidx = self.header.getColumns(self.header.UNIQUEITEM)
        # now the data replacement. EACH ITEM HAS ITS OWN MODELINDEX
        # and we get the modelindices from parent. Do for each of them
        for row in replace_in_rows:
            # walk through each parsed item, and change the data
            for key, value in parsed_data.items():
                mind = self.index(row,
                                  self.header.getColumn(key))
                if self.data(mind,
                             self.header.ItemEnabled):
                    self.setData(mind, value)
            # the point with rows is, that we need to collect
            # libref/value/footprint for each selected row, as it
            # they are the same for the entire selection, we are
            # eligible to write down the component selection _into
            # the component cache_ to be reused for the next
            # time. This can be done only if the selection of the
            # component is unique otherwise we would make a mess
            # in the database
            for icol in colidx:
                txt = self.data(self.index(row, icol))
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
            self.logger.info("""Cannot store the dropped component\
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
                self.logger.info("This component is used for first time,\
 writing into the component cache")
            self.modelModified.emit(True)

        QtWidgets.QApplication.restoreOverrideCursor()
        return True
