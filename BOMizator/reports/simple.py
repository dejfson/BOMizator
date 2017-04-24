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
Implements simple BOM output to PDF
"""
from BOMizator.bomheaders import bomheaders
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, A3, inch, landscape
from reportlab.platypus import SimpleDocTemplate, LongTable, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm


class rpt_simple(object):
    """ defines web search interface for uk.farnell.com.
    """

    def __init__(self):
        self.name = "Simple PDF reporter"
        self.header = bomheaders()
        self.doc = SimpleDocTemplate(
            "test_report_lab.pdf",
            pagesize=A4,
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20,
            allowSplitting=1,
            title="Bill of Material")
        #self.doc.pagesize = landscape(A4)

        # self.style = TableStyle([('ALIGN',(1,1),(-2,-2),'RIGHT'),
        #                          ('TEXTCOLOR',(1,1),(-2,-2),colors.red),
        #                          ('VALIGN',(0,0),(0,-1),'CENTER'),
        #                          ('TEXTCOLOR',(0,0),(0,-1),colors.blue),
        #                          ('ALIGN',(0,-1),(-1,-1),'CENTER'),
        #                          ('VALIGN',(0,-1),(-1,-1),'CENTER'),
        #                          ('TEXTCOLOR',(0,-1),(-1,-1),colors.green),
        #                          ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
        #                          ('BOX', (0,0), (-1,-1), 0.25, colors.black),
        #])
        self.style = TableStyle([('BOX', (0, -1), (-1, -1), 0.25,
                                  colors.black),
                                 ('TEXTCOLOR', (0, 0), (1, 1), colors.blue),
                                 ('SPAN',(0, -1), (-1, -1))
        ])

    def getListFromSupplier(self, ddata, supplier):
        """ from a given supplier provides a list of data. this is a _generator_
        """
        # browse through all the components
        head = self.header.getHeaders()
        items = map(lambda cmpn:
                   list(map(lambda it: cmpn[it], head)), ddata[supplier])
        for it in items:
            yield it

    def generateBOM(self, ddata):
        """ out of data structure (dictionary) generates BOM using reportlab
        """

        suppdata = list(self.getListFromSupplier(ddata, 'Farnell'))

        elements = []
        s = getSampleStyleSheet()
        s = s["BodyText"]
        s.wordWrap = 'CJK'
        s.spaceBefore = 50
        s.listAttrs()

        for component in ddata['Farnell']:
            # now we generate data for each row
            toptable = ['Multiplier', 'Adder', 'Total', 'Supplier no', 'Value', 'Manufacturer']
            header = [Paragraph(cell, s) for cell in toptable]
            P0 = Paragraph('''<link href="''' +
                           component['Datasheet'] +
                           '''"><b>''' +
                           component['Supplier no'] +
                           '''</b></link>''',
                           styleSheet["BodyText"])
            # we have to do this manually as we want to add link
            total = Paragraph("<b>" + component['Total'] + "</b>", s)
            datarow = [
                Paragraph(component['Multiplier'], s),
                Paragraph(component['Adder'], s),
                total,
                P0,
                Paragraph(component['Value'], s),
                Paragraph(component['Manufacturer'], s)]
            P1 = [Paragraph('''<b>Designators: </b>''' +
                            component['Designators'], s), ]

            data2 = [header, datarow, P1]
            a4width = [2 * cm,
                       2 * cm,
                       2 * cm,
                       2.5 * cm,
                       5.0 * cm,
                       5.0 * cm]
            t=LongTable(data2, colWidths= a4width)
            t.setStyle(self.style)

            elements.append(t)
        self.doc.build(elements)



DEFAULT_CLASS = rpt_simple

a = rpt_simple()
