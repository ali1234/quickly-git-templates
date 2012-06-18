# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
### BEGIN LICENSE
# This file is in the public domain
### END LICENSE

import gettext
from gettext import gettext as _
gettext.textdomain('project_name')

import logging
logger = logging.getLogger('python_name')

from python_name_lib.AboutDialog import AboutDialog

# See python_name_lib.AboutDialog.py for more details about how this class works.
class Aboutcamel_case_nameDialog(AboutDialog):
    __gtype_name__ = "Aboutcamel_case_nameDialog"
    
    def finish_initializing(self, builder): # pylint: disable=E1002
        """Set up the about dialog"""
        super(Aboutcamel_case_nameDialog, self).finish_initializing(builder)

        # Code for other initialization actions should be added here.

