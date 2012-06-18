#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

"""Code to add AppIndicator."""

from gi.repository import Gtk # pylint: disable=E0611
from gi.repository import AppIndicator3 # pylint: disable=E0611

from python_name_lib.helpers import get_media_file

import gettext
from gettext import gettext as _
gettext.textdomain('project_name')

class Indicator:
    def __init__(self, window):
        self.indicator = AppIndicator3.Indicator('project_name', '', AppIndicator3.IndicatorCategory.APPLICATION_STATUS)
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)

        icon_uri = get_media_file("project_name.svg")
        icon_path = icon_uri.replace("file:///", '')
        self.indicator.set_icon(icon_path)

        #Uncomment and choose an icon for attention state. 
        #self.indicator.set_attention_icon("ICON-NAME")
        
        self.menu = Gtk.Menu()

        # Add items to Menu and connect signals.
        
        #Adding preferences button 
        #window represents the main Window object of your app
        self.preferences = Gtk.MenuItem("Preferences")
        self.preferences.connect("activate",window.on_mnu_preferences_activate)
        self.preferences.show()
        self.menu.append(self.preferences)

        self.quit = Gtk.MenuItem("Quit")
        self.quit.connect("activate",window.on_mnu_close_activate)
        self.quit.show()
        self.menu.append(self.quit)

        # Add more items here                           

        self.menu.show()
        self.indicator.set_menu(self.menu)
    
def new_application_indicator(window):
    ind = Indicator(window)
    return ind.indicator
