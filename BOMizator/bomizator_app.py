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
import fnmatch
import json
from collections import defaultdict
from functools import partial
from PyQt4 import QtGui, uic, QtCore
from .headers import headers
from .colors import colors
from .qdesignatorsortmodel import QDesignatorSortModel
from .qbommodel import QBOMModel
from .sch_parser import schParser
from .qbomitemmodel import QBOMItemModel

localpath = os.path.dirname(os.path.realpath(__file__))
form_class = uic.loadUiType(os.path.join(localpath, "BOMLinker.ui"))[0]


class BOMizator(QtGui.QMainWindow, form_class):

    def __init__(self, projectDirectory='', parent=None, flags=0):
        """ Constructing small window with tree view of all components
    present in the schematics. Directory points to the KiCad project
    directory containing .sch (they can be in sub-directories as well)
        """
        QtGui.QMainWindow.__init__(self, parent, QtCore.Qt.WindowFlags(flags))
        self.setupUi(self)
        self.supplierInfo = QtGui.QLabel("")
        self.statusbar.addPermanentWidget(self.supplierInfo)
        self.isModified = False
        try:
            self.projectDirectory = self.openProject(projectDirectory)
        except ValueError:
            print("Cannot continue as not clear what project is to be\
 parsed")
            sys.exit(-1)

        # show/hide disabled components
        self.action_Hide_disabled_components.triggered.connect(
            lambda: self.hideShowDisabledComponents(True))
        self.action_Show_disabled_components.triggered.connect(
            lambda: self.hideShowDisabledComponents(False))
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
        # multiplier
        self.bomMultiplier.returnPressed.connect(self.newMultiplier)
        self.bomMultiplier.setValidator(QtGui.QIntValidator(1, 100))
        self.bomApply.clicked.connect(self.newMultiplier)
        # tab widget: we intercept tab change signal as everytime we
        # come to BOM, we have to re-create the data from scratch as
        # looking for changes would be complicated
        self.tabWidget.currentChanged.connect(self.tabChanged)
        self.tabWidget.setCurrentIndex(0)
        # switching tab in tablebiew
        # various menu items
        self.action_Quit.triggered.connect(self.close)
        self.action_Open.triggered.connect(self.openProject)
        self.action_Save.triggered.connect(self.saveProject)
        self.action_Reload.triggered.connect(self.reloadProject)
        # restore windows parameters
        self._readAndApplyWindowAttributeSettings()
        # update status for the first time
        self.treeSelection()

    def newMultiplier(self):
        """ called when global multiplier changed
        """
        orig = self.SCH.getGlobalMultiplier()
        new = int(self.bomMultiplier.text())
        if orig != new:
            print("newone")
            self.SCH.setGlobalMultiplier(new)
            self.modelModified(True)

    def tabChanged(self, newidx):
        """ when tab changes to BOM, we need to reload the treeview
        with new model data
        """
        # @TODO implement recreation of BOMview from data
        if self.tabWidget.tabText(newidx) == "BOM":
            # we have to re-create the new item model for BOM display
            # data
            self.bomTree = QBOMItemModel(self.SCH,
                                         self.disabledComponentsHidden)
            self.bomView.setModel(self.bomTree)
            # and resize columns
            self.bomView.expandAll()
            for i in range(self.bomTree.columnCount()):
                self.bomView.resizeColumnToContents(i)
            # setup multiplier
            self.bomMultiplier.setText("%d" % (self.SCH.getGlobalMultiplier()))

    def saveProject(self):
        """ this function generates the data out of all the components
        in the current data model, and passes these components to
        schematics parser to save
        """
        self.SCH.save()
        self.modelModified(False)

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

        self.disabledComponentsHidden = hideComponents
        self.action_Hide_disabled_components.setEnabled(not hideComponents)
        self.action_Show_disabled_components.setEnabled(hideComponents)
        # save the state into configfile
        self.settings.setValue("hideDisabledComponents",
                               hideComponents)
        self.model.fillModel(self.SCH.getDisabledDesignators(),
                             hideComponents)
        self.treeSelection()

    def treeSelection(self):
        """ When selection changes, the status bar gets updated with
        information about selection
        """
        default = "Loaded %d components." % (self.model.rowCount())
        # look on amount of disabled components,
        disabledDesignators = self.SCH.getDisabledDesignators()
        if len(disabledDesignators) > 0:
            default += " %d components disabled." % (len(disabledDesignators))

        # to display amount of selected components we need to
        # calculate how many rows is selected
        rows = set(map(lambda c: c.row(),
                       self.treeView.selectedIndexes()))
        if len(rows) > 0:
            default += " %d components selected." % (len(rows))
        self.statusbar.showMessage(default)

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
        if self.model.isModified():
            msgBox = QtGui.QMessageBox(self)
            msgBox.setText(self.tr("The document has been modified"))
            msgBox.setInformativeText(self.tr(
                "Do you want to save your changes?"))
            msgBox.setStandardButtons(
                QtGui.QMessageBox.Save |
                QtGui.QMessageBox.Discard |
                QtGui.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtGui.QMessageBox.Save);

            reply = msgBox.exec_();

            if reply == QtGui.QMessageBox.Cancel:
                event.ignore()
                return

            if reply == QtGui.QMessageBox.Save:
                # save data first
                self.saveProject()

        event.accept()
        self._writeWindowAttributeSettings()

    def modelModified(self, isModified):
        """ signal caught from model whenever its content changes. A
        main window title is updated
        """
        md = '*'
        if not isModified:
            md = ''

        self.setWindowTitle("BOMIZATOR - %s %s" % (
            md,
            self.projectDirectory))

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

    def getSelectedRows(self):
        """ returns tuple of rows, which are selected. This is done by
        looking through the rows and columns and detecting
        selections. THE MODELINDEXES RETURNED ARE RELATED TO MODEL AND
        NOT PROXY
        """
        a = []
        lc = map(self.proxy.mapToSource,
                 self.treeView.selectedIndexes())
        for index in lc:
            a.append(index.row())
        # treeview always returns proxied models
        return set(a)

    def clearAssignments(self):
        """ instructs model to delete selected item data
        """
        self.model.clearAssignments(self.getSelectedRows())

    def openMenu(self, position):
        """ opens context menu. Context menu is basically a
        right-click on any cell requested. The column and row is
        parsed, and depending of which column was used to select the
        context menu contains appropriate filter offers. In case of
        clicking over datasheet it opens the datasheet in the
        browser. In case of libref it can choose the same components
        etc...
        """

        # INDEX GOT FROM TREEVIEW IS ALWAYS LINKED TO PROXY AND NOT
        # MODEL. IF DATA FROM ROWS ARE TO BE LOADED, THEY NEED TO BE
        # MAPPED FIRST THROUGH THE PROXY
        inxx = self.treeView.selectedIndexes()
        # remap all indices to model
        indexes = list(map(self.proxy.mapToSource, inxx))
        if len(indexes) < 1:
            return

        # if the selection is unique, the component is here:
        component = self.model.selectionUnique(self.getSelectedRows())

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
            datasheet = indexes[0].data()
            open_action = menu.addAction(
                self.tr("Open %s" % (datasheet, )))
            open_action.triggered.connect(partial(self.openBrowser,
                                                  datasheet))
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
        if component:
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
                           self.model.data(index, self.header.ItemEnabled),
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

        # ###############################################################################
        # WHEN RIGHT CLICK ON ANY ITEMS, WHICH HAVE FILLED ALREADY
        # INFORMATION, PROPOSE CLEAR
        idata = self.model.getItemData(self.getSelectedRows())
        # now we search through all user defined items to see if all
        # of them are empty
        rowdata = []
        for item in idata:
            # filter interesting data - keep non-zero ones and only
            # those which are user definable
            idata = filter(lambda cxomponent:
                           (cxomponent[0] in self.header.USERITEMS) and
                           cxomponent[1] != '', item.items())
            rowdata.append(list(idata))
        allEmpty = all(map(lambda ctr: not ctr, rowdata))
        # if at least one is not empty, we add option to clear out
        if not allEmpty:
            menu.addAction(self.tr("Clear assignments"),
                           self.clearAssignments)
            execMenu = True

        # ################################################################################
        # WHEN RIGHT CLICK ON (EXISTING), SUPPLIERNO SEARCH THE
        # SUPPLIER NUMBER USING HIS WEB PAGES
        if component and\
           indexes[0].column() ==\
           self.header.getColumn(self.header.SUPPNO):
            iData = self.model.getItemData(self.getSelectedRows())[0]
            url = self.model.suppliers.getSearchString(
                iData[self.header.SUPPLIER],
                iData[self.header.SUPPNO])
            # create menu and corresponding action
            menu.addSeparator()
            menu.addAction(
                self.tr("Open supplier's web page searching for %s" % (iData[self.header.SUPPNO])),
                partial(self.openBrowser, url))
            execMenu = True

        # ###############################################################################
        # WHEN RIGHT CLICK ON COMPONENTS(s) PROPOSE COMPONENT FROM
        # CACHE IF THAT ONE EXISTS AND SELECTION RESOLVES TO UNIQUE
        # COMPONENT
        # last part of context menu is to look for components in cache
        try:
            component = self.model.selectionUnique(self.getSelectedRows())
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
            colors().printWarn("Selection is not unique, cannot\
 propose cached component")
            pass

        if execMenu:
            menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def reloadProject(self):
        """ reloads the project. asks for being sure as it rewrites
        all the changes already performed
        """
        if self.model.isModified():
            msg = self.tr("""Reloading project will discard all unsaved
 changes. Do you want to continue?""")
            reply = QtGui.QMessageBox.question(self, self.tr('Message'),
                                               msg,
                                               QtGui.QMessageBox.Yes,
                                               QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.Yes:
                # reopens the same project
                self.openProject(self.projectDirectory)
        else:
            self.openProject(self.projectDirectory)

    def getProjectPaths(self, projectDirectory):
        """ project directory can be either directory, or link to
        project file. We have to parse them to return file and
        directory separately so they can be used to load and save the data
        """

        if os.path.isfile(projectDirectory):
            projectFile = projectDirectory
        else:
            matches = []
            # find all project files within the directory (there should be
            # one theoretically, but we accept any number, i.e. when
            # subdirectory is given)
            for root, dirnames, filenames in os.walk(projectDirectory):
                for filename in fnmatch.filter(filenames, '*.pro'):
                    matches.append(os.path.join(root, filename))

            if matches == []:
                raise AttributeError('Provided directory does not contain\
 any kicad schematic files')
            projectFile = matches[0]
        projectDirectory = os.path.split(projectFile)[0]

        return projectFile, projectDirectory

    def openProject(self, projectDirectory=''):
        """ Opens directory search dialog, which asks for .pro file to
        be used as project.  .pro is generated by kicad. It accepts as
        well projectDirectory which can be directory pointing to
        project, or directly the project file. Returns none if no
        selection was done (cancelled dialog)
        """
        canContinue = False
        if not projectDirectory or\
           (not os.path.isfile(projectDirectory) and
            not os.path.isdir(projectDirectory)):
            # if not given directory from the command line, ask for it
            dlg = QtGui.QFileDialog()
            dlg.setFilter("Kicad project file (*.pro)")
            if dlg.exec_():
                canContinue = True
                projdir = dlg.selectedFiles()
                # we get directly the file
                projectDirectory = projdir[0]
        else:
            canContinue = True

        if canContinue:
            projectFile, projectDirectory = self.getProjectPaths(projectDirectory)
            # we have to find a single project file
            self.SCH = schParser(projectFile)
            self.SCH.parseComponents()

            self.settings = QtCore.QSettings()
            # get from the options the path to the component cache - a
            # filename, which is used to store the data
            self.componentsCacheFile = self.settings.value(
                "componentsCacheFile",
                os.path.join(projectDirectory, "componentsCache.json"),
                str)
            print("Using component cache from %s" %
                  (self.componentsCacheFile))
            # load the complete dictionary if exists. (either in
            # project directory, or if generally specified)
            try:
                with open(self.componentsCacheFile) as data_file:
                    self.componentsCache = json.load(data_file)
            except FileNotFoundError:
                self.componentsCache = {}
            # generate new schematic parser
            self.model = QBOMModel(self.SCH,
                                   self.componentsCache,
                                   self)
            self.model.droppedData.connect(self.droppedData)
            self.model.modelModified.connect(self.modelModified)
            self.model.addedComponentIntoCache.connect(self.saveComponentCache)
            # having model means that we know all the plugins
            # available and we can fill-in the plugins for searching
            self.menu_Suppliers.clear()
            for shortcut, plg in self.model.getPlugins():
                # now we add for each plugin incorporated
                self.menu_Suppliers.addAction(plg,
                                              partial(self.pluginChanged,
                                                      plg),
                                              QtGui.QKeySequence(ord("S"), ord(shortcut)))

            # search proxy:
            self.proxy = QDesignatorSortModel(self)
            self.proxy.setSourceModel(self.model)
            self.proxy.setDynamicSortFilter(True)
            # @TODO saving cache of components
            self.treeView.setModel(self.proxy)
            self.treeView.setSortingEnabled(True)
            # get header object
            self.header = headers()
            # set sorting of treeview by designator
            self.treeView.sortByColumn(self.header.getColumn(
                self.header.DESIGNATOR), QtCore.Qt.AscendingOrder)

            # fill the model with the data
            self.disabledComponentsHidden = self.settings.value(
                "hideDisabledComponents",
                False,
                bool)
            self.action_Hide_disabled_components.setEnabled(
                not self.disabledComponentsHidden)
            self.action_Show_disabled_components.setEnabled(
                self.disabledComponentsHidden)

            # load lastly used plugin
            lastPlugin = self.settings.value("lastUsedSearchPlugin",
                                             "FARNELL",
                                             str)
            self.pluginChanged(lastPlugin)

            self.model.fillModel(self.SCH.getDisabledDesignators(),
                                 self.disabledComponentsHidden)
            # as the model is filled with the data, we can resize columns
            for i in range(len(self.header)):
                self.treeView.resizeColumnToContents(i)

            self.projectDirectory = projectDirectory
            self.modelModified(False)

        # if projectfile exists, we better return this as it helps us
        # to determine exactly what .pro file user wants (otherwise we
        # have to search through default directory)
        if not canContinue:
            raise ValueError("No project given")

        try:
            return projectFile
        except UnboundLocalError:
            return projectDirectory

    def droppedData(self, data, row, column):
        """ catches when data are dropped into the model. Data have to
        be textual and will be parsed by one of the suppliers strings.
        """

        # first we find all items, which are selected. we are only
        # interested in rows, as those are determining what
        # designators are used.
        rows = self.getSelectedRows()
        # and with all selected rows we distinguish, whether we have
        # dropped the data into selected rows. If so, we will
        # overwritte all the information in _each row_. If however the
        # drop destination is outside of the selection, we only
        # replace given row
        if row in rows:
            # many items selected
            replace_in_rows = rows
        else:
            # only single item selected
            replace_in_rows = [row, ]
        self.model.updateModelData(replace_in_rows, data)

    def pluginChanged(self, newplugin):
        """ sets new default plugin
        """
        self.model.setDefaultPlugin(newplugin)
        # update supplier in status bar
        self.supplierInfo.setText(newplugin)
        self.settings.setValue("lastUsedSearchPlugin",
                               newplugin)

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
        aa = self.proxy.mapToSource(self.treeView.selectedIndexes()[0])
        self.droppedData(cmpData, aa.row(), aa.column())

    def enableProxyItems(self, enable):
        """ looks for all selected items in proxy, maps them into base
        and enables/disables as needed. This function is called from
        contextmenu when enable/disable is selected
        """
        rowsAffected = self.getSelectedRows()
        # having rows we can pull out all items from specific rowCount
        allItems = []
        for row in rowsAffected:
            singlerow = map(lambda col: self.model.itemFromIndex(
                self.model.index(row, col)),
                            range(self.model.columnCount()))
            allItems += list(singlerow)
        # instructs model to disable all designators. This is just a
        # view issue, nothing to do with real data storage. This
        # inside calls setData with specific user role, which triggers
        # in the model datachanged and hence sets up correctly
        # disabled designators
        self.model.enableItems(allItems, enable)
        # if we currently do not show the disabled components (in a
        # view), we have to remove the line from the model completely
        if self.disabledComponentsHidden:
            # we have to remove the row from the view. Problem with
            # removing is, that we have to do it one by one, _and_
            # when we remove a row, all indexing gets nuts, hence we
            # need to sort first the rows, then iterate over them and
            # subtract from index already rows existing
            rows = sorted(list(set(map(lambda ie: ie.row(), allItems))))
            for index, row in enumerate(rows):
                self.model.removeRows(row - index, 1)

        self.treeSelection()

    def selectSameFilter(self):
        """ in treeview selects the rows matching the selected items filters
        """
        # we have unique columns selected, and now we need to browse
        # each row of data, check if all the conditions are satisfied,
        # and if so, then select the columns. Indexes in in PROXY
        indexes = self.treeView.selectedIndexes()
        # get dictionary of 'column':filter_data
        d = defaultdict(int)
        for index in indexes:
            d[index.column()] = index.data()
        # and this has to be done in model as we're working over model
        # data. filter is a dictionary 'column':<filter_string>
        to_enable = map(self.proxy.mapFromSource,
                        self.model.setSelectionFilter(d))
        for idx in to_enable:
            self.treeView.selectionModel().select(
                idx,
                QtGui.QItemSelectionModel.Select)

    def openBrowser(self, page):
        """ opens the browser with datasheet
        """
        # now fire the web browser with this page opened
        b = webbrowser.get('firefox')
        b.open(page, new=0, autoraise=True)

    def openSearchBrowser(self, searchtext):
        """ This function calls default plugin to supply the web
        search string for a given text. This one is then used to open
        a browser window with searched item. Now, searching does not
        mean at all that the component will be found straight away. It
        just means that a page with search resuls will open, and user
        it responsible to look for a specific component further.
        """
        url = self.model.suppliers.searchForComponent(searchtext)
        # now fire the web browser with this page opened
        b = webbrowser.get('firefox')
        b.open(url, new=0, autoraise=True)

    def treeDoubleclick(self, index):
        """ when user doubleclicks item, we search for it in farnel
        (or later whatever else) web pages. this requires a lot of
        fiddling as the component search enginer for each seller are
        different. Index is the type QModelIndex _but_ of PROXY and
        not directly the model
        """
        # we process only columns libref and value as those are used
        # to search (most of the time)
        idx = self.proxy.mapToSource(index)
        if idx.column() in self.header.getColumns([self.header.LIBREF,
                                                   self.header.VALUE]):
            self.openSearchBrowser(index.data())


def main():
    """
    Main application body
    """

    app = QtGui.QApplication(sys.argv)
    # general settings file as follows
    QtCore.QCoreApplication.setOrganizationName("dejfson")
    QtCore.QCoreApplication.setOrganizationDomain("github.com/dejfson")
    QtCore.QCoreApplication.setApplicationName("bomizator")
    try:
        project = sys.argv[1]
    except IndexError:
        project = ''
    myWindow = BOMizator(project)
    myWindow.show()
    app.exec_()
