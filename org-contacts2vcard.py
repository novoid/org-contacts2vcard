#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# Time-stamp: <2014-12-07 20:16:40 vk>

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
import base64  ## for encoding to Base64


## debugging:   for setting a breakpoint:
#pdb.set_trace()## FIXXME
#import pdb

PROG_VERSION_NUMBER = u"0.1"
PROG_VERSION_DATE = u"2013-11-20"
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
        logging.warn("Contact did not have a name -> ignoring")
        return False

    if entry['mobile'] == [] and entry['mobile'] == [] and entry['homephone'] == [] and \
            entry['workphone'] == [] and entry['phone'] == [] and entry['email'] == []:
        if not options.omitignores:
            logging.warn("Contact \"%s\" did not have a name single phone number or email address -> ignoring" % entry['name'])
        return False

    return True


def check_phone_number_and_warn_if_necessary(name, number):
    """
    Checks a given phone number string and issues warnings if format
    is not 100% OK.

    @param name: string containing a contact name
    @param number: string containing a phone number
    @param return: nothing
    """

    if number[:2] != '00':
        logging.warning("Contact \"%s\": number \"%s\" does not start with \"00\"." % (name, number))


def parse_org_contact_file(orgfile, include_images):
    """
    Parses the given Org-mode file for contact entries.

    The return format is a follows:
    contacts = [<contact1>, <contact2>, <contact3>, ...]
    with "contact1" like:
    {'name':'First Middle Last', 'mobile':['++43/699/1234567', '0043681987654'], 'homephone':['0316/87654'],
     'workphone':['0399-9876543-42'], 'phone':['001-5489-808908'], 'email':['my-first-address@example.com',
     'my-second-address@example.com'], 'photograph':['/validated/path/to/image/file.jpeg']}

    @param orgfile: file name of a Org-mode file to parse
    @param include_images: boolean is True, when image files should be handled
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

    for rawline in codecs.open(orgfile, 'r', encoding='utf-8'):
        line = rawline.strip()   ## trailing and leading spaces are stupid
        linenr += 1

        #logging.debug("line [%s]" % line)
        #logging.debug("status [%s]" % str(status))

        header_components = re.match(HEADER_REGEX, line)
        if header_components:
            ## in case of new header, make new currententry because previous one was not a contact header with a property
            currententry = {'mobile': [], 'homephone': [], 'workphone': [], 'phone': [], 'email': [], 'photograph': []}
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
                if len(mobile_components.group(1)) > 7:
                    currententry['mobile'].append(mobile_components.group(1))
                    check_phone_number_and_warn_if_necessary(currententry['name'], mobile_components.group(1))
                else:
                    logging.debug("contact \"%s\" has a phone number shorter than 8 -> ignoring" % currententry['name'])
            elif homephone_components:
                currententry['homephone'].append(homephone_components.group(1))
                check_phone_number_and_warn_if_necessary(currententry['name'], homephone_components.group(1))
            elif workphone_components:
                currententry['workphone'].append(workphone_components.group(1))
                check_phone_number_and_warn_if_necessary(currententry['name'], workphone_components.group(1))
            elif phone_components:
                currententry['phone'].append(phone_components.group(1))
                check_phone_number_and_warn_if_necessary(currententry['name'], phone_components.group(1))
            elif email_components:
                currententry['email'].append(email_components.group(1))
            elif photograph_components:
                if include_images:
                    currententry['photograph'].append(photograph_components.group(1))
                else:
                    logging.debug("contact has photograph but include_images is False: [%s]" % currententry['name'])
            elif line == u':END:':
                if check_contact(currententry):
                    contacts.append(currententry)
                    logging.debug("appended contact \"%s\"" % currententry['name'])
                else:
                    logging.debug("contact \"%s\" did not pass the tests -> ignoring" % currententry['name'])
                status = headersearch

            continue

        else:
            ## I must have mixed up status numbers or similar - should never be reached.
            logging.error("Oops. Internal parser error: status \"%s\" unknown. The programmer is an idiot. Current contact entry might get lost due to recovering from that shock. (line number %s)" % (str(status), str(linenr)))
            status = headersearch
            currententry = {}
            continue

    logging.info("found %s suitable contacts while parsing \"%s\"" % (str(len(contacts)), orgfile))
    return contacts


def vcard_header():
    """
    Returns a string containing a generic VCard header.

    @param return: string containing the VCard header
    """

    return u"BEGIN:VCARD\nVERSION:2.1\n"


def vcard_footer():
    """
    Returns a string containing a generic VCard footer.

    @param return: string containing the VCard footer
    """

    return u"END:VCARD\n"


def file_extension_and_base64_of_file(contact, filename):
    """
    Reads the content of the given file and returns its Base64 encoded content.

    @param contact: contact name - for output logging
    @param filename: a file name
    @param return: string of file type according to VCard 2.1 standard format
    @param return: base64 string of file content; None if file not found or error occurred.
    """

    fullname = os.path.join(options.imagefolder, filename)

    if os.path.isfile(fullname):

        tmpfilename, filetype = os.path.splitext(fullname)
        upperfiletype = filetype.upper().replace(".", "")
        if upperfiletype == 'JPG':
            upperfiletype = 'JPEG'
        if upperfiletype not in ['JPEG', 'GIF', 'PNG']:
            ## PNG is not part of VCard 2.1 standard! -> However, it works on Android 4.4
            ## TIFF is part of VCard 2.1 standard! -> However, does not work on Android 4.4
            logging.debug("image file extension \"%s\" not in list of known extensions." % upperfiletype)
            logging.warn("Contact \"%s\": image file \"%s\" has not file type (extension) which is recognized. Skipping it this time." % (contact, fullname))
            return None, None

        with open(fullname, "rb") as image_file:
            return upperfiletype, base64.b64encode(image_file.read())
    else:
        logging.warn("Contact \"%s\": image file \"%s\" could not be found. Skipping it this time." % (contact, fullname))
        return None, None


def insert_into_string_every_X_characters(mystring, x, insertstring):
    """
    After each x characters, insertstring is added to mystring.
    """

    ## if x is less than 0 or interval is longer than input string, return inputstring:
    if x < 1 or x > len(mystring):
        return mystring

    newstring = ''
    number_of_insertions = int(len(mystring)/x)

    for index in range(number_of_insertions):
        position = index*x
        newstring += mystring[position:position+x] + insertstring

    ## add the rest of mystring at the end (if any):
    if len(mystring)%x != 0:
        newstring += mystring[-(len(mystring)%x):] # add remainding string

    return newstring


def generate_vcard_file(contacts, targetfile):
    """
    Generates a VCard file out of the contact information.

    @param contacts: list of dict-entries containing the contact data item lists
    @param return: nothing
    """

    count = 0

    with codecs.open(targetfile, 'wb', encoding = "utf-8") as output:
        for contact in contacts:
            logging.debug("writing contact [%s] ..." % contact['name'])
            output.write(vcard_header())

            output.write(u'FN:' + unicode(contact['name']) + u'\n')

            for mobile in contact['mobile']:
                output.write(u'TEL;CELL:' + mobile + '\n')
            for homephone in contact['homephone']:
                output.write(u'TEL;HOME:' + homephone + '\n')
            for workphone in contact['workphone']:
                output.write(u'TEL;WORK:' + workphone + '\n')
            for phone in contact['phone']:
                output.write(u'TEL:' + phone + '\n')
            for email in contact['email']:
                output.write(u'EMAIL:' + email + '\n')
            if len(contact['photograph']) > 0:
                filetype, base64string = file_extension_and_base64_of_file(contact['name'], contact['photograph'][0])
                if filetype and base64string:
                    truncated_base64string = insert_into_string_every_X_characters(base64string, 74, '\n ')
                    output.write("PHOTO;ENCODING=BASE64;TYPE=" + filetype + ":" + truncated_base64string + '\n\n')
                if len(contact['photograph']) > 1:
                    logging.warn("Contact \"%s\" has more than one photograph. I take only the first one." % contact['name'])
            output.write(vcard_footer())
            count += 1

        return count


if __name__ == "__main__":


    mydescription = u"This script converts Org-mode contacts of a certain format\n" + \
        "to a VCard file which is suitable to be imported to Android 4.4 (and probably\n" + \
        "others as well). Please refer to \n" + \
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

    parser.add_argument("--omitignores", dest="omitignores", action="store_true",
                        help="Omit (only) the ignored contacts due to missing phone number and email.")

    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true",
                        help="Enable verbose mode which is quite chatty - be warned.")

    parser.add_argument("-q", "--quiet", dest="quiet", action="store_true",
                        help="Enable quiet mode: only warnings and errors will be reported.")

    parser.add_argument("--version", dest="version", action="store_true",
                        help="Display version and exit.")

    options = parser.parse_args()

    logging = initialize_logging(options.verbose, options.quiet)

    if options.verbose:

        ## do some unit testing:  (well, I wrote the tests and did not want to delete them :-)
        mystring = "1234567890"
        assert(insert_into_string_every_X_characters(mystring, -1, '.') == mystring)
        assert(insert_into_string_every_X_characters(mystring, 0, '.') == mystring)
        assert(insert_into_string_every_X_characters(mystring, 1, '.') == '1.2.3.4.5.6.7.8.9.0.')
        assert(insert_into_string_every_X_characters(mystring, 2, '.') == '12.34.56.78.90.')
        assert(insert_into_string_every_X_characters(mystring, 3, '.') == '123.456.789.0')
        assert(insert_into_string_every_X_characters(mystring, 4, '.') == '1234.5678.90')
        assert(insert_into_string_every_X_characters(mystring, 5, '.') == '12345.67890.')
        assert(insert_into_string_every_X_characters(mystring, 6, '.') == '123456.7890')
        assert(insert_into_string_every_X_characters(mystring, 7, '.') == '1234567.890')
        assert(insert_into_string_every_X_characters(mystring, 8, '.') == '12345678.90')
        assert(insert_into_string_every_X_characters(mystring, 9, '.') == '123456789.0')
        assert(insert_into_string_every_X_characters(mystring, 10, '.') == mystring+'.')
        assert(insert_into_string_every_X_characters(mystring, 11, '.') == mystring)
        assert(insert_into_string_every_X_characters(mystring, 9999, '.') == mystring)

    try:

        if options.version:
            print os.path.basename(sys.argv[0]) + " version " + PROG_VERSION_NUMBER + \
                " from " + PROG_VERSION_DATE
            sys.exit(0)

        ## checking parameters ...

        if options.verbose and options.quiet:
            logging.error("Options \"--verbose\" and \"--quiet\" found. " +
                          "This does not make any sense, you silly fool :-)")
            error_exit(1)

        if os.path.isfile(options.targetfile):
            logging.critical("Target file \"%s\" is found. Please use other name or remove existing file." %
                             str(options.targetfile))
            error_exit(5)
        else:
            logging.debug("targetfile: [%s]" % options.targetfile)

        if options.imagefolder and not options.imageabbrev:
            logging.critical("You gave me a folder for the contact images but no \"--imageabbrev\" parameter. Bad boy.")
            error_exit(6)
        elif options.imageabbrev and not options.imagefolder:
            logging.critical("You gave me the \"--imageabbrev\" parameter but no folder for the contact images. Bad boy.")
            error_exit(7)
        else:
            logging.debug("imagefolder: [%s]" % options.imagefolder)
            logging.debug("imageabbrev: [%s]" % options.imageabbrev)

        include_images = False
        if options.imagefolder:
            include_images = True

        contacts = parse_org_contact_file(options.orgfile, include_images)

        logging.debug("----- parsing finished; generating VCard file ...")

        count = generate_vcard_file(contacts, options.targetfile)

        logging.info("successfully converted %s contacts to \"%s\"." % (str(count), options.targetfile))

    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

## END OF FILE #################################################################
# Local Variables:
# mode: flyspell
# eval: (ispell-change-dictionary "en_US")
# End:
