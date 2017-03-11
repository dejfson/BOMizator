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

import os
from collections import defaultdict
from .colors import colors
from .headers import headers
from .qdesignatorcomparator import QDesignatorComparator
import shlex
from PyQt4 import QtCore


class schParser(object):
    """ Parses the KiCad schematics files for components
    """

    def __init__(self, projectFile):
        """ projectFile points to a specific .pro file from KiCad
        """
        self.projectFile = projectFile

        # configuration filename is derived from projectname
        cfile = os.path.splitext(self.projectFile)[0]
        # projectDirectory is correctly pointing to given place
        # set of actions to initialize the model
        # local settings are read directly from the project
        # directory. If exist, they store information about suppressed
        # items (and other things for the future)
        self.localSettings =\
            QtCore.QSettings(os.path.join(cfile,
                                          ".bmz"),
                             QtCore.QSettings.IniFormat)
        self.debug = False
        self.header = headers()
        # we cannot do a simple looking for schematic files. Instead
        # we need to walk through the files and look for particular
        # project file, which tells us (from the filename), which is
        # the top-level schematic. this one has to be then parsed for
        # $sheet items and their attributes to see all the schematic
        # files appearing in the project. If we do not do so, we might
        # parse schematic files, which are broken, or are not part of
        # the project.
        self.matches = set(self.collectFiles())

        self.current_state = self._smCatchHeader
        # components is a dictionary of dict. each component is
        # identified by dictionary of
        # designator/libref/value/footprint .... to uniquely match it
        # to the bill of material. IF SOME ATTRIBUTES DO NOT EXIST (as
        # e.g. mfg), they are not created during the file writing, but
        # they are created on fly by a dynamic assignment of the data.
        # this list is the one giving the BOM data
        self.components = {}

        # define attributes dictionary for the component, each entry
        # has to correspond to specific attributes
        self.attribute_entry = {
            'L': self._attributeGeneric,
            'U': self._attributeGeneric,
            'P': self._attributeGeneric,
            'A': self._attributeAr,
            'F': self._attributeF,
            '\t': self._attributeTab,
            '$': self._attributeTermination}

        # disabled designators are those which are 'grayed out' and
        # any modification operation over them is ignored. Their list
        # is loaded from project configuration file
        self.loadDisabledDesignators()

    def loadDisabledDesignators(self):
        """ stores list of disabled operators into the local set
        """
        self.disabledDesignators = set(self.localSettings.value(
            'disabledDesignators',
            [],
            str))
        print(self.disabledDesignators)

    def getDisabledDesignators(self):
        """ returns _set_ of currently disabled designators. We return
        set because it represents unique items. Each designator is
        only single unique item (even if containing multiple designators)
        """
        return self.disabledDesignators

    def disableDesignators(self, desig):
        """ list of designators provided will be stored in the
        designator file.
        """
        print(desig)

    def updateComponents(self, targets, newdata):
        """ Update all the componenents identified by list of
        normalised designators by new data for each key of
        newdata. Newdata is a dictionary of
        items to change, designators is a list of designators whose
        values have changed
        """
        # we filter all the components having the designators. Problem
        # here is, that in order to filter items of interest we need
        # to compare if one of the designators is in one of the set of
        # the components, and we need to do it one by one (due to
        # multichannel design)
        complist = map(lambda tg: self.components[tg], targets)
        for target in complist:
            # we browse here all the components and update their
            # parameters
            for key, val in newdata.items():
                target[key] = val

    def getComponent(self, normDesig):
        """ returns component identified by normalised designator
        """
        return self.components[normDesig]

    def save(self):
        """ function parses all the project schematic files,
        identifies all the components and _replaces particular
        attributes_ to get all the information from the treeview
        stored directly in kicad sch as attribute. Now, the attribute
        in kicad corresponding to 'user' attribute is the one starting
        with 'F'. First three F attributes (F0, F1, F2) are defined
        purpose. The F3 attribute is 'documentation',
        i.e. datasheet. All other attributes are user definable and
        have following format:
        F 4 "1737246" H 9850 1300 60  0001 C CNN "FARNELL"

        F4 is the attribute, followed by attribute's value,
        horizontal, x, y, length, visibility, center, further, and at
        the end the attribute name, which is in this case farnell. WE
        CANNOT IMPOSE THE ATTRIBUTE NUMBER TO BE FIXED as user might
        already enter another attributes from the schematic, but we
        can make our own just by adding first free number, or we can
        modify already existing ones, if these are different from the
        data given.

        The data variable is the complete dictionary of the data to be
        changed. They are only updated in the schematics if the
        attribute of a given component is either missing, or different
        from our data.

        The algorithm for save uses the same mechanism as loading the
        data - the state machine parses the document, identifying
        header, position, designator etc, and when in saving mode we
        put an attention into parsing the F attributes and their
        change depending of currently detected designator.

        """

        # first save project variables
        self.localSettings.setValue('disabledDesignators',
                                    self.disabledDesignators)

        # then parse schematic files and make them update the
        # parameters
        inComponent = False
        # go through all the schematic files
        for schfile in self.matches:
            # and now let's run through
            with open(schfile, "rt") as codeline:
                # first let's open new filename
                with open(schfile+"tmp", "wt") as wrline:
                    for code in codeline:
                        # by default the line we write into output
                        # file is the same as input one
                        lineOut = code
                        # let's wait until component header gets in
                        if not inComponent and\
                           code.startswith("$Comp"):
                            inComponent = True
                            # ignore is used to skip all
                            # non-interesting components, starting
                            # with hash (as e.g. #PWR11)
                            ignore = False
                            # clear out such, that if some attributes
                            # were not identified during traversing
                            # the list, they would cause keyerror
                            designator, libref = None, None
                            center = None
                            replaceby = None
                        # end of component identified
                        elif inComponent and\
                             code.startswith("$EndComp"):
                            inComponent = False
                        # catching L attribute containing footprint
                        # and designator.
                        elif inComponent and not ignore and\
                             code.startswith("L "):
                            # get designator and reference
                            _, libref, designator = shlex.split(code)
                            # and we can identify which component
                            # we're replacing. There has to be
                            # _exactly one_. If not, there's an issue!
                            # (so that's why we do not try here, but
                            # assume)
                            if designator.startswith("#"):
                                ignore = True
                            else:
                                # the point is: EACH DESIGNATOR MUST
                                # RESOLVE IN EXACTLY ONE COMPONENT. If
                                # not, this is an error. It gets slightly
                                # more difficult as hierarchical designs
                                # export multiple designators for each
                                # component if that one is part of a
                                # shared sheet. That's why we're looking
                                # for a designator in _set of
                                # designators_. For this we not only
                                # use normalised designator as key
                                # into self.components, but each
                                # component as well keeps a separate
                                # set of those designators, so they
                                # can be easily searched for
                                datain = list(
                                    filter(lambda com:
                                           designator in com[
                                               self.header.DESIGNATOR],
                                           self.components.values()))[0]
                                # we need to create a copy for poping
                                # the data out (such we find which
                                # items are still to be written into
                                # the component)
                                replaceby = datain.copy()
                                # we pop out items, which are
                                # non-writable:
                                replaceby.pop(self.header.VALUE)
                                replaceby.pop(self.header.FOOTPRINT)
                                replaceby.pop(self.header.LIBREF)
                                replaceby.pop(self.header.DESIGNATOR)
                                # save highest seen F attribute
                                # (needed to add new attr)
                                highestF = 0
                        # we can completely ignore here U and AR attributes as
                        # well as numeric attributes because we do not
                        # need them. We however need P attribute just
                        # in case to add new (not-existing) attribute
                        elif inComponent and not ignore and\
                             code.startswith("P "):
                            # center point of the component
                            center = shlex.split(code)[1:]
                        # F-parameters - the core of our work: we have
                        # to look on their content and modify/add if
                        # necessary.
                        elif inComponent and not ignore and\
                             code.startswith("F "):
                            # here we have to split lexically as
                            # parameters might contain spaces within
                            # quotes, which count as a single string
                            fattr = shlex.split(code)
                            # store highest F attribute seen
                            if highestF < int(fattr[1]):
                                highestF = int(fattr[1])

                            # we completely ignore attribures F0->F2
                            # as they identify component
                            if fattr[1] not in ['0', '1', '2']:
                                # follow custom attributes. F3 is
                                # always present and it is a
                                # datasheet, we always overwrite it
                                # this will _ONLY REPLACE EXISTING
                                # ATTRIBUTES_
                                if fattr[1] == '3':
                                    # refurbish datasheet attribute
                                    lpart = ' '.join(
                                        [fattr[0], fattr[1]] +
                                        ['"' +
                                         replaceby.pop(self.header.DATASHEET) +
                                         '"', ] +
                                        fattr[3:7])
                                    rpart = ' '.join(fattr[7:])
                                    lineOut = lpart + "  " + rpart + "\n"
                                elif fattr[-1] in replaceby.keys():
                                    # we have found one of the
                                    # attributes, modify its value
                                    lpart = ' '.join(
                                        [fattr[0], fattr[1]] +
                                        ['"' +
                                         replaceby.pop(fattr[-1]) +
                                         '"', ] +
                                        fattr[3:7])
                                    rpart = ' '.join(
                                        fattr[7:-1] +
                                        ['"' +
                                         fattr[-1] +
                                         '"\n'])
                                    lineOut = lpart + "  " + rpart
                        elif inComponent and not ignore and\
                             code.startswith("\t"):
                            # this is definition code. At this
                            # place we need to _add nonexisting F
                            # attributes_ before we write down
                            # others, as e.g.:
                            # F 4 "NC" H 6775 4400 60  0000 C CNN "Mounted"
                            newattrs = []
                            # default assignment
                            lineOut = code
                            try:
                                # go through all the undefined
                                # attributes:
                                # NOTE THAT THERE ARE (FROM UNKNOWN
                                # REASONS) TWO SPACES BETWEEN WIDTH
                                # AND VISIBILITY ATTRIBUTE. we will
                                # keep it as kicad wants as we want to
                                # see only differences caused by
                                # bomizator, and not due to different formatting
                                for number, (key, val) in\
                                    enumerate(replaceby.items()):
                                    newattrs.append(
                                    'F %d "%s" H %s %s 60  0001 C CNN "%s"'\
                                    % (highestF + 1 + number,
                                       val,
                                       center[0],
                                       center[1],
                                       key))
                                # at the end of loop we need to clear
                                # out the dictionary as all attributes
                                # were defined
                                replaceby = {}
                                # add the original code:
                                lout = '\n'.join(newattrs + [code, ])
                                lineOut = lout
                            except KeyError:
                                # there's nothing in the dictionary
                                # any more, however to be sure we rise
                                # keyerror if there's indeed something
                                if len(replaceby):
                                    raise KeyError(replaceby)

                        wrline.write(lineOut)
            # now we just move the newly created file to the old one
            # and ... pray
            os.rename(schfile+"tmp", schfile)

    def collectFiles(self):
        """ uses project directory to pass through the projects
        """

        # having the project file the top-level schematic shares the
        # filenames, we can recursively search through using simple
        # parsing
        projectFiles = []
        fname = os.path.splitext(self.projectFile)[0]+'.sch'
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
        colors().printInfo("Parsing " + fname)
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

    def _smCatchHeader(self, line):
        """ state machine state catching the component start in the
        line of the code. line is a single line read from the
        schematic file
        """
        if line.startswith("$Comp"):
            self.current_component = {}
            self.current_state = self._smComponentBody

    def _smComponentBody(self, line):
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

    def getNormalisedDesignators(self, designators):
        """ takes set of designators, sorts them and normalises to
        produce a single string identifying all the designators of
        given component
        """
        return ', '.join(sorted(designators, key=QDesignatorComparator()))

    def _attributeTermination(self, line):
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
                # now we compact the information such, that we create
                # dictionary of items and we form list of it
                xm = defaultdict(str)
                # if AR attribute is defined for the component, it
                # takes over the default designator
                try:
                    designators = self.current_component['AR'].keys()
                except KeyError:
                    # otherwise take default component designator
                    designators = [self.current_component['L'][1], ]

                if self.debug:
                    print(self.current_component)
                # designator
                xm[self.header.DESIGNATOR] = set(designators)
                # library reference
                xm[self.header.LIBREF] = self.current_component['L'][0]
                # value
                xm[self.header.VALUE] = self.stripQuote(
                    self.current_component['F']['1'][0])  # value
                # footprint
                xm[self.header.FOOTPRINT] = self.stripQuote(
                    self.current_component['F']['2'][0])  # footprint

                for f_number, f_data in self.current_component['F'].items():
                    if int(f_number) == 3:
                        # datasheet (this is part of schematics)
                        xm[self.header.DATASHEET] = self.stripQuote(f_data[0])
                    elif int(f_number) > 3 and\
                         f_data[-1].find(self.header.SUPPNO) != -1:
                        # supplier reference number
                        xm[self.header.SUPPNO] = self.stripQuote(f_data[0])
                    elif int(f_number) > 3 and\
                         f_data[-1].find(self.header.SUPPLIER) != -1:
                        # supplier name
                        xm[self.header.SUPPLIER] = self.stripQuote(f_data[0])
                    elif int(f_number) > 3 and\
                         f_data[-1].find(self.header.MANUFACTURER) != -1:
                        # supplier name
                        xm[self.header.MANUFACTURER] = self.stripQuote(f_data[0])
                    elif int(f_number) > 3 and\
                         f_data[-1].find(self.header.MFRNO) != -1:
                        # supplier name
                        xm[self.header.MFRNO] = self.stripQuote(f_data[0])

                # before we append this component into selection we
                # might check, whether it is not yet existing. This is
                # done by checking in all previously defined
                # components. This MIGHT happen with multipart
                # devices, which are in schematic treated separately
                if not self.designatorDefined(xm[self.header.DESIGNATOR]):
                    dsg = self.getNormalisedDesignators(xm[self.header.DESIGNATOR])
                    self.components[dsg] = xm
                else:
                    print("Component(s) ", xm[self.header.DESIGNATOR],
                          " already defined. Multipart component?")

            self.current_state = self._smCatchHeader

    def designatorDefined(self, designator):
        """ returns true if none of the designators given is already defined
        """
        # Bit difficult to read, but: the inner map returns vector of
        # true/false for each designator contained in designators of
        # particular component. Any of them will trigger true. Then we
        # pass through entire component space to find if any component
        # claims the designator
        return any(map(lambda com:
                       any(map(lambda desig: desig in com[self.header.DESIGNATOR],
                               designator)),
                       self.components.values()))

    def _attributeGeneric(self, line):
        """ parses 'L' attribute of the component. This type of
        attribute is generic, e.g. L MCP23016 U2, where first value is
        library reference, and we just store all the parameters from
        this one to a list, which we add as dictionary item
        """
        attrs = line.split(" ")
        self.current_component[line[0]] = attrs[1:]

    def _attributeTab(self, line):
        """ tab attribute starts the component body, we keep these
        parameters as they are, just add them into the list
        """
        try:
            self.current_component['X'].append(line)
        except KeyError:
            self.current_component['X'] = []
            self.current_component['X'].append(line)

    def getDesignatorText(self, desig):
        """ input is a set of designators, output is the _textual
        representation_ of the designators, they are concatenated by
        comma and sorted in ascending order
        """


    def _attributeAr(self, line):
        """ AR-type attribute is used in hierarchical design. Its form
        is e.g. following:
AR Path="/55092EEE/56BE633D/56BE9140" Ref="C202"  Part="1"
AR Path="/55092EEE/56C1F5DB/56BE9140" Ref="C219"  Part="1"

        It states, that this particular component is used in two
        sheets identified by their paths and refered as two
        components: C202 and C219. This greatly simplifies parsing of
        the components as we do not need to store the hiearchy and by
        hard way analyse the trees, but it is just enough to collect
        all AR attributes as these were the real components (which in
        fact they are). Note as well, that one of the AR attributes
        will always point to the original designator of firstly
        generated board, hence AR attributes _always_ supercede the L
        attribute, where the original designator is stored. Note that
        there are always multiple ARs, hence we need to store them as
        dictionarys identified _by designator_
        """

        # first make list of a=b parameters
        separate = filter(lambda dat:
                          dat != '',
                          line.replace('"', '').split(" ")[1:])
        # then separate them into dictionary
        args = dict(map(lambda c: c.split('='), separate))
        # get rid of 'Ref' designator from the dictionary as this one
        # is used as key to 'AR' attribute
        dfields = dict(filter(lambda keyval:
                              keyval[0] != 'Ref',
                              args.items()))
        # we try to assign the data, however if we succeed, this
        # is faulty condition as it means, that there was already
        # previous designator of the same name. And designators
        # should be unique
        # first we find if the designator is not by chance already
        # in. If so, WE SHOW IT AS WARNING
        try:
            if args['Ref'] in self.current_component['AR'].keys():
                colors().printFail("Designator " +
                                   args['Ref'] +
                                   """ defined multiple times in the\
 project. CHECK YOUR ANNOTATIONS AS THEY MIGHT BE INCORRECT. KEEPING
THE FIRST DESIGNATOR FOUND""")
            else:
                self.current_component['AR'][args['Ref']] = dfields
        except KeyError:
            # AR attribute for the first time declared
            self.current_component['AR'] = {}
            self.current_component['AR'][args['Ref']] = dfields
        if self.debug and not args['Ref'][0] == '#':
            print("Defined AR attribute as ",
                  self.current_component['AR'])

    def _attributeF(self, line):
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

        the real danger is, when a user defined attribute contains
        spaces (and it can), hence we cannot simply split the data by
        space, but we need to have a look locally between
        quotes. e.g.:
        F 5 "FARNELL" H 5900 5800 60  0001 C CNN "supplier reference"
        is still valid attribute. This split is done by shlex module

        """

        data = shlex.split(line)
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

    def parseComponents(self):
        """ after initial filenames matching this function parses all
        the schematics files and gets the components names from the
        files. These are pulled into the dictionary, which is later on
        used either to get the info about the component, _or_ add/modify
        appropriate attributes.
        """
        for fname in self.matches:
            colors().printInfo("Parsing " +
                               fname)
            with open(fname, "rt") as f:
                # parsing the file for specific tokens of component
                # start/stop is a simple state machine
                for line in f:
                    self.current_state(line)

    def stripQuote(self, text):
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

        # returning each component separately
        for component in self.components:
                yield component

if __name__ == '__main__':
    # test stuff
    a = sch_parser('/home/belohrad/git/beaglebone_relay_multiplexor/beaglebone_relad_kicad')
    a.parseComponents()
