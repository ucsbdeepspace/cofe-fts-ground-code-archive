#!/usr/bin/env/python
#
# This script will run the groundstation code.
#

import GUI
from GUI.FileDialogs import request_old_directory
from GUI.Files import DirRef
import os
import sys

import fitsmanager
import groundgui

class GroundstationApplication( GUI.Application ):
    def open_app( self ):
        folder = request_old_directory().path
        manager = fitsmanager.FitsManager( folder )
        dcw = groundgui.DataControlWindow(manager)
        dcw.show()
        groundgui.DataViewWindow(manager).show()
        pcw = groundgui.PlotControlWindow(manager)
        pcw.show()
        dcw.set_plotwindow(pcw)

GroundstationApplication().run()
