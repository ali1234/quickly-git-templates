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
import webbrowser

from quickly import templatetools, commands
import license

import gettext
from gettext import gettext as _
gettext.textdomain('quickly')

from quickly import configurationhandler
from internal import quicklyutils, packaging
from quickly import launchpadaccess

launchpad = None
ppa_name = None
i = 0
args = []
argv = sys.argv

options = ["--ppa",]

def usage():
    templatetools.print_usage(_('quickly share [--ppa <ppa | group/ppa>]'))
def help():
    print _("""Updates your PPA with the the latest saved project changes.

Before running 'quickly share', you should: create your account 
on http://launchpad.net.
You also have to add a PPA to your launchpad account.

Name, email, and version will be automatically changed in setup.py.

The new version number will be 'CURRENT.VERSION-publicX', where X will
be incremented each time you share.

For example, if you most recently released 10.07.2 and you have shared
the package three times since then, another run of 'quickly share' will
use a new version of 10.07.2-public4.

You can optionally run 'quickly package' and test your package to make
sure it installs as expected.""")
def shell_completion(argv):
    ''' Complete --args '''
    # option completion
    rv = []
    if argv[-1].startswith("-"):
        rv = options
    elif len(argv) > 1 and argv[-2] == '--ppa': # if argument following --ppa, complete by ppa
        rv = packaging.shell_complete_ppa(argv[-1])
    if rv:
        rv.sort()
        print ' '.join(rv)

templatetools.handle_additional_parameters(sys.argv, help, shell_completion, usage=usage)


while i < len(argv):
    arg = argv[i]
    if arg.startswith('-'):
        if arg == '--ppa':
            if i + 1 < len(argv):
                ppa_name = argv[i + 1]
                i += 1
            else:
                cmd = commands.get_command('share', 'ubuntu-application')
                templatetools.usage_error(_("No PPA provided."), cmd=cmd)
        else:
            cmd = commands.get_command('share', 'ubuntu-application')
            templatetools.usage_error(_("Unknown option: %s."  % arg), cmd=cmd)
    else:
        args.append(arg)
    i += 1

# warning: project_name can be different from project.name (one local, one on launchpad)
if not configurationhandler.project_config:
    configurationhandler.loadConfig()
project_name = configurationhandler.project_config['project']

# connect to LP
try:
    launchpad = launchpadaccess.initialize_lpi()
except launchpadaccess.launchpad_connection_error, e:
    print(e)
    sys.exit(1)

# push the gpg key to the env
keyid = ""
try:
    keyid = quicklyutils.get_right_gpg_key_id(launchpad)
except quicklyutils.gpg_error, e:
    print(e)
    sys.exit(1)

# choose right ppa parameter (users, etc.) ppa or staging if ppa_name is None
try:
    (ppa_user, ppa_name, dput_ppa_name, ppa_url) = packaging.choose_ppa(launchpad, ppa_name)
except packaging.user_team_not_found, e:
    print(_("User or Team %s not found on Launchpad") % e)
    sys.exit(1)
except packaging.not_ppa_owner, e:
    print(_("You have to be a member of %s team to upload to its ppas") % e)
    sys.exit(1)

try:
    ppa_name = packaging.check_and_return_ppaname(launchpad, ppa_user, ppa_name) # ppa_name can be ppa name or ppa display name. Find the right one if exists
except packaging.ppa_not_found, e:
    print(_("%s does not exist. Please create it on launchpad if you want to push a package to it. %s has the following ppas available:") % (e, ppa_user.name))
    user_has_ppa = False
    for ppa_name, ppa_display_name in packaging.get_all_ppas(launchpad, ppa_user):
        print "%s - %s" % (ppa_name, ppa_display_name)
        user_has_ppa = True
    if user_has_ppa:
        print(_("You can temporary choose one of them with --ppa switch or definitely by executing 'quickly configure ppa <ppa_name>'."))
    sys.exit(1)

# license if needed (default with author in setup.py and GPL-3). Don't change anything if not needed
try:
    license.licensing()
except license.LicenceError, error_message:
    print(error_message)
    sys.exit(1)

try:
    release_version = packaging.updateversion(sharing=True)
except (packaging.invalid_versionning_scheme,
        packaging.invalid_version_in_setup), error_message:
    print(error_message)
    sys.exit(1)

# creation/update debian packaging
return_code = packaging.updatepackaging()
if return_code != 0:
    print _("ERROR: can't create or update ubuntu package")
    sys.exit(1)

# upload to launchpad
print _("pushing to launchpad")
return_code = packaging.push_to_ppa(dput_ppa_name, "../%s_%s_source.changes" % (project_name, release_version), keyid=keyid) != 0
if return_code != 0:
    sys.exit(return_code)


print _("%s %s is building on Launchpad. Wait for half an hour and have look at %s.") % (project_name, release_version, ppa_url)

sys.exit(0)
