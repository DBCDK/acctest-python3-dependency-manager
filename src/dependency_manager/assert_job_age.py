#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
import logging

from .common import NullHandler
from .common import die
from .jenkins_project import JenkinsProject


logger = logging.getLogger("dbc." + __name__)
logger.addHandler(NullHandler())

def cli():

    from optparse import OptionParser

    usage = "Assert that the specified job is build stable within the required time.\nVerifies that the specified job is not too old"
    parser = OptionParser(usage="%prog [options] job_name maximum-jobage-in-hours\n" + usage)

    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      help="Verbose output.")

    (options, args) = parser.parse_args()

    if len(args) < 2:
        parser.error("need job name and expected age")

    return (options, args[0], int(args[1]))


def setup_logger(verbose):
    logging.basicConfig(level=logging.DEBUG,
                        filename='assert_job_age.log',
                        filemode='w')
    logger = logging.getLogger('')
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    if verbose:
        ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)


def main():

    JENKINS_SERVER = 'http://is.dbc.dk'

    (options, job_name, age) = cli()
    setup_logger(options.verbose)

    max_age = age*3600
    proj = JenkinsProject(JENKINS_SERVER, job_name)

    age = proj.get_seconds_since_build()
    
    if age > max_age:
        die("Actual age: %s seconds is older than maximum age: %s seconds" % (age, max_age))
    else:
        logger.info("Actual age: %s seconds is younger than maximum age: %s seconds" % (age, max_age))

if __name__ == '__main__':
    main()
