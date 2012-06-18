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
import imp
import os
import sys
from quickly import templatetools, commands

import gettext
from gettext import gettext as _
# set domain text
gettext.textdomain('quickly')

argv = sys.argv

ADDABLE = {}
def get_addable_from_path(_path):
    '''parse addable files'''
    _path = os.path.expanduser(_path)
    globs = glob.glob('%s/*.py' % _path)
    # get only files
    addable_files = [y for y in globs if os.path.isfile(y)]
    # exclude __init__.py
    addable_files = [y for y in addable_files if os.path.basename(y)[0] != '_']
    for _file in addable_files:
        _basename = os.path.splitext(os.path.basename(_file))[0]
        py_mod = imp.load_source(_basename,_file)
        ADDABLE.update(((_basename, py_mod),))

def get_addable():
    parent_path = os.path.dirname(__file__)
    template_path = templatetools.get_template_path_from_project()
    get_addable_from_path(os.path.join(parent_path, 'store'))
    get_addable_from_path(os.path.join(template_path, 'store'))

get_addable()

options = {}
for item in ADDABLE.items():
    try:
        options[item[0]] = item[1].option
    except AttributeError:
        # ignore files in store that have no option for us
        pass

def usage():
    templatetools.print_usage(options.values())

def help():
    help_list = [_('Add something to your project\n')]
    # TODO sort keys
    for module in ADDABLE.values():
        try:
            help_list.append(module.help_text)
        except AttributeError:
            # ignore files in store that have no help for us
            pass
    help_text = '\n\n'.join(help_list)
    print help_text

def shell_completion(argv):
    ''' Complete args '''
    # option completion
    rv = []
    if len(argv) == 1:
        rv = options.keys()
    if rv:
        rv.sort()
        print ' '.join(rv)
templatetools.handle_additional_parameters(sys.argv, help, shell_completion, usage=usage)

if len(sys.argv) < 2:
    cmd = commands.get_command('add', 'ubuntu-application')
    templatetools.usage_error(_("Cannot add, no plugin name provided."), cmd=cmd, template='ubuntu-application')

if argv[1] in ADDABLE.keys():
    ADDABLE[argv[1]].add(options)
else:
    cmd = commands.get_command('add', 'ubuntu-application')
    templatetools.usage_error(_('Cannot add, did not recognize plugin name: %s' % argv[1]), cmd=cmd, template='ubuntu-application')
    sys.exit(4)
