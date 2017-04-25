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
Implements proxy for reporting plugins
"""
import logging
import os
import fnmatch
import imp


class reports_selector(object):
    """ Creates a proxy environment for reporting the BOMs
    """

    def __init__(self, plugins_directory='reports'):
        """ looks through plugins directory and loads all the plugins
        """

        self.logger = logging.getLogger('bomizator')
        # this is usually overwritten by upper class to give a seller name
        localpath = os.path.dirname(os.path.realpath(__file__))
        self.plugins_directory = os.path.join(
            localpath,
            plugins_directory)
        self.logger.info("Loading report plugins from " +
                         self.plugins_directory + ":")
        self.plugins = self.getPlugins()
        # and now we're ready to accept search queries

    def getPlugins(self):
        """ walks through plugins directory and returns list of plugins
        """

        plugins = []
        plugins_classes = {}
        for root, dirnames, filenames in os.walk(self.plugins_directory):
            for filename in fnmatch.filter(filenames, '*.py'):
                plugins.append(os.path.join(root, filename))

        for plugin in plugins:
            # skip __init__.py if there's any
            if "__init__.py" in plugin:
                continue

            # each plugin has to have DEFAULT_CLASS attribute defined,
            # which sets up the class name to be. Plugin filename must
            # correspond to class defined inside
            info = imp.load_source('', plugin).DEFAULT_CLASS
            self.logger.info("\t" + info().name)
            plugins_classes[info().name] = info()
        return plugins_classes

    def generateBOM(self, plugin, data, additional={}):
        """ calls appropriate plugin to generate BOM data
        """
        self.plugins[plugin].generateBOM(data, additional)
