#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2013-11-04 18:12:23 vk>

## TODO:
## * fix parts marked with «FIXXME»

## ===================================================================== ##
##  You might not want to modify anything below this line if you do not  ##
##  know, what you are doing :-)                                         ##
## ===================================================================== ##

import os
import logging
import datetime
import sys
import argparse  ## command line arguments

## debugging:   for setting a breakpoint:
#pdb.set_trace()## FIXXME
import pdb

PROG_VERSION_NUMBER = u"0.1"
PROG_VERSION_DATE = u"2013-11-04"
INVOCATION_TIME = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

EPILOG = u"\n\
:copyright: (c) 2013 by Karl Voit <tools@Karl-Voit.at>\n\
:license: GPL v3 or any later version\n\
:URL: https://github.com/novoid/org-contacts2vcard\n\
:bugreports: via github or <tools@Karl-Voit.at>\n\
:version: " + PROG_VERSION_NUMBER + " from " + PROG_VERSION_DATE + "\n"


def initialize_logging(identifier, verbose, quiet):
    """Log handling and configuration"""

    logger = logging.getLogger(identifier)

    # create console handler and set level to debug
    ch = logging.StreamHandler()

    FORMAT = None
    if verbose:
        FORMAT = "%(levelname)-8s %(asctime)-15s %(message)s"
        ch.setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
    elif quiet:
        FORMAT = "%(levelname)-8s %(message)s"
        ch.setLevel(logging.ERROR)
        logger.setLevel(logging.ERROR)
    else:
        FORMAT = "%(levelname)-8s %(message)s"
        ch.setLevel(logging.INFO)
        logger.setLevel(logging.INFO)

    # create formatter
    formatter = logging.Formatter(FORMAT)

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)

    ## omit double output (default handler and my own handler):
    logger.propagate = False

    ## # "application" code
    ## logger.debug("debug message")
    ## logger.info("info message")
    ## logger.warn("warn message")
    ## logger.error("error message")
    ## logger.critical("critical message")

    logger.debug("logging initialized")

    return logger


def error_exit(errorcode):
    """
    Exits with return value of errorcode and prints to stderr.

    @param errorcode: integer that will be reported as return value.
    """

    logger = logging.getLogger('org-contacts2vcard')
    logger.debug("exiting with error code %s" % str(errorcode))

    sys.stdout.flush()
    sys.exit(errorcode)



if __name__ == "__main__":

    mydescription = u"FIXXME. Please refer to \n" + \
        "https://github.com/novoid/org-contacts2vcard for more information."

    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     formatter_class=argparse.RawDescriptionHelpFormatter,  ## keep line breaks in EPILOG and such
                                     epilog=EPILOG,
                                     description=mydescription)

    parser.add_argument("--orgfile", dest="orgfile", nargs='+', metavar='ORGFILE', required=True,
                        help="One Org-mode file which contains all contact information.")

    parser.add_argument("--targetfile", dest="targetfile", metavar='OUTFILE', required=True,
                        help="Path where the output file will be written to.")

    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="Enable verbose mode which is quite chatty - be warned.")

    parser.add_argument("-q", "--quiet", dest="quiet", action="store_true",
                        help="Enable quiet mode: only warnings and errors will be reported.")

    parser.add_argument("--version", dest="version", action="store_true",
                        help="Display version and exit.")

    options = parser.parse_args()

    logging = initialize_logging("org-contacts2vcard", options.verbose, options.quiet)

    try:

        if options.version:
            print os.path.basename(sys.argv[0]) + " version " + PROG_VERSION_NUMBER + \
                " from " + PROG_VERSION_DATE
            sys.exit(0)

        ## checking parameters ...


        if options.verbose and options.quiet:
            logging.error("Options \"--verbose\" and \"--quiet\" found. " +
                          "This does not make any sense, you silly fool :-)")
            Utils.error_exit(1)





#        with open(options.logfilename, 'a') as outputhandle:
#            outputhandle.write(u"## -*- coding: utf-8 -*-\n" +
#                               "## This file is best viewed with GNU Emacs Org-mode: http://orgmode.org/\n" +
#                               "* Warnings and Error messages from lazyblorg     :lazyblorg:log:\n\n" +
#                               "Messages gets appended to this file. Please remove fixed issues manually.\n")
#            outputhandle.flush()



        #if not os.path.isfile(options.targetfile):

        if os.path.isfile(options.targetfile):
            logging.critical("Target file \"\" is found. Please use other name or remove existing file." % options.outfile)
            error_exit(5)
        else:
            logging.debug("targetfile: [%s]" % options.targetfile)



        logging.debug("successfully finished.")

    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

## END OF FILE #################################################################
# Local Variables:
# mode: flyspell
# eval: (ispell-change-dictionary "en_US")
# End:
