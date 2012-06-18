# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
# Copyright 2010 Didier Roche
# Copyright 2010 Tony Byrne
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

option = 'quickly add help-guide <guide-name>'

help_text=_("""adds a help guide to your project.

To edit the guide, run:
$ quickly edit
All the help pages are loaded into your editor as well as the python files.
""")

def add(options):
    if len(argv) != 3:
        templatetools.print_usage(options['help-guide'])
        sys.exit(4)

    try:
        guide_name = templatetools.quickly_name(argv[2])
    except templatetools.bad_project_name, e:
        print(e)
        sys.exit(1)

    abs_template_path = templatetools.get_template_path_from_project()
    abs_command_path = os.path.abspath(os.path.dirname(sys.argv[0]))

    if not configurationhandler.project_config:
        configurationhandler.loadConfig()
    project_name = configurationhandler.project_config['project']

    template_help_dir = os.path.join(abs_template_path,
     'store', 'data', 'mallard')

    # take files from command directory if don't exist
    help_page = os.path.join(template_help_dir,
                               'g_u_i_d_e.page')

    if not os.path.isfile(help_page):
        template_help_dir = os.path.join(abs_command_path,
         'store', 'data', 'mallard')
        help_page = os.path.join(template_help_dir,
                   'g_u_i_d_e.page')

    target_help_dir = os.path.join('help', 'C')
    if not os.path.exists(target_help_dir):
        os.makedirs(target_help_dir)

    python_name = templatetools.python_name(guide_name)
    sentence_name, cc_name = templatetools.conventional_names(guide_name)
    
    substitutions = (
    ('g_u_i_d_e', guide_name),
    ('sentence_name', sentence_name),
    )

    templatetools.file_from_template(template_help_dir, 
                                    'g_u_i_d_e.page', 
                                    target_help_dir, substitutions)
