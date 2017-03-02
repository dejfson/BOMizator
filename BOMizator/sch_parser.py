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
from .colors import *


class sch_parser(object):
    """ Parses the KiCad schematics files for components
    """

    def __init__(self, dirname):
        """ dirname = KiCad project directory containing schematics files
        """
        self.dirname = dirname
        self.debug = False
        self.matches = []
        # we cannot do a simple looking for schematic files. Instead
        # we need to walk through the files and look for particular
        # project file, which tells us (from the filename), which is
        # the top-level schematic. this one has to be then parsed for
        # $sheet items and their attributes to see all the schematic
        # files appearing in the project. If we do not do so, we might
        # parse schematic files, which are broken, or are not part of
        # the project.
        self.matches = self.collectFiles()

        self.current_state = self._sm_catch_header
        self.components = defaultdict(list)

        # define attributes dictionary for the component, each entry
        # has to correspond to specific attributes
        self.attribute_entry = {
            'L': self._attribute_generic,
            'U': self._attribute_generic,
            'P': self._attribute_generic,
            'A': self._attribute_generic,
            'F': self._attribute_f,
            '\t': self._attribute_tab,
            '$': self._attribute_termination}

    def collectFiles(self):
        """ uses project directory to pass through the projects
        """

        matches = []
        # find all project files within the directory (there should be
        # one theoretically, but we accept any number, i.e. when
        # subdirectory is given)
        for root, dirnames, filenames in os.walk(self.dirname):
            for filename in fnmatch.filter(filenames, '*.pro'):
                matches.append(os.path.join(root, filename))

        if matches == []:
            raise AttributeError('Provided directory does not contain\
 any kicad schematic files')

        # having the project file the top-level schematic shares the
        # filenames, we can recursively search through using simple
        # parsing
        projectFiles = []
        for project in matches:
            fname = os.path.splitext(project)[0]+'.sch'
            dirname, core = os.path.split(fname)
            for fn in os.listdir(dirname):
                if core.lower() == fn.lower():
                    # case insensitive match of the file:
                    toparse = os.path.join(dirname, fn)
                    projectFiles += self.getSheets(toparse)
        return projectFiles

    def getSheets(self, fname):
        """ opens the sheet fname, parses it for sub-sheets and
        returns their list.
        """
        print(COLORINFO+"Parsing "+fname+COLORNUL)
        subsheet = []
        with open(fname, "rt") as f:
            insheet = False
            for line in f:
                if line.startswith("$Sheet"):
                    insheet = True
                elif line.startswith("F1 ") and insheet:
                    # we have reached an attribute of the sheet, which
                    # tells us the filename of a subsheet
                    sht = line.split(" ")[1].replace('"', '')
                    dirname, core = os.path.split(fname)
                    # append proper dirname and re-request to parse
                    # the sub-sheet in this moment
                    subsheet += self.getSheets(
                        os.path.join(dirname, sht))
                elif line.startswith('$EndSheet') and insheet:
                    insheet = False
        return [fname, ] + subsheet


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
        print(line)
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
                if self.debug:
                    print("Found component ",
                          self.current_component['L'][1], ":",
                          self.current_component['F']['1'][0])
                self.components[
                    self.current_component['L'][1]] = self.current_component

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
        print(self.matches)
        for fname in self.matches:
            print(COLORINFO+"Parsing "+fname+COLORNUL)
            with open(fname, "rt") as f:
                # parsing the file for specific tokens of component
                # start/stop is a simple state machine
                for line in f:
                    self.current_state(line)

    def strip_quote(self, text):
        """ helper function replacing quotes by empty string
        """
        return text.replace('"', '')

    def BOM(self):
        """ iterator returns always a text-based list of [designator,
        library part, manufacturer, mfg reference]. If some of those
        do not exist, empty strings are returned. The returned tuple
        contains following information:
        [ designator, libref, value, footprint,
        """

        # this kind of data to be expected:
        # Q1 {'P': ['8900', '9700'], 'U': ['1', '1', '589E4C6E'], 'L':
        # ['BSS138', 'Q1'], 'X': ['1    8900 9700', '1    0    0
        # -1'], 'F': {'1': ['"BSS138"', 'H', '9091', '9655', '50', '',
        # '0000', 'L', 'CNN'], '0': ['"Q1"', 'H', '9091', '9746',
        # '50', '', '0000', 'L', 'CNN'], '3': ['""', 'H', '-1950',
        # '2100', '50', '', '0001', 'L', 'CNN'], '2':
        # ['"TO_SOT_Packages_SMD:SOT-23"', 'H', '-1750', '2025', '50',
        # '', '0001', 'L', 'CIN'], '4': ['"2306392"', 'H', '8900',
        # '9700', '60', '', '0001', 'C', 'CNN', '"FARNELL"']}}

        # or for resistance:
        # {'P': ['8550', '9850'], 'U': ['1', '1', '589E4F2C'], 'L':
        # ['R', 'R7'], 'X': ['1    8550 9850', '1    0    0    -1'],
        # 'F': {'1': ['"10k"', 'H', '8620', '9805', '50', '', '0000',
        # 'L', 'CNN'], '0': ['"R7"', 'H', '8620', '9896', '50', '',
        # '0000', 'L', 'CNN'], '3': ['""', 'H', '-1600', '1700', '50',
        # '', '0001', 'C', 'CNN'], '2': ['"Resistors_SMD:R_1206"',
        # 'V', '-1670', '1700', '50', '', '0001', 'C', 'CNN']}}

        for key, value in self.components.items():
            data = [value['L'][1],  # designator
                    value['L'][0],  # library reference
                    self.strip_quote(value['F']['1'][0]),  # value of component
                    self.strip_quote(value['F']['2'][0])]  # footprint

            # now we have to see in 'L' attributes entires correct
            # attribute names
            datasheet, mfg, mfgno = '', '', ''
            for f_number, f_data in value['F'].items():
                if int(f_number) == 3:
                    # datasheet (this is part of schematics)
                    datasheet = self.strip_quote(f_data[0])
                elif int(f_number) > 3 and\
                     f_data[-1].find("supplier_ref") != -1:
                    # supplier reference number
                    mfgno = self.strip_quote(f_data[0])
                elif int(f_number) > 3 and\
                     f_data[-1].find("supplier") != -1:
                    # supplier name
                    mfg = self.strip_quote(f_data[0])

            yield data + [mfg, mfgno, datasheet]

if __name__ == '__main__':
    # test stuff
    a = sch_parser('/home/belohrad/git/beaglebone_relay_multiplexor/beaglebone_relad_kicad')
    a.parse_components()
