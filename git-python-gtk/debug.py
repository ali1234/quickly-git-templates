#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
# Copyright 2010 Travis B. Hartwell
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


import os
import stat
import sys
import subprocess

import gettext
from gettext import gettext as _
gettext.textdomain('quickly')

from quickly import configurationhandler
from quickly import templatetools

def usage():
    templatetools.print_usage(_('quickly debug -- [program arguments]'))
def help():
    print _("""Debugs your application with winpdb.

$ quickly debug -- values -<whatever>
to pass '-whatever' and 'values' to the executed program. Without that
if you use for instance --help, it would be Quickly help and not your
program one.""")
templatetools.handle_additional_parameters(sys.argv, help, usage=usage)

# if config not already loaded
if not configurationhandler.project_config:
    configurationhandler.loadConfig()

# check if we can execute a graphical project
if not templatetools.is_X_display():
    print _("Can't access to X server, so can't run winpdb")
    sys.exit(1)

project_bin = 'bin/' + configurationhandler.project_config['project']
command_line = ["winpdb", project_bin]
command_line.extend([arg for arg in sys.argv[1:] if arg != "--"])

# run with args if bin/project exist
st = os.stat(project_bin)
mode = st[stat.ST_MODE]
if mode & stat.S_IEXEC:
    nullfile = file("/dev/null")
    subprocess.Popen(" ".join(command_line), shell=True, stderr=nullfile)
else:
    print _("Can't execute winpdb")
    sys.exit(1)
