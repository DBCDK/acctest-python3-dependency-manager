#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
import logging

from .common import NullHandler
from .common import die
from .jenkins_project import JenkinsProject
from .dependency_list import DependencyList


logger = logging.getLogger("dbc." + __name__)
logger.addHandler(NullHandler())

def cli():

    from optparse import OptionParser

    usage = "Assert that the specified jobs dependency built within the required time.\nVerifies that the specified dependency of the job is not too old to release"
    parser = OptionParser(usage="%prog [options] master_job master_build dependency maximum-jobage-in-hours\n" + usage)

    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      help="Verbose output.")

    (options, args) = parser.parse_args()

    if len(args) < 4:
        parser.error("need job name and expected age")

    return (options, args[0], int(args[1]), args[2], int(args[3]))


def setup_logger(verbose):
    logging.basicConfig(level=logging.DEBUG,
                        filename='assert_dependency_age.log',
                        filemode='w')
    logger = logging.getLogger('')
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    if verbose:
        ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)


def main():

    DEPENDENCY_FILENAME = 'dependencies.txt'
    JENKINS_SERVER = 'http://is.dbc.dk'
    REPOSITORY_PROJECT = 'opensearch-3rd-party-dependencies'

    (options, master_job, master_build, dependency_name, age) = cli()
    setup_logger(options.verbose)

    max_age = age*3600
    project = JenkinsProject(JENKINS_SERVER, master_job, master_build)
    
    dependencies = DependencyList(JENKINS_SERVER, project, DEPENDENCY_FILENAME, REPOSITORY_PROJECT, recursive=True)

    dependency = dependencies._get_dependency(dependency_name)
    
    logger.debug("Found dependency %s"%dependency)
    
    age = dependency.get_seconds_since_build()
    
    if age > max_age:
        die("Actual age: %s seconds of %s build %s is older than maximum age: %s seconds" % (age, dependency.name, dependency.build_number, max_age))
    else:
        logger.info("Actual age: %s seconds is younger than maximum age: %s seconds" % (age, max_age))

if __name__ == '__main__':
    main()
