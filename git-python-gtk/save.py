#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
# Copyright 2009 Didier Roche
#
# This file is part of Quickly ubuntu-application template
#
#This program is free software: you can redistribute it and/or modify it 
#under the terms of the GNU General Public License version 3, as published 
#by the Free Software Foundation.

#This program is distributed in the hope that it will be useful, but 
#WITHOUT ANY WARRANTY; without even the implied warranties of 
#MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
#PURPOSE.  See the GNU General Public License for more details.

#You should have received a copy of the GNU General Public License along 
#with this program.  If not, see <http://www.gnu.org/licenses/>.


import sys
import subprocess

import gettext
from gettext import gettext as _
gettext.textdomain('quickly')

from quickly import templatetools

def usage():
    templatetools.print_usage(_('quickly save [comments]'))
def help():
    print _("""This command commits all changes since the last save to bzr. Note that 
it does not push changes to any back up location. If you need revert
or otherwise use the revision control, use bzr directly:
$ bzr help""")
templatetools.handle_additional_parameters(sys.argv, help, usage=usage)

#set either a default message or the specified message
commit_msg = " ".join(sys.argv[1:])
if commit_msg == "":
   commit_msg = _('quickly saved')

#save away
subprocess.call(["bzr", "add"])
return_code = subprocess.call(["bzr", "commit", "-m" + commit_msg])
if return_code == 3:
    print _("It seems that you have no change to record.")

sys.exit(return_code)

