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

import os
import sys
import subprocess

import internal.apportutils

from internal import quicklyutils, packaging
from internal import bzrutils
from quickly import configurationhandler, templatetools
from quickly import launchpadaccess


import gettext
from gettext import gettext as _
# set domain text
gettext.textdomain('quickly')

argv = sys.argv
options = {'bzr': _('quickly configure bzr <bzr-branch-string>'),
          'dependencies': 'quickly configure dependencies',
          'lp-project': _('quickly configure lp-project [project-name]'),
          'ppa': _('quickly configure ppa <ppa-name>'),
          'target-distribution': _('quickly configure target-distribution <ubuntu-release-name>')}

def usage():
    templatetools.print_usage(options.values())
def help():
    print _("""Enable to set or change some parameters of the project, like which
launchpad project should be bound with the current ubuntu application, what
PPA should we use by default to share your package, what additional dependencies
should be added…

Note: If you are specifying a target-distribution apart from the one you are
running, be warned that dependency detection may not be as accurate due to
(rare) discrepancies between distributions.""")
def shell_completion(argv):
    ''' Complete args '''
    # option completion
    rv = []
    if len(argv) == 1:
        rv = options.keys()
    elif len(argv) > 1 and argv[-2] == 'ppa': # if argument following ppa keyname, complete by ppa
        rv = packaging.shell_complete_ppa(argv[-1])
    if rv:
        rv.sort()
        print ' '.join(rv)

templatetools.handle_additional_parameters(sys.argv, help, shell_completion, usage=usage)

if len(argv) < 2:
    help()
    sys.exit (1)

# set the project, skipping the interactive phase if project_name is provided
if argv[1] == "lp-project":
    # connect to LP
    try:
        launchpad = launchpadaccess.initialize_lpi()
    except launchpadaccess.launchpad_connection_error, e:
        print(e)
        sys.exit(1)

    project_name = None
    if len(argv) > 2:
        project_name = argv[2]
    else:
        project_name = quicklyutils.read_input()
    # need to try and get the original project name if it exists.  We'll need this
    # to replace any existing settings
    if not configurationhandler.project_config:
        configurationhandler.loadConfig()
    previous_lp_project_name = configurationhandler.project_config.get('lp_id', None)
    quickly_project_name = configurationhandler.project_config.get('project', None)
    try:
        project = launchpadaccess.link_project(launchpad, "Change your launchpad project:", project_name)
        internal.apportutils.update_apport(quickly_project_name, previous_lp_project_name, project.name)
    except launchpadaccess.launchpad_project_error, e:
        print(e)
        sys.exit(1)
    # get the project now and save the url into setup.py
    project_url  = launchpadaccess.launchpad_url + '/' + project.name
    quicklyutils.set_setup_value('url', project_url)
    about_dialog_file_name = quicklyutils.get_about_file_name()
    if about_dialog_file_name:
        quicklyutils.change_xml_elem(about_dialog_file_name, "object/property",
                                     "name", "website", project_url, {})

# change default ppa
elif argv[1] == "ppa":
    if len(argv) != 3:
        templatetools.print_usage(options['ppa'])
        print _("\nUse shell completion to find all available PPAs")
        sys.exit(4)

    # connect to LP
    try:
        launchpad = launchpadaccess.initialize_lpi()
    except launchpadaccess.launchpad_connection_error, e:
        print(e)
        sys.exit(1)

    ppa_name = argv[2]
    # choose right ppa parameter (users, etc.) ppa or staging
    try:
        (ppa_user, ppa_name, dput_ppa_name, ppa_url) = packaging.choose_ppa(launchpad, ppa_name)
    except packaging.user_team_not_found, e:
        print(_("User or team %s not found on Launchpad") % e)
        sys.exit(1)
    except packaging.not_ppa_owner, e:
        print(_("You have to be a member of %s team to upload to its PPAs") % e)
        sys.exit(1)

    try:
        ppa_name = packaging.check_and_return_ppaname(launchpad, ppa_user, ppa_name) # ppa_name can be ppa name or ppa display name. Find the right one if exists
    except packaging.ppa_not_found, e:
        print(_("%s does not exist. Please create it on launchpad if you want to upload to it. %s has the following PPAs available:") % (e, ppa_user.name))
        for ppa_name, ppa_display_name in packaging.get_all_ppas(launchpad, ppa_user):
            print "%s - %s" % (ppa_name, ppa_display_name)
        sys.exit(1)

    if ppa_user.is_team:
        configurationhandler.project_config['ppa'] = '%s/%s' % (ppa_user.name, ppa_name)
    else:
        configurationhandler.project_config['ppa'] = ppa_name
    configurationhandler.saveConfig()

# change default bzr push branch
elif argv[1] == "bzr":
    if len(argv) != 3:
        templatetools.print_usage(options['bzr'])
        sys.exit(4)
    bzrutils.set_bzrbranch(argv[2])
    configurationhandler.saveConfig()    

# add additional dependencies
elif argv[1] == "dependencies":
    if not configurationhandler.project_config:
        configurationhandler.loadConfig()
    try:
        dependencies = [elem.strip() for elem in configurationhandler.project_config['dependencies'].split(',') if elem]
    except KeyError:
        dependencies = []
    userinput = quicklyutils.read_input('\n'.join(dependencies))
    dependencies = []
    for depends in userinput.split('\n'):
        dependencies.extend([elem.strip() for elem in depends.split(',') if elem])
    configurationhandler.project_config['dependencies'] = ", ".join(dependencies)
    configurationhandler.saveConfig()

# Originally, this was target_distribution, but we changed it to be more consistent with other commands
elif argv[1] == "target-distribution" or argv[1] == "target_distribution":
    if len(argv) != 3:
        templatetools.print_usage(options['target-distribution'])
        sys.exit(4)
    if not configurationhandler.project_config:
        configurationhandler.loadConfig()
    configurationhandler.project_config["target_distribution"] = argv[2]
    configurationhandler.saveConfig()

