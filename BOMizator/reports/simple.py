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
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, LongTable
from reportlab.platypus import TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm, mm


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
        # in case:
        # self.doc.pagesize = landscape(A4)

        self.style = TableStyle([
            ('BOX', (0, 0), (-1, 0), 0.5 * mm, colors.black),
            ('LINEBEFORE', (0, 0), (0, -1), 0.25 * mm, colors.black),
            ('LINEAFTER', (-1, 0), (-1, -1), 0.25 * mm, colors.black),
            ('LINEBELOW', (0, -1), (-1, -1), 0.25 * mm, colors.black),
            ('TEXTCOLOR', (0, 0), (1, 1), colors.blue),
            ('SPAN', (0, 0), (-1, 0))
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

        elements = []
        s = getSampleStyleSheet()
        s = s["BodyText"]
        s.wordWrap = 'CJK'
        s.spaceBefore = 50
        s.listAttrs()

        for component in ddata['Farnell']:
            # now we generate data for each row
            toptable = [self.header.MULTIPLYFACTOR,
                        self.header.ADDFACTOR,
                        self.header.TOTAL,
                        self.header.SUPPNO,
                        self.header.VALUE,
                        self.header.LIBREF,
                        self.header.MANUFACTURER]
            header = [Paragraph(cell, s) for cell in toptable]
            P0 = Paragraph('''<link href="''' +
                           component[self.header.DATASHEET] +
                           '''"><b>''' +
                           component[self.header.SUPPNO] +
                           '''</b></link>''',
                           s)
            # we have to do this manually as we want to add link
            total = Paragraph("<b>" + component[self.header.TOTAL] + "</b>", s)
            datarow = [
                Paragraph(component[self.header.MULTIPLYFACTOR], s),
                Paragraph(component[self.header.ADDFACTOR], s),
                total,
                P0,
                Paragraph(component[self.header.VALUE], s),
                Paragraph(component[self.header.LIBREF], s),
                Paragraph(component[self.header.MANUFACTURER], s)]
            P1 = [Paragraph('''<b>Designators: </b>''' +
                            component[self.header.DESIGNATORS], s), ]

            data2 = [P1, header, datarow]
            a4width = [2 * cm,
                       2 * cm,
                       2 * cm,
                       2.5 * cm,
                       2.5 * cm,
                       3.0 * cm,
                       5.0 * cm]
            t = LongTable(data2, colWidths=a4width)
            t.setStyle(self.style)

            elements.append(t)
            # add space after each table
            elements.append(Spacer(1 * cm, 0.5 * cm))
        self.doc.build(elements)



DEFAULT_CLASS = rpt_simple

a = rpt_simple()
