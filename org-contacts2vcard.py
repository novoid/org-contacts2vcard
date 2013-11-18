#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Time-stamp: <2013-11-18 17:24:42 vk>

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
import re  ## regex library
import codecs  ## Unicode file handling

## debugging:   for setting a breakpoint:
#pdb.set_trace()## FIXXME
import pdb

PROG_VERSION_NUMBER = u"0.1beta"
PROG_VERSION_DATE = u"2013-11-17"
INVOCATION_TIME = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


EPILOG = u"\n\
:copyright: (c) 2013 by Karl Voit <tools@Karl-Voit.at>\n\
:license: GPL v3 or any later version\n\
:URL: https://github.com/novoid/org-contacts2vcard\n\
:bugreports: via github or <tools@Karl-Voit.at>\n\
:version: " + PROG_VERSION_NUMBER + " from " + PROG_VERSION_DATE + "\n"

LOGGINGID = "org-contacts2vcard"

logger = logging.getLogger(LOGGINGID)

HEADER_REGEX = re.compile('^(\*+)\s+(.*?)(\s+(:\S+:)+)?$')
PHONE = '\s+([\+\d\-/ ]{7,})$'
EMAIL = '([a-zA-Z0-9._%-+]+@[a-zA-Z0-9._%-]+.[a-zA-Z]{2,6})'
MOBILE_REGEX = re.compile(':MOBILE:' + PHONE)
HOMEPHONE_REGEX = re.compile(':HOMEPHONE:' + PHONE)
WORKPHONE_REGEX = re.compile(':WORKPHONE:' + PHONE)
PHONE_REGEX = re.compile(':PHONE:' + PHONE)
EMAIL_REGEX = re.compile(':EMAIL:\s+' + EMAIL)
PHOTOGRAPH_REGEX = re.compile(':PHOTOGRAPH: \[\[photo:(.+)\]\]')


def initialize_logging(verbose, quiet):
    """Log handling and configuration"""

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

    logger.debug("exiting with error code %s" % str(errorcode))
    sys.stdout.flush()
    sys.exit(errorcode)


def check_contact(entry):
    """
    Checks the current entry dict and returns true if it meets all criteria.

    @param return: True if it is OK. False if not.
    """

    if not entry:
        logging.error("No entry found -> check failed")
        return False

    if entry['name'] == "":
        logging.warn("Entry did not have a name -> ignoring")
        return False

    if entry['mobile'] == [] and entry['mobile'] == [] and entry['homephone'] == [] and \
            entry['workphone'] == [] and entry['phone'] == [] and entry['email'] == []:
        logging.warn("Entry \"%s\" did not have a name single phone number or email address -> ignoring" % entry['name'])
        return False

    return True


def parse_org_contact_file():
    """
    Parses the given Org-mode file for contact entries.

    The return format is a follows:
    contacts = [<contact1>, <contact2>, <contact3>, ...]
    with "contact1" like:
    {'name':'First Middle Last', 'mobile':['++43/699/1234567', '0043681987654'], 'homephone':['0316/87654'],
     'workphone':['0399-9876543-42'], 'phone':['001-5489-808908'], 'email':['my-first-address@example.com', 
     'my-second-address@example.com'], 'photograph':['/validated/path/to/image/file.jpeg']}

    @param return: list of dict-entries containing the contact data item lists
    """

    linenr = 0

    ## defining distinct parsing status states:
    headersearch = 21
    propertysearch = 42
    inproperty = 73
    status = headersearch
    
    contacts = []
    currententry = {}

    for rawline in codecs.open(options.orgfile, 'r', encoding='utf-8'):
        line = rawline.strip()   ## trailing and leading spaces are stupid
        linenr += 1

        #logging.debug("line [%s]" % line)
        #logging.debug("status [%s]" % str(status))

        header_components = re.match(HEADER_REGEX, line)
        if header_components:
            ## in case of new header, make new currententry because previous one was not a contact header with a property
            currententry = {'mobile':[], 'homephone':[], 'workphone':[], 'phone':[], 'email':[], 'photograph':[]}
            currententry['name'] = header_components.group(2)
            status = propertysearch
            continue

        if status == headersearch:
            ## if there is something to do, it was done above when a new heading is found
            continue

        if status == propertysearch:
            if line == u':PROPERTIES:':
                status = inproperty
            continue

        elif status == inproperty:

            mobile_components = re.match(MOBILE_REGEX, line)
            homephone_components = re.match(HOMEPHONE_REGEX, line)
            workphone_components = re.match(WORKPHONE_REGEX, line)
            phone_components = re.match(PHONE_REGEX, line)
            email_components = re.match(EMAIL_REGEX, line)
            photograph_components = re.match(PHOTOGRAPH_REGEX, line)

            if mobile_components:
                currententry['mobile'].append(mobile_components.group(1))
            elif homephone_components:
                currententry['homephone'].append(homephone_components.group(1))
            elif workphone_components:
                currententry['workphone'].append(workphone_components.group(1))
            elif phone_components:
                currententry['phone'].append(phone_components.group(1))
            elif email_components:
                currententry['email'].append(email_components.group(1))
            elif photograph_components:
                currententry['photograph'].append(photograph_components.group(1))
                #pdb.set_trace()## FIXXME
            elif line == u':END:':
                if check_contact(currententry):
                    contacts.append(currententry)
                    logging.debug("appended contact \"%s\"" % currententry['name'])
                else:
                    logging.debug("contact \"%s\" did not pass the tests -> ignoring" % currententry['name'])
                status = headersearch
                #pdb.set_trace()## FIXXME

            continue


        else:
            ## I must have mixed up status numbers or similar - should never be reached.
            logging.error("Oops. Internal parser error: status \"%s\" unknown. The programmer is an idiot. Current contact entry might get lost due to recovering from that shock. (line number %s)" % (str(status), str(linenr)))
            status = headersearch
            currententry = {}
            continue

    logging.info("found %s suitable contacts while parsing \"%s\"" % (str(len(contacts)), options.orgfile))
    return contacts


if __name__ == "__main__":

    mydescription = u"FIXXME. Please refer to \n" + \
        "https://github.com/novoid/org-contacts2vcard for more information."

    parser = argparse.ArgumentParser(prog=sys.argv[0],
                                     formatter_class=argparse.RawDescriptionHelpFormatter,  ## keep line breaks in EPILOG and such
                                     epilog=EPILOG,
                                     description=mydescription)

    parser.add_argument("--orgfile", dest="orgfile", metavar='ORGFILE', required=True,
                        help="One Org-mode file which contains all contact information.")

    parser.add_argument("--targetfile", dest="targetfile", metavar='OUTFILE', required=True,
                        help="Path where the output file will be written to.")

    parser.add_argument("--imagefolder", dest="imagefolder", metavar='DIR', required=False,
                        help="Path where the contact image files are located.")

    parser.add_argument("--imageabbrev", dest="imageabbrev", metavar='NAME', required=False,
                        help="The name of you custom link which defines contact images (e.g., \"photo\").")

    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="Enable verbose mode which is quite chatty - be warned.")

    parser.add_argument("-q", "--quiet", dest="quiet", action="store_true",
                        help="Enable quiet mode: only warnings and errors will be reported.")

    parser.add_argument("--version", dest="version", action="store_true",
                        help="Display version and exit.")

    options = parser.parse_args()

    logging = initialize_logging(options.verbose, options.quiet)

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

        if os.path.isfile(options.targetfile):
            logging.critical("Target file \"\" is found. Please use other name or remove existing file." % 
                             options.outfile)
            error_exit(5)
        else:
            logging.debug("targetfile: [%s]" % options.targetfile)

        if options.imagefolder and not options.imageabbrev:
            logging.critical("You gave me a folder for the contact images but no \"--imageabbrev\" parameter. Bad boy.")
            error_exit(6)
        else:
            logging.debug("imagefolder: [%s]" % options.imagefolder)
            logging.debug("imageabbrev: [%s]" % options.imageabbrev)


        contacts = parse_org_contact_file()
        
        ## FIXXME: write vcard file here

        logging.debug("successfully finished.")

    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

## END OF FILE #################################################################
# Local Variables:
# mode: flyspell
# eval: (ispell-change-dictionary "en_US")
# End:
