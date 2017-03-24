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
Mouser webpages search engine
"""

import urllib3
try:
    from BeautifulSoup import BeautifulSoup
except ImportError:
    from bs4 import BeautifulSoup
# import headers to be able to match the string names correctly
from BOMizator.headers import headers
from BOMizator.suppexceptions import NotMatchingHeader, MalformedURL

# FOR THE MOMENT THE FARNELL LOOKUP IS DONE BY PARSING THEIR WEB
# PAGES. AND IT WORKS GREAT. HOWEVER IF THAT FOR SOME CASE FAILS, IT
# SEEMS THAT FARNELL IS VERY WELL ORGANISED AND TRIES TO DO THE BEST
# FOR HIS CUSTOMER, AND CAME WITH AN API, DESCRIBED HERE:
# http://partner.element14.com/docs/Product_Search_API_REST__Description
# SO IF THAT PAGES PARSER FOR SOME REASONS STOPS FUNCTIONING, WE MIGHT
# REIMPLEMENT THE SEARCH ENGINE USING THEIR API. LOVELY! COMPARED TO
# RADIOSPARES WEB PAGES IT IS LIKE A HEAVEN AGAINST HELL


class mouser(object):
    """ defines web search interface for uk.farnell.com.
    """

    def __init__(self):
        self.name = "Mouser"
        self.header = headers()
        self.debug = False

    def getUrl(self, searchtext):
        """ returns URL of farnell, which triggers searching for a
        specific component or name. This is used by back-searching
        from the webpage based e.g. on farnell order code
        """
        raise ValueError("NOT IMPLEMENTED")
#         return "http://uk.farnell.com/webapp/\
# wcs/stores/servlet/Search?st=%s" % (searchtext,)

#     def getFastPasteText(self, data):
#         """ converts tuple (ordercode, number) into a farnell
#         fast-paste order text, which is a format of
# ordercode, number, comment (empty)
# per each ordering code. See e.g. 'quick paste' at uk.farnell.com
#         """
#         return '\n'.join(["%s, %s" % (str(ix[0]),
#                                       str(ix[1])) for ix in data])

    def parseURL(self, urltext):
        """ the urltext is used to fetch the web page content and
        harvest the datasheet link from it. it does not work all the
        time as there are some ambiguities, but works reasonably well
        by parsing simple textual data.
        """

        if urltext.upper().find("MOUSER.COM") == -1:
            raise NotMatchingHeader("No Mouse identifier detected")
        # manufacturer and manunumber if free of charge as it is in
        # the header, we use bs to parse the web pages
        # this is dependent of web page structure
        user_agent = {'user-agent': 'Mozilla/5.0 (Windows NT 6.3;\
rv:36.0) Gecko/20100101 Firefox/36.0'}
        # we need to use user_agent as mouser is obsfucated, using
        # user agent should 'assure' that we can get web page and not
        # being identified as crawler (which is not the case, right :)
        http = urllib3.PoolManager(2, headers=user_agent)
        response = http.request('GET', urltext)
        html = response.data.decode("utf-8")
        parsed_html = BeautifulSoup(html)
        l1 = parsed_html.body.find('div',
                                   attrs={'class':
                                          'product-info'})
        suppno = l1.find('div',
                         attrs={'id':
                                'divMouserPartNum'}).contents[0].strip()
        manufnoitem = l1.find('div',
                              attrs={'id':
                                     'divManufacturerPartNum'}).find('h1')
        manufno = manufnoitem.contents[0].strip()
        manufacturer = l1.find('span',
                               attrs={'itemprop':
                                      'name'}).contents[0].strip()

        # datasheet is clumsy
        datasheet = l1.find('a',
                            attrs={'id':
                                   "ctl00_ContentMain_rptrCatalogDataSheet_ctl00_lnkCatalogDataSheet",
                                   'target':
                                   "_blank"}).attrs['href'].strip()

        datanames = (self.header.MANUFACTURER,
                     self.header.MFRNO,
                     self.header.SUPPLIER,
                     self.header.SUPPNO,
                     self.header.DATASHEET)
        data = (manufacturer.upper(),
                manufno.upper(),
                self.name,
                suppno.upper(),
                datasheet)
        return dict(zip(datanames, data))

        # except ValueError:
        #     # ValueError is risen when not enouth data to split the
        #     # header. In this case this is probably not an URL we're
        #     # looking for, so skipping
        #     raise MalformedURL("URL not understood")

DEFAULT_CLASS = mouser


if __name__ == '__main__':
    a = mouser()
    urltext = 'http://eu.mouser.com/ProductDetail/AVX/FE37M6C0206KB\
/?qs=%2fha2pyFadug2Q1cOiFJf0Z9LKjcrra%2fRJ4i9GyUbonHQeR5nMYnV%252bA%3d%3d&\
utm_source=octopart&utm_medium=aggregator&utm_campaign=581-FE37M6C0206KB&utm_content=AVX'
    print(a.parseURL(urltext))