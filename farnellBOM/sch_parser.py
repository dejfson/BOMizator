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
Class responsible for simple parsing of SCH files. It takes as input
argument a directory and searches for all .sch files, then looks for
all the embedded components
"""

import fnmatch
import os
from collections import defaultdict

class sch_parser(object):
    """ Parses the KiCad schematics files for components
    """

    def __init__(self, dirname):
        """ dirname = KiCad project directory containing schematics files
        """
        self.dirname = dirname

        self.matches = []
        for root, dirnames, filenames in os.walk(self.dirname):
            for filename in fnmatch.filter(filenames, '*.sch'):
                self.matches.append(os.path.join(root, filename))

        self.current_state = self._sm_catch_header
        self.components = defaultdict(list)

        # define attributes dictionary for the component, each entry
        # has to correspond to specific attributes
        self.attribute_entry = {
            'L': self._attribute_generic,
            'U': self._attribute_generic,
            'P': self._attribute_generic,
            'F': self._attribute_f,
            '\t': self._attribute_tab,
            '$': self._attribute_termination}


    def _sm_catch_header(self, line):
        """ state machine state catching the component start in the
        line of the code. line is a single line read from the
        schematic file
        """
        if line.startswith("$Comp"):
            self.current_component = {}
            self.current_state = self._sm_component_body

    def _sm_component_body(self, line):
        """ state machine state decoding the body of the
        component. This is done by looking for each particular
        attributes and processing them into separate flags, added into
        current_component dictionary
        """
        # the point here is, that we use the first character as a
        # deteminant of which attribute the component entry
        # corresponds to. If it is not found, then the 'default' line
        # attribute is assigned
        self.attribute_entry[line[0]](line.strip())


    def _attribute_termination(self, line):
        """ dollar sign introduces entity ending
        """
        if line.startswith('$EndComp'):
            # state machine ends here and we store the component
            # information into the list of components, we have to
            # check here if it is not a power supply or ground, as
            # these are in principle not components
            if not self.current_component['L'][1].startswith('#'):
                print "Found component ",\
                    self.current_component['L'][1], ":",\
                    self.current_component['F']['1'][0]
                self.components[self.current_component['L'][1]] = self.current_component

            self.current_state = self._sm_catch_header

    def _attribute_generic(self, line):
        """ parses 'L' attribute of the component. This type of
        attribute is generic, e.g. L MCP23016 U2, where first value is
        library reference, and we just store all the parameters from
        this one to a list, which we add as dictionary item
        """
        attrs = line.split(" ")
        self.current_component[line[0]] = attrs[1:]

    def _attribute_tab(self, line):
        """ tab attribute starts the component body, we keep these
        parameters as they are, just add them into the list
        """
        try:
            self.current_component['X'].append(line)
        except KeyError:
            self.current_component['X'] = []
            self.current_component['X'].append(line)

    def _attribute_f(self, line):
        """ F-type attributes are different. the second number is
        specific. There can be up to 11 F parameters depending of
        values which user uses as data fields in the components. We
        are interested in supplier and supplier_ref attributes, as
        those are used for us to generate the bill of material. First
        4 parameters are _given_ by specs of kicad, the additional up
        to 11 are user specific. We have to explode these into list of
        lists separately. Typically the F attributes might look like
        this:

        F 0 "U2" H 6450 6900 50  0000 C CNN
        F 1 "MCP23016-I/SO" H 6300 6800 50  0000 C CNN
        F 2 "Housings_SOIC:SOIC-28W_7.5x17.9mm_Pitch1.27mm" H 1250 -3050 50  0001 L CNN
        F 3 "" H 1350 -1100 50  0001 C CNN
        F 4 "1439758" H 5900 5800 60  0001 C CNN "supplier_ref"
        F 5 "FARNELL" H 5900 5800 60  0001 C CNN "supplier"

        """

        data = line.split(" ")
        # what we do here: F attribute is just another dictionary with
        # key equal to attribute number (as they have to be exported
        # in the same way later), all the rest of the attributes is
        # stored 'as is' and various manipulation functions have to
        # deal with it.
        try:
            self.current_component['F'][data[1]] = data[2:]
        except KeyError:
            # for the first time
            self.current_component['F'] = {}
            self.current_component['F'][data[1]] = data[2:]



    def parse_components(self):
        """ after initial filenames matching this function parses all
        the schematics files and gets the components names from the
        files. These are pulled into the dictionary, which is later on
        used either to get the info about the component, _or_ add/modify
        appropriate attributes.
        """
        for fname in self.matches:
            with open(fname, "rt") as f:
                # parsing the file for specific tokens of component
                # start/stop is a simple state machine
                for line in f:
                    self.current_state(line)

a = sch_parser('/home/belohrad/git/beaglebone_relay_multiplexor/beaglebone_relad_kicad')
a.parse_components()
