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
import webbrowser

from internal import quicklyutils, packaging, launchpad_helper
from internal import bzrutils
from quickly import templatetools, configurationhandler, commands
import license

import logging

from quickly import launchpadaccess

import gettext
from gettext import gettext as _
gettext.textdomain('quickly')

options = ["--ppa",]

def usage():
    templatetools.print_usage(_('quickly submitubuntu [--ppa <ppa | group/ppa>] [release-version] [comments]'))
def help():
    print _("""Posts a release of your project and submit it the ubuntu
application review board so that any users can see and install the
application ont their system.

Before running 'quickly submitubuntu', you should: create your account
and a project page on http://launchpad.net.
You also have to add a PPA to your launchpad account.

Name, email, and version will be automatically changed in setup.py and
bzr will tag the current source with the new version number.

If not specified, the new version number will be 'YEAR.MONTH[.RELEASE]'.

For example, the third release in July 2010 would be versioned 10.07.2.

You may want to make sure that the description and long description in
setup.py are up to date before releasing.

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


launchpad = None
project = None
ppa_name = None
i = 0
args = []
argv = sys.argv

while i < len(argv):
    arg = argv[i]
    if arg.startswith('-'):
        if arg == '--ppa':
            if i + 1 < len(argv):
                ppa_name = argv[i + 1]
                i += 1
            else:
                cmd = commands.get_command('submitubuntu', 'ubuntu-application')
                templatetools.usage_error(_("No PPA provided."), cmd=cmd)
        else:
            cmd = commands.get_command('submitubuntu', 'ubuntu-application')
            templatetools.usage_error(_("Unknown option: %s."  % arg), cmd=cmd)
    else:
        args.append(arg)
    i += 1

    commit_msg = None
if len(args) == 1:
    proposed_version = None
elif len(args) == 2:
    proposed_version = args[1]
elif len(args) > 2:
    proposed_version = args[1]
    commit_msg = " ".join(args[2:])

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

# push the gpg key and email to the env
try:
    keyid = quicklyutils.get_right_gpg_key_id(launchpad)
except quicklyutils.gpg_error, e:
    print(e)
    sys.exit(1)

# get the project now and save the url into setup.py
try:
    project = launchpadaccess.get_project(launchpad)
except launchpadaccess.launchpad_project_error, e:
    print(e)
    sys.exit(1)
project_url  = launchpadaccess.launchpad_url + '/' + project.name
quicklyutils.set_setup_value('url', project_url)
about_dialog_file_name = quicklyutils.get_about_file_name()
if about_dialog_file_name:
    quicklyutils.change_xml_elem(about_dialog_file_name, "object/property",
                                 "name", "website", project_url, {})

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

# update license if needed. Don't change anything if not needed
try:
    license.licensing()
except license.LicenceError, error_message:
    print(error_message)
    sys.exit(1)

try:
    release_version = packaging.updateversion(proposed_version)
except (packaging.invalid_versionning_scheme,
        packaging.invalid_version_in_setup), error_message:
    print(error_message)
    sys.exit(1)

if commit_msg is None:
    commit_msg = _('quickly released: %s' % release_version)


# check if already released with this name
bzr_instance = subprocess.Popen(["bzr", "tags"], stdout=subprocess.PIPE)
bzr_tags, err = bzr_instance.communicate()
if bzr_instance.returncode !=0:
    print(err)
    sys.exit(1)
if release_version in bzr_tags:
    print _("ERROR: quickly can't release: %s seems to be already released. Choose another name.") % release_version
    sys.exit(1)

# commit current changes
packaging.filter_exec_command(["bzr", "add"])
return_code = packaging.filter_exec_command(["bzr", "commit", '--unchanged', '-m',
                                _('commit before release')])
if return_code != 0 and return_code != 3:
    print _("ERROR: quickly can't release as it can't commit with bzr")
    sys.exit(return_code)

# try to get last available version in bzr
previous_version = None
bzr_instance = subprocess.Popen(['bzr', 'tags', '--sort=time'],
                                 stdout=subprocess.PIPE)    
result, err = bzr_instance.communicate()
if bzr_instance.returncode == 0 and result:
    output = result.split('\n') # pylint: disable=E1103
    output.reverse()
    for tag_line in output:
        tag_elem = tag_line.split (' ')
        if not (tag_elem[-1] == '?' or tag_elem[-1] == ''):
            previous_version = tag_elem[0]
            break

changelog = quicklyutils.collect_commit_messages(previous_version)
# creation/update debian packaging
return_code = packaging.updatepackaging(changelog, installopt=True)
if return_code != 0:
    print _("ERROR: can't create or update ubuntu package")
    sys.exit(1)

# add files, setup release version, commit and push !
#TODO: check or fix if we don't have an ssh key (don't tag otherwise to be able to release again)
packaging.filter_exec_command(["bzr", "add"])
return_code = packaging.filter_exec_command(["bzr", "commit", '-m', commit_msg])
if return_code != 0 and return_code != 3:
    print _("ERROR: quickly can't release as it can't commit with bzr")
    sys.exit(return_code)
packaging.filter_exec_command(["bzr", "tag", release_version]) # tag revision

# check if pull branch is set
bzr_instance = subprocess.Popen(["bzr", "info"], stdout=subprocess.PIPE)
bzr_info, err = bzr_instance.communicate()
if bzr_instance.returncode !=0:
    print(err)
    sys.exit(1)


if (launchpadaccess.lp_server == "staging"):
    bzr_staging = "//staging/"
else:
    bzr_staging = ""

custom_location_in_info = None
branch_location = []
custom_location = bzrutils.get_bzrbranch()
if custom_location:
    branch_location = [custom_location]
    custom_location_in_info = custom_location.replace('lp:', '')
# if no branch, create it in ~user_name/project_name/quickly_trunk
# or switch from staging to production
if ("parent branch" in bzr_info) and not (
    (custom_location_in_info and custom_location_in_info not in bzr_info) or
   ((".staging." in bzr_info) and not bzr_staging) or
   (not (".staging." in bzr_info) and bzr_staging)):
    return_code = packaging.filter_exec_command(["bzr", "pull"])
    if return_code != 0:
        print _("ERROR: quickly can't release: can't pull from launchpad.")
        sys.exit(return_code)

    return_code = packaging.filter_exec_command(["bzr", "push"])
    if return_code != 0:
        print _("ERROR: quickly can't release: can't push to launchpad.")
        sys.exit(return_code)
else:
    if not branch_location:
        branch_location = ['lp:', bzr_staging, '~', launchpad.me.name, '/', project.name, '/quickly_trunk']
    return_code = packaging.filter_exec_command(["bzr", "push", "--remember", "--overwrite", "".join(branch_location)])
    if return_code != 0:
        print _("ERROR: quickly can't release: can't push to launchpad.")
        sys.exit(return_code)

    # make first pull too
    return_code = packaging.filter_exec_command(["bzr", "pull", "--remember", "".join(branch_location)])
    if return_code != 0:
        print _("ERROR: quickly can't release correctly: can't pull from launchpad.")
        sys.exit(return_code)


# upload to launchpad
print _("pushing to launchpad")
return_code = packaging.push_to_ppa(dput_ppa_name, "../%s_%s_source.changes" % (project_name, release_version), keyid=keyid) != 0
if return_code != 0:
    sys.exit(return_code)

#create new release_date
launchpad_helper.push_tarball_to_launchpad(project, release_version,
                                    "../%s_%s.tar.gz" % (project_name,
                                    release_version), changelog)

print _("%s %s released and submitted to ubuntu. Wait for half an hour and have look at %s.") % (project_name, release_version, ppa_url)
print _("Then your application will be reviewed by the application review board.")

# as launchpad-open doesn't support staging server, put an url
if launchpadaccess.lp_server == "staging":
    webbrowser.open(launchpadaccess.LAUNCHPAD_CODE_STAGING_URL + '/' + project.name)
else:
    webbrowser.open(launchpadaccess.LAUNCHPAD_URL + '/' + project.name)
