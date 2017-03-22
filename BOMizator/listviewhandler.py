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
Logging handler sending the data in full color to listwidget
"""

import logging
from PyQt5 import QtGui, QtWidgets


class ListViewHandler(logging.StreamHandler):
    """
    logging handler pushing everything to listview
    """

    COLORS = {
        'INFO': QtGui.QColor("black"),
        'WARNING': QtGui.QColor("blue"),
        'ERROR': QtGui.QColor("red"),
        'CRITICAL': QtGui.QColor("red")
        }

    def __init__(self, listWidget=None):
        """ takes listwidget as a target to push the data to
        """
        super(ListViewHandler, self).__init__()
        self.listWidget = listWidget

    def emit(self, record):
        try:
            msg = str(self.format(record))
            severity, message = msg.split("-")
            # having message we can push it to the listwidget
            ni = QtWidgets.QListWidgetItem(message)
            ni.setForeground(self.COLORS[severity.strip().upper()])
            self.listWidget.addItem(ni)
            self.listWidget.scrollToItem(ni)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)
