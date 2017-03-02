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
This is a class taking care about loading all the plugins of sellers
and their web search iterfaces
"""

import os
import imp
import fnmatch
from .colors import *


class supplier_selector(object):
    """ Looks into a specific directory for all the python modules
    there, loads them into internal array, and defines their interfaces
    """

    # define what to look for in modules
    main_module = "__init__"

    def __init__(self, plugins_directory='suppliers'):
        """ looks through plugins directory and loads all the plugins
        """

        # this is usually overwritten by upper class to give a seller name
        localpath = os.path.dirname(os.path.realpath(__file__))
        self.plugins_directory = os.path.join(
            localpath,
            plugins_directory)
        print("Loading plugins from ", self.plugins_directory, ":")
        self.plugins = self.get_plugins()
        self.set_default_plugin('FARNELL')
        # and now we're ready to accept search queries

    def set_default_plugin(self, plugin):
        """ sets the default search plugin engine
        """
        self.default_plugin = plugin
        # generate constructor with appropriate search plugin
        self.engine = self.plugins[self.default_plugin]

    def parse_URL(self, urltext):
        """ Uses all plugins installed to detect if one of the plugins
        can accept the web page URL and parse its content to get the
        data into right format. If so, this function returns a dictionary
        containing: (Manufacturer, Mfg. reference, Supplier, Supplier
        reference, datasheet). NOT ALL SUPPLIERS CAN RESOLVE THE
        INFORMATION. The best one seems to be farnell, which provides
        all this information in the URL directly. Radiospares is
        clumsy. Digikey seems to be as good as farnell in parsing from
        URL. First one which matches is the valid one.
        """
        print(COLORINFO+"Searching in plugins:"+COLORNUL)
        for name, plug in self.plugins.items():
            try:
                print(COLORNUL+"\tChecking "+name+" ... ", end='')
                data = plug.parse_URL(urltext)
                print(COLOROK+"FOUND"+COLORNUL)
                return data
            except KeyError:
                print(COLORFAIL+"NOT FOUND"+COLORNUL)
                pass
        # when here, no plugin matched the selection, raise KeyError
        print(COLORFAIL +
              "No installed plugin matches the URL selection" +
              COLORNUL)
        raise KeyError

    def get_url(self, searchtext):
        """ Using default plugin the search text is translated into
        URL, which can be used to open the web pages
        """
        return self.engine.get_url(searchtext)

    def get_plugins(self):
        """ walks through plugins directory and returns list of plugins
        """

        plugins = []
        plugins_classes = {}
        for root, dirnames, filenames in os.walk(self.plugins_directory):
            for filename in fnmatch.filter(filenames, '*.py'):
                plugins.append(os.path.join(root, filename))

        for plugin in plugins:
            # skip __init__.py if there's any
            if self.main_module + ".py" in plugin:
                continue

            # each plugin has to have DEFAULT_CLASS attribute defined,
            # which sets up the class name to be. Plugin filename must
            # correspond to class defined inside
            info = imp.load_source('', plugin).DEFAULT_CLASS
            print("\t", info().name)
            plugins_classes[info().name] = info()
        return plugins_classes

    def search_for_component(self, component):
        """ returns URL to be used in the component search for
        _active_ supplier
        """
        return self.get_url(component)
