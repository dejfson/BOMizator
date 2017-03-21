#!/usr/bin/env python3
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
Entry point for bomizator
"""

import sys
from PyQt5.QtCore import QT_VERSION_STR
from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5 import QtWidgets, QtCore
from sip import SIP_VERSION_STR
from BOMizator.bomizator_app import BOMizator

def main(args=None):
    """The main routine."""
    if args is None:
        args = sys.argv[1:]

    print("ENVIRONMENT INFORMATION:")
    print("Running using python", sys.version)
    print("Qt version:", QT_VERSION_STR)
    print("SIP version:", SIP_VERSION_STR)
    print("PyQt version:", PYQT_VERSION_STR)

    app = QtWidgets.QApplication(sys.argv)
    # general settings file as follows
    QtCore.QCoreApplication.setOrganizationName("dejfson")
    QtCore.QCoreApplication.setOrganizationDomain("github.com/dejfson")
    QtCore.QCoreApplication.setApplicationName("bomizator")
    try:
        project = args[0]
    except IndexError:
        project = ''

    myWindow = BOMizator(project)
    myWindow.show()
    app.exec_()

if __name__ == '__main__':
    main()
