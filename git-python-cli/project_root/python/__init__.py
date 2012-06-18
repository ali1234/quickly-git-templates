import logging
import optparse

import gettext
from gettext import gettext as _
gettext.textdomain('project_name')

from python_name import python_nameconfig

LEVELS = (  logging.ERROR,
            logging.WARNING,
            logging.INFO,
            logging.DEBUG,
            )

def main():
    version = python_nameconfig.__version__
    # Support for command line options.
    usage = _("project_name [options]")
    parser = optparse.OptionParser(version="%%prog %s" % version, usage=usage)
    parser.add_option('-d', '--debug', dest='debug_mode', action='store_true',
        help=_('Print the maximum debugging info (implies -vv)'))
    parser.add_option('-v', '--verbose', dest='logging_level', action='count',
        help=_('set error_level output to warning, info, and then debug'))
    # exemple of silly CLI option
    parser.add_option("-f", "--foo", action="store", dest="foo",
                      help=_("foo should be assigned to bar"))
    parser.set_defaults(logging_level=0, foo=None)
    (options, args) = parser.parse_args()

    # set the verbosity
    if options.debug_mode:
        options.logging_level = 3
    logging.basicConfig(level=LEVELS[options.logging_level], format='%(asctime)s %(levelname)s %(message)s')


    # this is the easter egg (:
    if options.foo == 'bar':
        logging.warning(_('easter egg found'))
        print("Schweet")

    # Run your cli application there.
    print _("I'm launched and my args are: %s") % (" ".join(args))
    logging.debug(_('end of prog'))


if __name__ == "__main__":
    main()
