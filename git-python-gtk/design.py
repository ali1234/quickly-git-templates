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

import glob
import subprocess
import sys

import gettext
from gettext import gettext as _
# set domain text
gettext.textdomain('quickly')

from quickly import configurationhandler, templatetools

def usage():
    templatetools.print_usage('quickly design')
def help():
    print _("""Opens Glade UI editor so that you can edit the UI for dialogs
and windows in your project. Note that you *must* open Glade
in this manner for quickly to work. If you try to open Glade
directly, and the open the UI files, Glade will throw errors
and won't open the files.""")
templatetools.handle_additional_parameters(sys.argv, help, usage=usage)

if not configurationhandler.project_config:
    configurationhandler.loadConfig()
mainfile = "data/ui/" + templatetools.get_camel_case_name(configurationhandler.project_config['project']).lower() + "window.ui"
files = []
for ui_file in glob.glob("data/ui/*.ui"):
    if ui_file.lower() != mainfile:
        files.insert(0, ui_file)
    else:
        files.append(ui_file)

(project_version, template_version) = templatetools.get_project_and_template_versions("ubuntu-application")
if project_version < '11.12': # GTK+ 3 changeover
    glade_cmd = 'GLADE_CATALOG_PATH=./data/ui glade-gtk2'
else:
    glade_cmd = 'GLADE_CATALOG_SEARCH_PATH=./data/ui glade'

cmd = glade_cmd + " " + " ".join(files)

#run glade with env variables pointing to catalogue xml files
if templatetools.in_verbose_mode():
    subprocess.Popen(cmd, shell=True)
else:
    nullfile=file("/dev/null") 
    subprocess.Popen(cmd, shell=True, stderr=nullfile)
