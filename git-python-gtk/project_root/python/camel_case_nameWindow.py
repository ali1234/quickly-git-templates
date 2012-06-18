# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gettext
from gettext import gettext as _
gettext.textdomain('project_name')

from gi.repository import Gtk # pylint: disable=E0611
import logging
logger = logging.getLogger('python_name')

from python_name_lib import Window
from python_name.Aboutcamel_case_nameDialog import Aboutcamel_case_nameDialog
from python_name.Preferencescamel_case_nameDialog import Preferencescamel_case_nameDialog

# See python_name_lib.Window.py for more details about how this class works
class camel_case_nameWindow(Window):
    __gtype_name__ = "camel_case_nameWindow"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the main window"""
        super(camel_case_nameWindow, self).finish_initializing(builder)

        self.AboutDialog = Aboutcamel_case_nameDialog
        self.PreferencesDialog = Preferencescamel_case_nameDialog

        # Code for other initialization actions should be added here.

