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
from BOMizator.colors import colors
from BOMizator.suppexceptions import NotMatchingHeader, MalformedURL
from BOMizator.headers import headers


class radiospares(object):
    """ defines web search interface for uk.farnell.com.
    """

    def __init__(self):
        self.name = "RS Components"
        self.debug = False
        self.header = headers()

    def getUrl(self, searchtext):
        """ returns URL of farnell, which triggers searching for a
        specific component or name.
        """
        return "http://fr.rs-online.com/web/zr/?searchTerm=%s" % (searchtext)

    def getFastPasteText(self, data):
        """ converts tuple (ordercode, number) into a radiospares
        fast-paste order text, which is a format of
ordercode, number, price center, internal product code
per each ordering code. See
        e.g. http://fr.rs-online.com/web/ca/recapitulatifpanier/
and select ' Copiez et collez votre liste d'articles' to open the
        dialog box with fast entry. We only fill here ordercode and
        number of pieces, all the rest is empty
        """
        return '\n'.join(["%s, %s" % (str(ix[0]),
                                      str(ix[1])) for ix in data])
    def parseURL(self, urltext):
        """ takes the text of the radiospares URL and verifies if it
        is really radiospares. then tries to parse mfg data and
        returns them if all of them are found. If not, raises keyerror
        """
        try:
            # remove doubletrailing first (http://, https://)
            realpart = urltext.split("?")[0].replace("//", "/")
            # from the real part we need to abstract the parameters:
            if self.debug:
                print("REALPART: ", realpart)
            urlparts = list(
                filter(lambda a: a != '', realpart.split("/")))
            if self.debug:
                print(urlparts)
            # series of checks: site has to contain farnell:
            if urlparts[1].upper().find("RS-ONLINE") == -1:
                raise NotMatchingHeader("No RS identifier detected")
            # the last has to be number, as it is a manuf partnum
            try:
                partnum = int(urlparts[-1])
            except ValueError:
                raise NotMatchingHeader(
                    "RS ordering code not identified: %s" % urlparts[-1])

            # now we fetch the webpage and have to parse it for
            # specific components to extract the data we need
            http = urllib3.PoolManager()
            response = http.request('GET', urltext)
            html = response.data.decode("utf-8")

            try:
                # this is dependent of web page structure
                parsed_html = BeautifulSoup(html)
                l1 = parsed_html.body.find('div',
                                           attrs={'class':
                                                  'keyDetailsDivLL'})
                l2 = l1.find('ul',
                             attrs={'class':
                                    'keyDetailsLL'})
                # we're at the level where we can harvest the data
                manufacturer = l2.find('span',
                                       attrs={'itemprop':
                                              'brand'}).contents[0]

                mfgno = l2.find('span',
                                attrs={'itemprop':
                                       'mpn'}).contents[0]
                # now we have to harvest the datasheet as all other
                # information we have
                l3 = parsed_html.body.find('div',
                                           attrs={'class':
                                                  'top10 techRefBlockContainer'})
                l4 = l3.find('div',
                             attrs={'class': 'techRefContainer'})
                l5 = l4.find('div',
                             attrs={'class': 'techRefLink'})
                sheet = l5.find('a').attrs['onclick']

                datasheet = sheet.split("'")[1]
                # now, sheet:
                if self.debug:
                    print(sheet)
                    print(datasheet)

            except AttributeError:
                sheet = ''

            datanames = (self.header.MANUFACTURER,
                         self.header.MFRNO,
                         self.header.SUPPLIER,
                         self.header.SUPPNO,
                         self.header.DATASHEET)
            # return properly formed dictionary:(Manufacturer, Mfg. reference,
            # Supplier, Supplier reference, datasheet)
            data = (manufacturer.upper(),
                    mfgno.upper(),
                    self.name,
                    str(partnum).upper(),
                    datasheet)
            if self.debug:
                print (data)
            return dict(zip(datanames, data))

        except ValueError:
            # ValueError is risen when not enouth data to split the
            # header. In this case this is probably not an URL we're
            # looking for, so skipping
            raise MalformedURL("URL not understood")


DEFAULT_CLASS = radiospares
