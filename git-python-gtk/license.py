#!/usr/bin/python
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
# Copyright 2009 Didier Roche
#
# This file is part of Quickly ubuntu-application template
#
#This program is free software: you can redistribute it and/or modify it 
#under the terms of the GNU General Public License version 3, as published 
#by the Free Software Foundation.
#
#This program is distributed in the hope that it will be useful, but 
#WITHOUT ANY WARRANTY; without even the implied warranties of 
#MERCHANTABILITY, SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR 
#PURPOSE.  See the GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License along 
#with this program.  If not, see <http://www.gnu.org/licenses/>.

import datetime
import filecmp
import os
import re
import shutil
import sys
import subprocess

from quickly import configurationhandler, templatetools, commands
from internal import quicklyutils

import gettext
from gettext import gettext as _
# set domain text
gettext.textdomain('quickly')

class LicenceError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

BEGIN_LICENCE_TAG = '### BEGIN LICENSE'
END_LICENCE_TAG = '### END LICENSE'


def usage():
    templatetools.print_usage(_('quickly license [license-name]'))
    licenses = get_supported_licenses()
    licenses.sort()
    print _('Candidate licenses: %s') % ', '.join(licenses + ['other'])
def help():
    print _("""Adds license to project files. Before using this command, you should:

1. Edit the file AUTHORS to include your authorship (this step is automatically done
   if you directly launch 'quickly release' or 'quickly share' before changing license)
   In this case, license is GPL-3 by default.
2. If you want to put your own quickly unsupported Licence, add a COPYING file containing
   your own licence and execute $ quickly license other.
3. Executes either 'quickly license' or 'quickly license <License>'
   where <License> can be either:
   - GPL-3 (default)
   - GPL-2
   - other

This will modify the COPYING file with the chosen licence (with GPL-3 by default).
Updating previous chosen Licence if needed.
If you previously removed the tags to add your own licence, it will leave it pristine.
If no name is attributed to the Copyright, it will try to retrieve it from Launchpad
(in 'quickly release' or 'quickly share' command only)

Finally, this will copy the Copyright at the head of every files.

Note that if you don't run 'quickly licence' before calling 'quickly release' or 'quickly share',
this one will execute it for you and guess the copyright holder from your
launchpad account if you didn't update it.""")

def get_supported_licenses():
    """Get supported licenses"""

    available_licenses = []
    
    for license_file in os.listdir(os.path.dirname(__file__) + "/available_licenses"):
        result = re.split("header_(.*)", license_file)
        if len(result) == 3:
            available_licenses.append(result[1])
 
    return available_licenses
    

def copy_license_to_files(license_content):
    """Copy license header to every .py files"""

    # get the project name
    if not configurationhandler.project_config:
        configurationhandler.loadConfig()
    project_name = configurationhandler.project_config['project']

    # open each python file and main bin file
    for root, dirs, files in os.walk('./'):
        for name in files:
            if name.endswith('.py') or os.path.join(root, name) == "./bin/" + project_name:
                skip_until_end_found = False
                try:
                    target_file_name = os.path.join(root, name)
                    ftarget_file_name = file(target_file_name, 'r')
                    ftarget_file_name_out = file(ftarget_file_name.name + '.new', 'w')
                    for line in ftarget_file_name:
                        # seek if we have to add or Replace a License
                        if BEGIN_LICENCE_TAG in line:
                            ftarget_file_name_out.write(line) # write this line, otherwise will be skipped
                            skip_until_end_found = True
                            ftarget_file_name_out.write(license_content)

                        if END_LICENCE_TAG in line:
                            skip_until_end_found = False

                        if not skip_until_end_found:
                            ftarget_file_name_out.write(line)

                    ftarget_file_name.close()
                    ftarget_file_name_out.close()

                    if skip_until_end_found: # that means we didn't find the END_LICENCE_TAG, don't copy the file
                        print _("WARNING: %s was not found in the file %s. No licence replacement") % (END_LICENCE_TAG, ftarget_file_name.name)
                        os.remove(ftarget_file_name_out.name)
                    else:
                        templatetools.apply_file_rights(ftarget_file_name.name, ftarget_file_name_out.name)
                        os.rename(ftarget_file_name_out.name, ftarget_file_name.name)

                except (OSError, IOError), e:
                    msg = _("%s file was not found") % target_file_name
                    raise LicenceError(msg)


def guess_license(flicense):
    """Determines if the user currently has specified a other license"""
    try:
        f = file(flicense)
        contents = f.read()
        if not contents:
            return None
    except:
        return None

    # flicense exists and has content.  So now we check if it is just a copy
    # of any existing license.
    supported_licenses_list = get_supported_licenses()
    for license in supported_licenses_list:
        path = "/usr/share/common-licenses/" + license
        if os.path.isfile(path):
            return_code = subprocess.call(['diff', '-q', flicense, path], stdout=subprocess.PIPE)
            if return_code == 0:
                return license

    return 'other'


def licensing(license=None):
    """Add license or update it to the project files

    Default is GPL-3"""


    fauthors_name = "AUTHORS"
    flicense_name = "COPYING"

    if not configurationhandler.project_config:
        configurationhandler.loadConfig()
    project_name = configurationhandler.project_config['project']
    python_name = templatetools.python_name(project_name)

    # check if we have a license tag in setup.py otherwise, default to GPL-3
    if not license:
        try:
            license = quicklyutils.get_setup_value('license')
        except quicklyutils.cant_deal_with_setup_value:
            pass
    if not license:
        license = guess_license(flicense_name)
        if license == 'other':
            msg = _("COPYING contains an unknown license.  Please run 'quickly license other' to confirm that you want to use a custom license.")
            raise LicenceError(msg)
    if not license:
        license = 'GPL-3'

    supported_licenses_list = get_supported_licenses()
    supported_licenses_list.sort()
    if license not in supported_licenses_list and license != 'other':
        cmd = commands.get_command('license', 'ubuntu-application')
        templatetools.usage_error(_("Unknown licence %s.") % license, cmd=cmd)

    # get Copyright holders in AUTHORS file
    license_content = ""
    try:
        for line in file(fauthors_name, 'r'):
            if "<Your Name> <Your E-mail>" in line:
                # if we have an author in setup.py, grab it
                try:
                    author = quicklyutils.get_setup_value('author')
                    author_email = quicklyutils.get_setup_value('author_email')
                    line = "Copyright (C) %s %s <%s>\n" % (datetime.datetime.now().year, author, author_email)
                    # update AUTHORS file
                    fout = file('%s.new' % fauthors_name, 'w')
                    fout.write(line)
                    fout.flush()
                    fout.close()
                    os.rename(fout.name, fauthors_name)
                except quicklyutils.cant_deal_with_setup_value:
                    msg = _('Copyright is not attributed. ' \
                            'Edit the AUTHORS file to include your name for the copyright replacing ' \
                            '<Your Name> <Your E-mail>. Update it in setup.py or use quickly share/quickly release ' \
                            'to fill it automatically')
                    raise LicenceError(msg)
            license_content += "# %s" % line
    except (OSError, IOError), e:
        msg = _("%s file was not found") % fauthors_name
        raise LicenceError(msg)

    # add header to license_content
    # check that COPYING file is provided if using a personal license
    if license in supported_licenses_list:
        header_file_path = os.path.dirname(__file__) + "/available_licenses/header_" + license
    else:
        header_file_path = flicense_name
    try:
        for line in file(header_file_path, 'r'):
            license_content += "# %s" % line
    except (OSError, IOError), e:
        if header_file_path == flicense_name:
            msg = _("%s file was not found. It is compulsory for user defined license") % flicense_name
        else:
            msg = _("Header of %s license not found. Quickly installation corrupted?") % header_file_path
        raise LicenceError(msg)


    # update license in config.py, setup.py and refresh COPYING if needed
    try:
        config_file = '%s_lib/%sconfig.py' % (python_name, python_name)
        if not os.path.exists(config_file):
            config_file = '%s/%sconfig.py' % (python_name, python_name) # old location
        for line in file(config_file, 'r'):
            fields = line.split(' = ') # Separate variable from value
            if fields[0] == '__license__' and fields[1].strip() != "'%s'" % license:
                fin = file(config_file, 'r')
                fout = file(fin.name + '.new', 'w')
                for line_input in fin:            
                    fields = line_input.split(' = ') # Separate variable from value
                    if fields[0] == '__license__':
                        line_input = "%s = '%s'\n" % (fields[0], license)
                    fout.write(line_input)
                fout.flush()
                fout.close()
                fin.close()
                os.rename(fout.name, fin.name)
                if license in supported_licenses_list:
                    src_license_file = "/usr/share/common-licenses/" + license
                    if os.path.isfile(src_license_file):
                        shutil.copy("/usr/share/common-licenses/" + license, flicense_name)
                break
        try:
            quicklyutils.set_setup_value('license', license)
        except quicklyutils.cant_deal_with_setup_value:
            msg = _("Can't update license in setup.py file\n")
            raise LicenceError(msg)
    except (OSError, IOError), e:
        msg = _("%s file not found.") % (config_file)
        raise LicenceError(msg)

    # update About dialog, if present:
    about_dialog_file_name = quicklyutils.get_about_file_name()
    if about_dialog_file_name:
        copyright_holders = ""
        authors_holders = ""
        # get copyright holders and authors
        for line in file(fauthors_name, 'r'):
            if "copyright" in line.lower() or "(c)" in line.lower(): 
                copyright_holders += line.decode('UTF-8')
                authors_holders += line.decode('UTF-8')
            else:
                authors_holders += line.decode('UTF-8')

        # update without last \n
        quicklyutils.change_xml_elem(about_dialog_file_name, "object/property",
                                     "name", "copyright", copyright_holders[:-1],
                                     {'translatable': 'yes'})
        quicklyutils.change_xml_elem(about_dialog_file_name, "object/property",
                                     "name", "authors", authors_holders[:-1],
                                     {})
        quicklyutils.change_xml_elem(about_dialog_file_name, "object/property",
                                     "name", "license", license_content,
                                     {'translatable': 'yes'})
    copy_license_to_files(license_content)


def shell_completion(argv):
    """Propose available license as the third parameter"""
    
    # if then license argument given, returns available licenses
    if len(argv) == 1:
        rv = get_supported_licenses()
        rv.sort()
        print ' '.join(rv)


if __name__ == "__main__":

    templatetools.handle_additional_parameters(sys.argv, help, shell_completion, usage=usage)
    license = None
    if len(sys.argv) > 2:
        cmd = commands.get_command('license', 'ubuntu-application')
        templatetools.usage_error(_("This command only take one optional argument."), cmd=cmd)
    if len(sys.argv) == 2:
        license = sys.argv[1]
    try:
        licensing(license)
    except LicenceError, error_message:
        print(error_message)
        sys.exit(1)

