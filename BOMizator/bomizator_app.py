#!/usr/bin/env python3
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
import webbrowser
import json
from collections import defaultdict
from functools import partial
from PyQt4 import QtGui, uic, QtCore
from itertools import chain
from .sch_parser import sch_parser
from .headers import headers
from .qdesignatorsortmodel import QDesignatorSortModel
from .colors import colors


localpath = os.path.dirname(os.path.realpath(__file__))
form_class = uic.loadUiType(os.path.join(localpath, "BOMLinker.ui"))[0]


class BOMizator(QtGui.QMainWindow, form_class):

    def __init__(self, projectDirectory, parent=None, flags=0):
        """ Constructing small window with tree view of all components
    present in the schematics. Directory points to the KiCad project
    directory containing .sch (they can be in sub-directories as well)
        """
        QtGui.QMainWindow.__init__(self, parent, QtCore.Qt.WindowFlags(flags))
        self.setupUi(self)

        # local settings are read directly from the project
        # directory. If exist, they store information about suppressed
        # items (and other things for the future)
        self.localSettings =\
            QtCore.QSettings(os.path.join(projectDirectory,
                                          "bomizator.ini"),
                             QtCore.QSettings.IniFormat)
        self.settings = QtCore.QSettings()
        # get from the options the path to the component cache - a
        # filename, which is used to store the data
        self.componentsCacheFile = self.settings.value(
            "componentsCacheFile",
            os.path.join(projectDirectory, "componentsCache.json"),
            str)
        print("Using component cache from %s" %
              (self.componentsCacheFile))
        # load the complete dictionary
        try:
            with open(self.componentsCacheFile) as data_file:
                self.componentsCache = json.load(data_file)
        except json.FileNotFoundError:
            self.componentsCache = {}
        self.projectDirectory = projectDirectory
        self.SCH = sch_parser(self.projectDirectory)
        self.SCH.parseComponents()

        self.model = QtGui.QStandardItemModel(self.treeView)
        # search proxy:
        self.proxy = QDesignatorSortModel(self.treeView, self.componentsCache)
        self.proxy.setSourceModel(self.model)
        self.proxy.setDynamicSortFilter(True)
        self.proxy.addedComponentIntoCache.connect(self.saveComponentCache)

        # assign proxy to treeView so we influence how the stuff is sorted
        self.treeView.setModel(self.proxy)
        self.treeView.setSortingEnabled(True)
        # get header object
        self.header = headers()

        sorted_header = self.header.getHeaders()
        self.model.setHorizontalHeaderLabels(sorted_header)
        # set sorting of treeview by designator
        self.treeView.sortByColumn(self.header.getColumn(
            self.header.DESIGNATOR), QtCore.Qt.AscendingOrder)

        # fill the model with the data
        hideDisabled = self.settings.value("hideDisabledComponents",
                                           False,
                                           bool)
        self.action_Hide_disabled_components.setEnabled(not hideDisabled)
        self.action_Show_disabled_components.setEnabled(hideDisabled)
        self.action_Hide_disabled_components.triggered.connect(
            lambda: self.hideShowDisabledComponents(True))
        self.action_Show_disabled_components.triggered.connect(
            lambda: self.hideShowDisabledComponents(False))

        self.fillModel(hideDisabled)
        # as the model is filled with the data, we can resize columns
        for i in range(len(self.header)):
            self.treeView.resizeColumnToContents(i)

        # connect signals to treeView so we can invoke search engines
        self.treeView.doubleClicked.connect(self.treeDoubleclick)
        self.treeView.selectionModel().selectionChanged.connect(
            self.treeSelection)
        # register accepting drops
        self.treeView.setAcceptDrops(True)
        self.treeView.setDropIndicatorShown(True)
        # and register custom context menu, which will be used as
        # 'filtering' to select correcly chosen indices
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.openMenu)

        # restore windows parameters
        self._readAndApplyWindowAttributeSettings()
        # update status for the first time
        self.treeSelection()

    def saveComponentCache(self):
        """ signal caught when component cache changed and save is required
        """
        with open(self.componentsCacheFile, 'wt') as outfile:
            json.dump(self.componentsCache, outfile)

    def rec_dd(self):
        """
        http://stackoverflow.com/questions/19189274/defaultdict-of-defaultdict-nested

function generating nested defaultdicts. Previously used for loading and
        operating the components cache, but as it turned out to be
        very dangerous to use, I'm reverting back to ordinary dictionary
        """
        return defaultdict(self.rec_dd)

    def hideShowDisabledComponents(self, hideComponents):
        """ if hideComponents is true, then the model to display all
        the components is restored from scratch and will not contain
        the hidden components.
        """
        self.action_Hide_disabled_components.setEnabled(not hideComponents)
        self.action_Show_disabled_components.setEnabled(hideComponents)
        # save the state into configfile
        self.settings.setValue("hideDisabledComponents",
                               hideComponents)
        self.fillModel(hideComponents)
        self.treeSelection()

    def fillModel(self, hideDisabled=True):
        """ resets the components treeview, and reloads it with the
        model data
        """
        # disabled designators are from separate file:
        # load all disabled designators (if any) from the settings
        # file
        disabledDesignators = self.localSettings.value(
            'disabledDesignators',
            [],
            str)
        # clearout the model
        self.model.removeRows(0, self.model.rowCount())
        # having headers we might deploy the data into the multicolumn
        # view. We need to collect all the data:
        for cmpCount, itemData in enumerate(self.SCH.BOM()):
            line = map(QtGui.QStandardItem, list(itemData))
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
            datarow = self.enableItems(shat, enabled)
            # now, if we want to see the disabled items in the menu:
            if (not hideDisabled and not enabled) or enabled:
                self.model.appendRow(datarow)
        # total amount of components in the data
        self.numComponents = cmpCount

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

    def treeSelection(self):
        """ When selection changes, the status bar gets updated with
        information about selection
        """
        default = "Loaded %d components." % (self.numComponents)
        # look on amount of disabled components,
        disabledDesignators = self.localSettings.value(
            'disabledDesignators',
            [],
            str)
        if len(disabledDesignators) > 0:
            default += " %d components disabled." % (len(disabledDesignators))

        # to display amount of selected components we need to
        # calculate how many rows is selected
        rows = set(map(lambda c: c.row(),
                       self.treeView.selectedIndexes()))
        if len(rows) > 0:
            default += " %d components selected." % (len(rows))
        self.statusbar.showMessage(default)

    def indexData(self, index, role=QtCore.Qt.DisplayRole):
        """ convenience function returning the data of given
        modelindex. Gets complicated because we are using filter
        proxy, hence the index has to be converted to source model index.
        """
        try:
            return self.proxy.itemData(index)[role]
        except KeyError:
            colors().printFail("ENABLE/DISABLE role does not exist:")
            print(self.proxy.itemData(index))
            raise KeyError

    def resizeEvent(self, event):
        """ reimplementation of resize event to store state into settings
        """
        super(BOMizator, self).resizeEvent(event)
        self._writeWindowAttributeSettings()

    def moveEvent(self, event):
        """ reimplementation of move event to store state into settings
        """
        super(BOMizator, self).moveEvent(event)
        self._writeWindowAttributeSettings()

    def closeEvent(self, event):
        """ reimplemented close to save window position
        """
        super(BOMizator, self).closeEvent(event)
        self._writeWindowAttributeSettings()

    def _readAndApplyWindowAttributeSettings(self):
        """ Read window attributes from settings, using current
        attributes as defaults (if settings not exist.) Called at
        QMainWindow initialization, before show().  """

        self.settings.beginGroup("mainWindow")
        self.restoreGeometry(self.settings.value("geometry",
                                                 self.saveGeometry()))
        self.restoreState(self.settings.value("saveState", self.saveState()))
        self.move(self.settings.value("pos", self.pos()))
        self.resize(self.settings.value("size", self.size()))
        if self.settings.value("maximized", self.isMaximized()):
            self.showMaximized()

        self.settings.endGroup()

    def _writeWindowAttributeSettings(self):
        """ Save window attributes as settings.
        Called when window moved, resized, or closed. """
        self.settings.beginGroup("mainWindow")
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("saveState", self.saveState())
        self.settings.setValue("maximized", self.isMaximized())
        if not self.isMaximized():
            self.settings.setValue("pos", self.pos())
            self.settings.setValue("size", self.size())
        self.settings.endGroup()

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
        menu = QtGui.QMenu()
        execMenu = False

        # ###############################################################################
        # WHEN RIGHT CLICK ON DATASHEET, PROPOSE ITS OPENING
        if len(indexes) == 1 and\
           indexes[0].column() ==\
           self.header.getColumn(self.header.DATASHEET):
            # create menu and corresponding action
            self.datasheet = self.indexData(indexes[0])
            open_action = menu.addAction(
                self.tr("Open %s" % (self.datasheet, )))
            open_action.triggered.connect(self.openDatasheet)
            execMenu = True

        # ###############################################################################
        # WHEN RIGHT CLICK ON LIBREF/VALUE/FOOTPRINT such that only
        # one of them is selected, propose selecting filter
        #
        # variant 2: we can select from libref, value, footprint in
        # each column _single item only_, and this one can be used to
        # create a selection mask. From obvious reasons selecting TWO
        # DIFFERENT LIBREFs e.g. does not make any sense. The same for
        # other columns. Only these three (for the moment) can be used
        # to form a filter as the others are 'user fillable', hence
        # can contain whatever information, ergo hell to make filter
        # first we have to make a 'histogram', i.e. counting
        # occurences of columns.
        if self.proxy.selectionUnique():
            menu.addAction(self.tr("Select same"), self.selectSameFilter)

        # ###############################################################################
        # WHEN RIGHT CLICK ON ANY ITEM(s) PROPOSE ENABLE/DISABLE
        #
        # in all other possibilities it depends whether the item(s)
        # are enabled or disabled. We can select 'whatever' and make
        # it enabled/disabled. Modus operandi is e.g. following: i
        # select 10k 1206 resistors by selecting one, then right click
        # to select all of them, then right click to disable/enable
        # selected.
        # first we find whether at least is enabled or at least one
        # disabled, and depending of that we add context menus. NOTE
        # THAT ENABLE/DISABLE ALWAYS WORKS ON ENTIRE ROWS EVEN IF ONLY
        # SINGLE CELL IS SELECTED. Following returns list of
        # enable/disable for each index in the selection. NOTE THAT WE
        # HAVE TO MAP THE PROXY SELECTION TO SOURCE AS THESE ARE NOT
        # THE SAME MODELINDEXES. and we are setting this property on
        # self.model indices and not on self.proxy indices
        enabled = list(map(lambda index:
                           self.model.itemData(
                               self.proxy.mapToSource(
                                   index))[self.header.ItemEnabled],
                           indexes))
        # if any of these is true, there's at least one element enabled
        oneEnabled = any(enabled)
        # if all are enabled, then there's not a single one disabled:
        oneDisabled = not all(enabled)
        # let's add menus
        if oneDisabled:
            menu.addAction(self.tr("Enable"),
                           partial(self.enableProxyItems,
                                   True))
            execMenu = True
        if oneEnabled:
            menu.addAction(self.tr("Disable"),
                           partial(self.enableProxyItems,
                                   False))
            execMenu = True
        if oneEnabled and oneDisabled:
            menu.addAction(self.tr("Invert enable/disable"),
                           partial(self.invertProxyEnableItems,
                                   False))
            execMenu = True

        # ###############################################################################
        # WHEN RIGHT CLICK ON ANY ITEMS, WHICH HAVE FILLED ALREADY
        # INFORMATION, PROPOSE CLEAR
        idata = self.proxy.getItemData()
        # now we search through all user defined items to see if all
        # of them are empty
        rowdata = []
        for item in idata:
            # filter interesting data - keep non-zero ones and only
            # those which are user definable
            idata = filter(lambda component:
                           (component[0] in self.header.USERITEMS) and
                           component[1] != '', item.items())
            rowdata.append(list(idata))
        allEmpty = all(map(lambda ctr: not ctr, rowdata))
        # if at least one is not empty, we add option to clear out
        if not allEmpty:
            menu.addAction(self.tr("Clear assignments"),
                           self.proxy.clearAssignments)
            execMenu = True

        # ###############################################################################
        # WHEN RIGHT CLICK ON COMPONENTS(s) PROPOSE COMPONENT FROM
        # CACHE IF THAT ONE EXISTS AND SELECTION RESOLVES TO UNIQUE
        # COMPONENT
        # last part of context menu is to look for components in cache
        try:
            component = self.proxy.selectionUnique()
            # map cols to list as needed:
            idxs = map(self.header.getColumn, self.header.UNIQUEITEM)
            # get indices into cmpcache:
            itms = list(map(lambda cx: component[cx], idxs))
            # this is not so nicely implemented, is there any other way
            # how to check in nested defaultdicts if the key exists?
            if itms[0] in self.componentsCache:
                if itms[1] in self.componentsCache[itms[0]]:
                    if itms[2] in self.componentsCache[itms[0]][itms[1]]:
                        # get all the reference data
                        refdata = self.componentsCache[itms[0]]\
                                  [itms[1]]\
                                  [itms[2]].items()
                        # we have specific components, we can add them
                        # into the menu such, that it will trigger
                        # automatic refill
                        menu.addSeparator()
                        # for hashed, data in refdata:
                        for hashed, cmpData in refdata:
                            # we have to construct the string to be
                            # displayed.
                            txt = cmpData[self.header.MANUFACTURER] +\
                                " " +\
                                cmpData[self.header.MFRNO] +\
                                " from " +\
                                cmpData[self.header.SUPPLIER]
                            menu.addAction(txt,
                                           partial(self.fillFromComponentCache,
                                                   cmpData))
                        execMenu = True
        except TypeError:
            # seletion is not unique
            pass

        if execMenu:
            menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def fillFromComponentCache(self, cmpData):
        """ function called from context menu when user selects a
        unique component and this component is found in the component
        cache such, that it fits the libref/value/footprint. Inthis
        case a context menu will contain name of this component. When
        triggered, this function is called with cmpData containing the
        dictionary with mfg/mfgno/supplier/supplierno/datasheet. This
        function mimics 'dropMimeData' action to fully reuse its
        implementation to fill-in these data in the selected
        rows/components (which can be one or many depending of how the
        user selects the items)
        """
        # we have to have at least one selected index as otherwise we
        # do not know where to stick the data
        aa = self.treeView.selectedIndexes()[0]
        self.proxy.dropMimeData(cmpData, None, -1, -1, aa)

    def enableProxyItems(self, enable):
        """ looks for all selected items in proxy, maps them into base
        and enables/disables as needed.
        """
        indexes = self.treeView.selectedIndexes()
        rowsAffected = set(list(map(lambda ix: ix.row(), indexes)))
        # having rows we can pull out all items from specific rowCount
        allItems = []
        for row in rowsAffected:
            singlerow = map(lambda col: self.model.itemFromIndex(
                self.proxy.mapToSource(self.proxy.index(row, col))),
                            range(self.model.columnCount()))
            allItems += list(singlerow)
        self.enableItems(allItems, enable)
        # and now we run through _all the items int the list_ and
        # check whether they are enabled/disabled and write it down
        # into the configuration file (local settings file) such, that
        # next time the disabled items are properly marked. We do not
        # care here going through proxy
        desig = map(lambda row: (self.model.item(row, 0).text(),
                            self.model.item(row, 0).data(
                                self.header.ItemEnabled)),
                    range(self.model.rowCount()))
        # filter disabled designators
        disab = list(map(lambda d: d[0], filter(lambda des: not des[1], desig)))
        # list of disabled components is stored in local settings file
        self.localSettings.setValue('disabledDesignators', disab)
        self.treeSelection()

    def selectSameFilter(self):
        """ in treeview selects the rows matching the selected items filters
        """
        # we have unique columns selected, and now we need to browse
        # each row of data, check if all the conditions are satisfied,
        # and if so, then select the columns
        indexes = self.treeView.selectedIndexes()
        # get dictionary of 'column':filter_data
        d = defaultdict(int)
        for index in indexes:
            d[index.column()] = self.indexData(index)
        # and this has to be done in model as we're working over model
        # data. filter is a dictionary 'column':<filter_string>
        to_enable = self.proxy.setSelectionFilter(d)
        for idx in to_enable:
            self.treeView.selectionModel().select(
                idx,
                QtGui.QItemSelectionModel.Select)

    def openDatasheet(self):
        """ opens the browser with datasheet
        """
        # now fire the web browser with this page opened
        b = webbrowser.get('firefox')
        b.open(self.datasheet, new=0, autoraise=True)

    def openSearchBrowser(self, searchtext):
        """ This function calls default plugin to supply the web
        search string for a given text. This one is then used to open
        a browser window with searched item. Now, searching does not
        mean at all that the component will be found straight away. It
        just means that a page with search resuls will open, and user
        it responsible to look for a specific component further.
        """
        url = self.proxy.suppliers.search_for_component(searchtext)
        # now fire the web browser with this page opened
        b = webbrowser.get('firefox')
        b.open(url, new=0, autoraise=True)

    def treeDoubleclick(self, index):
        """ when user doubleclicks item, we search for it in farnel
        (or later whatever else) web pages. this requires a lot of
        fiddling as the component search enginer for each seller are
        different. Index is the type QModelIndex
        """
        # we process only columns libref and value as those are used
        # to search (most of the time)
        if index.column() in self.header.getColumns([self.header.LIBREF,
                                                     self.header.VALUE]):
            self.openSearchBrowser(self.indexData(index))


def main():
    """
    Main application body
    """

    app = QtGui.QApplication(sys.argv)
    # general settings file as follows
    QtCore.QCoreApplication.setOrganizationName("dejfson")
    QtCore.QCoreApplication.setOrganizationDomain("github.com/dejfson")
    QtCore.QCoreApplication.setApplicationName("bomizator")

    # if not given directory from the command line, ask for it
    try:
        projdir = sys.argv[1]
    except IndexError:
        projdir = str(
            QtGui.QFileDialog.getExistingDirectory(None,
                                                   app.tr("Select\
 KiCad project directory")))
    myWindow = BOMizator(projdir)
    myWindow.show()
    app.exec_()
