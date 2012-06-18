# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-
# Copyright 2009 Didier Roche
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

import datetime
import re
import subprocess
import sys
import os
from launchpadlib.errors import HTTPError # pylint: disable=E0611


from quickly import configurationhandler
from quickly import launchpadaccess
from internal import quicklyutils
from quickly import templatetools

import gettext
from gettext import gettext as _

#set domain text
gettext.textdomain('quickly')

class ppa_not_found(Exception):
    pass
class not_ppa_owner(Exception):
    pass
class user_team_not_found(Exception):
    pass
class invalid_versionning_scheme(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)
class invalid_version_in_setup(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

class DomainLevel:
    NONE=0
    WARNING=1
    ERROR=2

def _continue_if_errors(err_output, warn_output, return_code,
                       ask_on_warn_or_error):
    """print existing error and warning"""

    if err_output:
        print #finish the current line
        print ('----------------------------------')
        print _('Command returned some ERRORS:')
        print ('----------------------------------')
        print ('\n'.join(err_output))
        print ('----------------------------------')
    if warn_output:
        # seek if not uneeded warning (noise from DistUtilsExtra.auto)
        # line following the warning should be "  …"
        line_number = 0
        for line in warn_output:
            if (re.match(".*not recognized by DistUtilsExtra.auto.*", line)):
                try:
                    if not re.match('  [^ ].*',  warn_output[line_number + 1]):
                        warn_output.remove(line)
                        line_number -= 1
                except IndexError:
                    warn_output.remove(line)
                    line_number -= 1  
            line_number += 1
        # if still something, print it     
        if warn_output:
            if not err_output:
                print #finish the current line
            print _('Command returned some WARNINGS:')
            print ('----------------------------------')
            print ('\n'.join(warn_output))
            print ('----------------------------------')
    if ((err_output or warn_output) and ask_on_warn_or_error
         and return_code == 0):
        if not 'y' in raw_input("Do you want to continue (this is not safe!)? y/[n]: "):
            return(4)
    return return_code

def _filter_out(line, output_domain, err_output, warn_output):
    '''filter output dispatching right domain'''

    if 'ERR' in line:
        output_domain = DomainLevel.ERROR
    elif 'WARN' in line:
        output_domain = DomainLevel.WARNING
    elif not line.startswith('  ') or line.startswith('   dh_'):
        output_domain = DomainLevel.NONE
        if '[not found]' in line:
            output_domain = DomainLevel.WARNING
    if output_domain == DomainLevel.ERROR:
        # only add once an error
        if not line in err_output:
                err_output.append(line)
    elif output_domain == DomainLevel.WARNING:
        # only add once a warning
        if not line in warn_output:
            # filter bad output from dpkg-buildpackage (on stderr) and p-d-e auto
            if not(re.match('  .*\.pot', line)
                   or re.match('  .*\.in', line)
                   or re.match(' dpkg-genchanges  >.*', line)
                   # python-mkdebian warns on help files
                   or re.match('  help/.*/.*', line)
                   # FIXME: this warning is temporary: should be withed in p-d-e
                   or re.match('.*XS-Python-Version and XB-Python-Version.*', line)):
                warn_output.append(line)
    else:
        sys.stdout.write('.')
    return (output_domain, err_output, warn_output)
 

def _exec_and_log_errors(command, ask_on_warn_or_error=False):
    '''exec the giving command and hide output if not in verbose mode'''

    if templatetools.in_verbose_mode():
        return(subprocess.call(command))
    else:
        proc = subprocess.Popen(command, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        stdout_domain = DomainLevel.NONE
        stderr_domain = DomainLevel.NONE
        err_output = []
        warn_output = []
        while True:
            line_stdout = proc.stdout.readline().rstrip()
            line_stderr = proc.stderr.readline().rstrip()
            # filter stderr
            if line_stderr:
                (stderr_domain, err_output, warn_output) = _filter_out(line_stderr, stderr_domain, err_output, warn_output)

            if not line_stdout:
                # don't replace by if proc.poll() as the output can be empty
                if proc.poll() != None:
                    break
            # filter stdout
            else:
                (stdout_domain, err_output, warn_output) = _filter_out(line_stdout, stdout_domain, err_output, warn_output)

        return(_continue_if_errors(err_output, warn_output, proc.returncode,
                                     ask_on_warn_or_error))


# TODO: Vastly simplify this function.  This was implemented post-12.04 to
# make it easier to get an SRU for these fixes.  But the only things here
# that can't be done in-code (either wrapper code or setup.py) is compiling
# the schemas and moving the desktop file.
def update_rules():
    project_name = configurationhandler.project_config['project']

    install_rules = """
override_dh_install:
	dh_install"""

    opt_root = "/opt/extras.ubuntu.com/" + project_name

    # Move script to bin/ folder.
    # There are some complications here.  As of this writing, current versions
    # of python-mkdebian do not correctly install our executable script in a
    # bin/ subdirectory.  Instead, they either install it in the opt-project
    # root or in the opt-project python library folder (depending on whether
    # the project name is the same as its python name).  So if we find that to
    # be the case, we move the script accordingly.
    bin_path = "%(opt_root)s/bin/%(project_name)s" % {
        'opt_root': opt_root, 'project_name': project_name}
    bad_bin_debpath = "debian/%(project_name)s%(opt_root)s/%(project_name)s" % {
        'opt_root': opt_root, 'project_name': project_name}
    python_name = templatetools.python_name(project_name)
    if project_name == python_name:
        bad_bin_debpath += "/" + project_name
    install_rules += """
	mkdir -p debian/%(project_name)s%(opt_root)s/bin
	if [ -x %(bad_bin_debpath)s ]; then mv %(bad_bin_debpath)s debian/%(project_name)s%(opt_root)s/bin; fi""" % {
        'project_name': project_name, 'opt_root': opt_root, 'bad_bin_debpath': bad_bin_debpath}

    # Move desktop file and update it to point to our /opt locations.
    # The file starts, as expected, under /opt.  But the ARB wants and allows
    # us to install it in /usr, so we do.
    old_desktop_debdir = "debian/%(project_name)s%(opt_root)s/share/applications" % {
        'project_name': project_name, 'opt_root': opt_root}
    new_desktop_debdir = "debian/%(project_name)s/usr/share/applications" % {'project_name': project_name}
    new_desktop_debpath = new_desktop_debdir + "/extras-" + project_name + ".desktop"
    install_rules += """
	if [ -f %(old_desktop_debdir)s/%(project_name)s.desktop ]; then \\
		mkdir -p %(new_desktop_debdir)s; \\
		mv %(old_desktop_debdir)s/%(project_name)s.desktop %(new_desktop_debpath)s; \\
		rmdir --ignore-fail-on-non-empty %(old_desktop_debdir)s; \\
		sed -i 's|Exec=.*|Exec=%(bin_path)s|' %(new_desktop_debpath)s; \\
		sed -i 's|Icon=/usr/|Icon=%(opt_root)s/|' %(new_desktop_debpath)s; \\
	fi""" % {
        'bin_path': bin_path, 'old_desktop_debdir': old_desktop_debdir,
        'new_desktop_debdir': new_desktop_debdir, 'project_name': project_name,
        'opt_root': opt_root, 'new_desktop_debpath': new_desktop_debpath}

    # Set gettext's bindtextdomain to point to /opt and use the locale
    # module (gettext's C API) instead of the gettext module (gettext's Python
    # API), so that translations are loaded from /opt
    localedir = os.path.join(opt_root, 'share/locale') 
    install_rules += """
	grep -RlZ 'import gettext' debian/%(project_name)s/* | xargs -0 -r sed -i 's|\(import\) gettext$$|\\1 locale|'
	grep -RlZ 'from gettext import gettext as _' debian/%(project_name)s/* | xargs -0 -r sed -i 's|from gettext \(import gettext as _\)|from locale \\1|'
	grep -RlZ "gettext.textdomain('%(project_name)s')" debian/%(project_name)s/* | xargs -0 -r sed -i "s|gettext\(\.textdomain('%(project_name)s')\)|locale\.bindtextdomain('%(project_name)s', '%(localedir)s')\\nlocale\\1|" """ % {
        'project_name': project_name, 'localedir': localedir}

    # We install a python_nameconfig.py file that contains a pointer to the
    # data directory.  But that will be determined by setup.py, so it will be
    # wrong (python-mkdebian's --prefix command only affects where it moves
    # files during build, but not what it passes to setup.py)
    config_debpath = "debian/%(project_name)s%(opt_root)s/%(python_name)s*/%(python_name)sconfig.py" % {
        'project_name': project_name, 'opt_root': opt_root, 'python_name': python_name}
    install_rules += """
	sed -i "s|__%(python_name)s_data_directory__ =.*|__%(python_name)s_data_directory__ = '%(opt_root)s/share/%(project_name)s/'|" %(config_debpath)s""" % {
        'opt_root': opt_root, 'project_name': project_name,
        'python_name': python_name, 'config_debpath': config_debpath}

    # Adjust XDG_DATA_DIRS so we can find schemas and help files
    install_rules += """
	sed -i 's|        sys.path.insert(0, opt_path)|\\0\\n    os.putenv("XDG_DATA_DIRS", "%%s:%%s" %% ("%(opt_root)s/share/", os.getenv("XDG_DATA_DIRS", "")))|' debian/%(project_name)s%(bin_path)s""" % {
        'opt_root': opt_root, 'project_name': project_name, 'bin_path': bin_path}

    # Compile the glib schema, since it is in a weird place that normal glib
    # triggers won't catch during package install.
    schema_debdir = "debian/%(project_name)s%(opt_root)s/share/glib-2.0/schemas" % {
        'opt_root': opt_root, 'project_name': project_name}
    install_rules += """
	if [ -d %(schema_debdir)s ]; then glib-compile-schemas %(schema_debdir)s; fi""" % {
        'schema_debdir': schema_debdir}

    # Set rules back to include our changes
    rules = ''
    with open('debian/rules', 'r') as f:
        rules = f.read()
    rules += install_rules
    templatetools.set_file_contents('debian/rules', rules)

def get_python_mkdebian_version():
    proc = subprocess.Popen(["python-mkdebian", "--version"], stdout=subprocess.PIPE)
    version = proc.communicate()[0]
    return float(version)

def get_forced_dependencies():
    deps = []

    # check for yelp usage
    if subprocess.call(["grep", "-rq", "['\"]ghelp:", "."]) == 0:
        deps.append("yelp")

    return deps

def updatepackaging(changelog=None, no_changelog=False, installopt=False):
    """create or update a package using python-mkdebian.

    Commit after the first packaging creation"""

    if not changelog:
        changelog = []
    command = ['python-mkdebian']
    version = get_python_mkdebian_version()
    if version >= 2.28:
        command.append('--force-control=full')
    else:
        command.append('--force-control')
    if version > 2.22:
        command.append("--force-copyright")
        command.append("--force-rules")
    if no_changelog:
        command.append("--no-changelog")
    if installopt:
       command.append("--prefix=/opt/extras.ubuntu.com/%s" % configurationhandler.project_config['project'])
    for message in changelog:
        command.extend(["--changelog", message])
    if not configurationhandler.project_config:
        configurationhandler.loadConfig()
    dependencies = get_forced_dependencies()
    try:
        dependencies.extend([elem.strip() for elem
                             in configurationhandler.project_config['dependencies'].split(',')
                             if elem])
    except KeyError:
        pass
    for dep in dependencies:
        command.extend(["--dependency", dep])
    try:
        distribution = configurationhandler.project_config['target_distribution']
        command.extend(["--distribution", distribution])
    except KeyError:
        pass # Distribution has not been set by user, let python-mkdebian decide what it should be


    return_code = _exec_and_log_errors(command, True)
    if return_code != 0:
        print _("An error has occurred when creating debian packaging")
        return(return_code)

    if installopt:
        update_rules()

    print _("Ubuntu packaging created in debian/")

    # check if first python-mkdebian (debian/ creation) to commit it
    # that means debian/ under unknown
    bzr_instance = subprocess.Popen(["bzr", "status"], stdout=subprocess.PIPE)
    bzr_status, err = bzr_instance.communicate()
    if bzr_instance.returncode != 0:
        return(bzr_instance.returncode)

    if re.match('(.|\n)*unknown:\n.*debian/(.|\n)*', bzr_status):
        return_code = filter_exec_command(["bzr", "add"])
        if return_code == 0:
            return_code = filter_exec_command(["bzr", "commit", "-m", 'Creating ubuntu package'])

    return(return_code)


def filter_exec_command(command):
    ''' Build either a source or a binary package'''

    return(_exec_and_log_errors(command, False))


def shell_complete_ppa(ppa_to_complete):
    ''' Complete from available ppas '''

    # connect to LP and get ppa to complete
    try:
        launchpad = launchpadaccess.initialize_lpi(False)
    except launchpadaccess.launchpad_connection_error:
        sys.exit(0)
    available_ppas = []
    if launchpad:
        try:
            (ppa_user, ppa_name) = get_ppa_parameters(launchpad, ppa_to_complete)
        except user_team_not_found:
            pass
        else:
            for current_ppa_name, current_ppa_displayname in get_all_ppas(launchpad, ppa_user):
                # print user/ppa form
                available_ppas.append("%s/%s" % (ppa_user.name, current_ppa_name))
                # if it's the user, print in addition just "ppa_name" syntax
                if ppa_user.name == launchpad.me.name:
                    available_ppas.append(current_ppa_name)
                # if we don't have provided a team, show all teams were we are member off
                if not '/' in ppa_to_complete:
                    team = [mem.team for mem in launchpad.me.memberships_details if mem.status in ("Approved", "Administrator")]
                    for elem in team:
                        available_ppas.append(elem.name + '/')
        return available_ppas

def get_ppa_parameters(launchpad, full_ppa_name):
    ''' Check if we can catch good parameters for specified ppa in form user/ppa or ppa '''

    if '/' in full_ppa_name:
        ppa_user_name = full_ppa_name.split('/')[0]
        ppa_name = full_ppa_name.split('/')[1]
        # check that we are in the team/or that we are the user
        try:
            lp_ppa_user = launchpad.people[ppa_user_name]
            if lp_ppa_user.name == launchpad.me.name:
                ppa_user = launchpad.me
            else:
                # check if we are a member of this team
                team = [mem.team for mem in launchpad.me.memberships_details if mem.status in ("Approved", "Administrator") and mem.team.name == ppa_user_name]
                if team:
                    ppa_user = team[0]
                else:
                    raise not_ppa_owner(ppa_user_name)
        except (KeyError, HTTPError): # launchpadlib may give 404 instead
            raise user_team_not_found(ppa_user_name)
    else:
        ppa_user = launchpad.me
        ppa_name = full_ppa_name
    return(ppa_user, ppa_name)

def choose_ppa(launchpad, ppa_name=None):
    '''Look for right ppa parameters where to push the package'''

    if not ppa_name:
        if not configurationhandler.project_config:
            configurationhandler.loadConfig()
        try:
            (ppa_user, ppa_name) = get_ppa_parameters(launchpad, configurationhandler.project_config['ppa'])
        except KeyError:
            ppa_user = launchpad.me
            if (launchpadaccess.lp_server == "staging"):
                ppa_name = 'staging'
            else: # default ppa
                ppa_name = 'ppa'
    else:
        (ppa_user, ppa_name) = get_ppa_parameters(launchpad, ppa_name)
    ppa_url = '%s/~%s/+archive/%s' % (launchpadaccess.LAUNCHPAD_URL, ppa_user.name, ppa_name)
    dput_ppa_name = 'ppa:%s/%s' % (ppa_user.name, ppa_name)
    return (ppa_user, ppa_name, dput_ppa_name, ppa_url.encode('UTF-8'))

def push_to_ppa(dput_ppa_name, changes_file, keyid=None):
    """ Push some code to a ppa """

    # creating local binary package
    buildcommand = ["dpkg-buildpackage", "-S", "-I.bzr"]
    if keyid:
        buildcommand.append("-k%s" % keyid)
    return_code = filter_exec_command(buildcommand)
    if return_code != 0:
        print _("ERROR: an error occurred during source package creation")
        return(return_code)
    # now, pushing it to launchpad personal ppa (or team later)
    return_code = subprocess.call(["dput", dput_ppa_name, changes_file])
    if return_code != 0:
        print _("ERROR: an error occurred during source upload to launchpad")
        return(return_code)
    return(0)

def get_all_ppas(launchpad, lp_team_or_user):
    """ get all from a team or users

    Return list of tuples (ppa_name, ppa_display_name)"""

    ppa_list = []
    for ppa in lp_team_or_user.ppas:
        ppa_list.append((ppa.name, ppa.displayname))
    return ppa_list

def check_and_return_ppaname(launchpad, lp_team_or_user, ppa_name):
    """ check whether ppa exists using its name or display name for the lp team or user

    return formated ppaname (not display name)"""

    # check that the owner really has this ppa:
    ppa_found = False
    for current_ppa_name, current_ppa_displayname in get_all_ppas(launchpad, lp_team_or_user):
        if current_ppa_name == ppa_name or current_ppa_displayname == ppa_name:
            ppa_found = True
            break
    if not ppa_found:
        raise ppa_not_found('ppa:%s:%s' % (lp_team_or_user.name, ppa_name.encode('UTF-8')))
    return(current_ppa_name)

def updateversion(proposed_version=None, sharing=False):
    '''Update versioning with year.month, handling intermediate release'''

    if proposed_version:
        # check manual versioning is correct
        try:
            for number in proposed_version.split('.'):
                float(number)
        except ValueError:
            msg = _("Release version specified in command arguments is not a " \
                    "valid version scheme like 'x(.y)(.z)'.")
            raise invalid_versionning_scheme(msg)
        new_version = proposed_version
    else:
        # get previous value
        try:
            old_version = quicklyutils.get_setup_value('version')
        except quicklyutils.cant_deal_with_setup_value:
            msg = _("No previous version found in setup.py. Put one please")
            raise invalid_version_in_setup(msg)

        # sharing only add -publicX to last release, no other update, no bumping
        if sharing:
            splitted_release_version = old_version.split("-public")
            if len(splitted_release_version) > 1:
                try:
                    share_version = float(splitted_release_version[1])
                except ValueError:
                    msg = _("Share version specified after -public in "\
                            "setup.py is not a valid number: %s") \
                            % splitted_release_version[1]
                    raise invalid_versionning_scheme(msg)
                new_version = splitted_release_version[0] + '-public' + \
                              str(int(share_version + 1))
            else:
                new_version = old_version + "-public1"

        # automatically version to year.month(.subversion)
        else:
            base_version = datetime.datetime.now().strftime("%y.%m")
            if base_version in old_version:
                try:
                    # try to get a minor version, removing -public if one
                    (year, month, minor_version) = old_version.split('.')
                    minor_version = minor_version.split('-public')[0]
                    try:
                        minor_version = float(minor_version)
                    except ValueError:
                        msg = _("Minor version specified in setup.py is not a " \
                                "valid number: %s. Fix this or specify a " \
                                "version as release command line argument") \
                                % minor_version
                        raise invalid_versionning_scheme(msg)
                    new_version = base_version + '.' + str(int(minor_version + 1))

                except ValueError:
                    # no minor version, bump to first one (be careful,
                    # old_version may contain -publicX)
                    new_version = base_version + '.1'

            else:
                # new year/month
                new_version = base_version

    # write release version to setup.py and update it in aboutdialog
    quicklyutils.set_setup_value('version', new_version)
    about_dialog_file_name = quicklyutils.get_about_file_name()
    if about_dialog_file_name:
        quicklyutils.change_xml_elem(about_dialog_file_name, "object/property",
                                     "name", "version", new_version, {})

    return new_version
