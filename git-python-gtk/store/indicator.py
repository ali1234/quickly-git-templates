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

import os
import sys
argv = sys.argv

import gettext
from gettext import gettext as _
# set domain text
gettext.textdomain('quickly')

from quickly import configurationhandler, templatetools, commands

option = 'quickly add indicator'

help_text=_("""This will add support for Ubuntu Application Indicator to your quickly project.
Next time you run your app, the Indicator will show up in the panel on top right.
You can add/remove/modify items from the indicator menu by editing indicator.py
""")

def add(options):
    if len(argv) != 2:
        templatetools.print_usage(options['indicator'])
        sys.exit(4)

    abs_template_path = templatetools.get_template_path_from_project()
    abs_command_path = os.path.abspath(os.path.dirname(sys.argv[0]))

    if not configurationhandler.project_config:
        configurationhandler.loadConfig()
    project_name = configurationhandler.project_config['project']

    template_python_dir = os.path.join(abs_template_path, 'store', 'python')
    # take files from command directory if don't exist
    python_file = os.path.join(template_python_dir,
                               'indicator.py')
    python_name = templatetools.python_name(project_name)
    target_python_dir = python_name

    project_sentence_name, project_camel_case_name = \
        templatetools.conventional_names(project_name)

    substitutions = (("project_name",project_name),
                    ( "python_name",python_name))

    templatetools.file_from_template(template_python_dir, 
                                    "indicator.py", 
                                    target_python_dir, 
                                    substitutions)
