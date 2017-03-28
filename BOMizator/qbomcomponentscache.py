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
implements caching mechanism of the components dropped by
user. Caching is based on making a relationship between
libref/value/footprint and appropriate component dragged by user from
web page into the application. Component cache allows an efficient
reuse of the previously selected components such, that in another
project the same components can be used
"""
from PyQt5 import QtCore
from .headers import headers
import json
import hashlib


class QBOMComponentCache(QtCore.QObject):
    """ takes care about the component cache handling
    """

    """ emitted when cache stores another component
    """
    addedComponentIntoCache = QtCore.pyqtSignal(dict, dict)

    def __init__(self, cacheFile):
        """ initializes component cache based on application settings
        and the project directory. cacheFile is CLASS HANDLER, which
        takes care about loading/saving. Typically cacheFileAccess or
        cacheGitAccess when GIT handling is involved
        """
        super(QBOMComponentCache, self).__init__()
        self.componentsCacheFile = cacheFile
        self.header = headers()
        self.componentsCache = cacheFile.load()

    def findComponent(self, itms):
        """ given dictionary of (libref, value, footprint) this function
        returns dictionary items of the component. None is returned if
        no component with these three items exists
        """
        try:
            refdata = self.componentsCache[itms[self.header.LIBREF]]\
                      [itms[self.header.VALUE]]\
                      [itms[self.header.FOOTPRINT]].items()
        except KeyError:
            refdata = None
        return refdata

    def createKey(self, keydata):
        """ in the cache creates libref/value/footprint key
        """
        try:
            a = self.componentsCache[keydata[self.header.LIBREF]]
        except KeyError:
            self.componentsCache[keydata[self.header.LIBREF]] = {}

        try:
            b = self.componentsCache[keydata[self.header.LIBREF]]\
                [keydata[self.header.VALUE]]
        except KeyError:
            self.componentsCache[keydata[self.header.LIBREF]]\
                [keydata[self.header.VALUE]] = {}

        try:
            c = self.componentsCache[keydata[self.header.LIBREF]]\
                    [keydata[self.header.VALUE]]\
                    [keydata[self.header.FOOTPRINT]]
        except KeyError:
            self.componentsCache[keydata[self.header.LIBREF]]\
                [keydata[self.header.VALUE]]\
                [keydata[self.header.FOOTPRINT]] = {}

        return self.componentsCache[keydata[self.header.LIBREF]]\
                [keydata[self.header.VALUE]]\
                [keydata[self.header.FOOTPRINT]]

    def storeComponents(self, complist, data):
        """ complist is a list of dictionary of libref/value/footprint
        for each component to store the data. data is the dictionary
        of manufacturing/supplier/datasheet etc stuff which should
        be used for particular components
        """
        # generate data hash, this is unique identifier of data
        # (manuf+supp+...)
        cmphash = hashlib.md5(
            json.dumps(data,
                       sort_keys=True).encode("utf-8")).hexdigest()

        for component in complist:
            # we have to find if the component is already used or not
            # we make a hash of all values of each component. these
            # should be only libref, value, footprint
            try:
                cmpdict = self.componentsCache[component[self.header.LIBREF]]\
                          [component[self.header.VALUE]]\
                          [component[self.header.FOOTPRINT]]
            except KeyError:
                # the key does not exist at all, let's create it
                cmpdict = self.createKey(component)

            if cmphash in cmpdict.keys():
                # component already defined in cache by some previous
                # operations, no need to do anything here
                continue
            self.componentsCache\
                [component[self.header.LIBREF]]\
                [component[self.header.VALUE]]\
                [component[self.header.FOOTPRINT]]\
                [cmphash] = data
            self.addedComponentIntoCache.emit(data, component)

    def save(self):
        """ signal caught when component cache changed and save is required
        """
        self.componentsCacheFile.save(self.componentsCache)
