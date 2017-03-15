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
Farnell webpages search engine
"""

import urllib3
try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup
# import headers to be able to match the string names correctly
from BOMizator.headers import headers
from BOMizator.colors import colors
from BOMizator.suppexceptions import NotMatchingHeader, MalformedURL

# FOR THE MOMENT THE FARNELL LOOKUP IS DONE BY PARSING THEIR WEB
# PAGES. AND IT WORKS GREAT. HOWEVER IF THAT FOR SOME CASE FAILS, IT
# SEEMS THAT FARNELL IS VERY WELL ORGANISED AND TRIES TO DO THE BEST
# FOR HIS CUSTOMER, AND CAME WITH AN API, DESCRIBED HERE:
# http://partner.element14.com/docs/Product_Search_API_REST__Description
# SO IF THAT PAGES PARSER FOR SOME REASONS STOPS FUNCTIONING, WE MIGHT
# REIMPLEMENT THE SEARCH ENGINE USING THEIR API. LOVELY! COMPARED TO
# RADIOSPARES WEB PAGES IT IS LIKE A HEAVEN AGAINST HELL


class farnell(object):
    """ defines web search interface for uk.farnell.com.
    """

    def __init__(self):
        self.name = "Farnell"
        self.header = headers()
        self.debug = False

    def getUrl(self, searchtext):
        """ returns URL of farnell, which triggers searching for a
        specific component or name. This is used by back-searching
        from the webpage based e.g. on farnell order code
        """
        return "http://uk.farnell.com/webapp/\
wcs/stores/servlet/Search?st=%s" % (searchtext,)

    def harvestDatasheet(self, urltext):
        """ the urltext is used to fetch the web page content and
        harvest the datasheet link from it. it does not work all the
        time as there are some ambiguities, but works reasonably well
        by parsing simple textual data.
        """
        http = urllib3.PoolManager()
        response = http.request('GET', urltext)
        html = response.data.decode("utf-8")
        # data here, write them to temporary file, just for sake of
        # completeness (and for searching later on why the heck it
        # does not work)
        with open("/tmp/htmlread.html", "wt") as f:
            f.write(html)

        try:
            # this is dependent of web page structure
            parsed_html = BeautifulSoup(html)
            techdoc = parsed_html.body.find('ul',
                                            attrs={'id': 'technicalData'})
            sheet = techdoc.find('a').attrs['href']
        except AttributeError:
            sheet = ''
        return sheet

    def parseURL(self, urltext):
        """ From GIVEN URL (web pages) parses all the data to resolve
        the component. Farnell is relatively easy to do. Here is the
        typical URL, self-explanatory. NOTE THAT ALL OBJECTS ARE
        RETURNED AS QSTRINGS AND NOT ORDINARY PYTHON STRINGS
        (convenience). Fortunately FARNELL is very consistent about it
        (thank you guys), hence it can be used to parse all what we need
        http://uk.farnell.com/multicomp/mj-179ph/socket-low-voltage-12vdc-4a/dp/1737246?ost=MJ-179PH&searchView=table&iscrfnonsku=false

        but one can have a farnell side with resolved language as
        follows:
http:/ch.farnell.com/fr-CH/avx/06033d104kat2a/condensateur-mlcc-x5r-100nf-25v/dp/23325

        hence there's displacement of one item and as we're parsing
        the command line, we want to have both options given
        """

        try:
            # remove doubletrailing first (http://, https://)
            realpart = urltext.split("?")[0].replace("//", "/")
            # from the real part we need to abstract the parameters:
            if self.debug:
                print(realpart)
            try:
                header,\
                    site,\
                    manufacturer,\
                    reference,\
                    description,\
                    deep,\
                    partnum = realpart.split("/")
            except ValueError:
                header,\
                    site,\
                    language,\
                    manufacturer,\
                    reference,\
                    description,\
                    deep,\
                    partnum = realpart.split("/")

            if self.debug:
                print(header,
                      site,
                      manufacturer,
                      reference,
                      description,
                      deep,
                      partnum)
            # series of checks: site has to contain farnell:
            if site.upper().find("FARNELL") == -1:
                raise NotMatchingHeader("No Farnell identifier detected")

            # deep has to contain DP:
            if deep.upper().find("DP") == -1:
                raise NotMatchingHeader("Malformed URL for FARNELL plugin")
            # the most problematic is to dig out the datasheet for the
            # component. This is not part of the URL and for this we need
            # to actually fetch and parse the page. For the moment
            # 'nothing'
            datasheet = self.harvestDatasheet(str(urltext))
            if self.debug:
                print("Datasheet link: ",datasheet)
            # now we convert the data into dictionary:
            datanames = (self.header.MANUFACTURER,
                         self.header.MFRNO,
                         self.header.SUPPLIER,
                         self.header.SUPPNO,
                         self.header.DATASHEET)
            # return properly formed dictionary:(Manufacturer, Mfg. reference,
            # Supplier, Supplier reference, datasheet)
            data = (manufacturer.upper(),
                    reference.upper(),
                    self.name,
                    partnum.upper(),
                    datasheet)
            return dict(zip(datanames, data))

        except ValueError:
            # ValueError is risen when not enouth data to split the
            # header. In this case this is probably not an URL we're
            # looking for, so skipping
            raise MalformedURL("URL not understood")

DEFAULT_CLASS = farnell
