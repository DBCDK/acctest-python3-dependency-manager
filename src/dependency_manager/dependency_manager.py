#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
:mod:`dependency_manager.dependency_manager` -- main class for dependency-manager project
=========================================================================================

==================
Dependency Manager
==================

Project designed to control and collect dependencies between
jenkins projects.

When calling the dependency-manager in a jenkins project a
'dependencies.txt' file is created containing the specific builds
build-number and svn revision is created. If upstream projects
are present, Their dependency file are examined and their content
is added to the local depedendency file. If a build number
mismatch is detected between common dependencies the current
build is aborted.
"""
import logging
import os
import re
import urllib.request, urllib.parse, urllib.error

from .dependency_list import DependencyList
from .dependency_list import parse_dependency_string
from .jenkins_project import JenkinsProject
from .repository_project import JenkinsRepositoryProject
from .common import DependencyException
from .common import NullHandler

# define logger
logger = logging.getLogger("dbc." + __name__)
logger.addHandler(NullHandler())


def download_artifacts(target_folder, pattern, dependency_filename, jenkins_server, repository_project, jenkins_credentials=None):
    """ Download artifacts from projects specified in the
        local dependency filename

        :param target_folder: Folder to place downloaded artifacts in
        :param pattern: Regular expression to filter artifacts to download
        :param dependency_filename: name of dependency file
        :param jenkins_server: The url of the jenkins server
        :param repository_project: Name of repository project
    """
    logger.info('Downloading artifacts')
    logger.debug('Using pattern %s' % pattern)
    target_artifacts = []
    
    with open(dependency_filename) as fh:
        content = fh.read()
        main_project, dependencies = parse_dependency_string(jenkins_server, content, repository_project, jenkins_credentials=jenkins_credentials)

        for project, added_by in [main_project] + dependencies:

            for key, value in project.get_artifacts().items():

                if not key == dependency_filename and re.match(pattern, key):
                    target_artifacts.append((key, value))

    if target_artifacts and not os.path.exists(target_folder):
        os.mkdir(target_folder)

    for name, url in target_artifacts:
        logger.debug("downloading '%s' from '%s'" % (name, url))
        urllib.request.urlretrieve(url, os.path.join(target_folder, name))


def add_project_or_artifact(project_or_artifact, project_type, dependency_filename, jenkins_server, repository_project, jenkins_credentials=None):
    """ Add projectrepository artifact to local dependency file.

        :param project: Adds non upstream project to dependency file.
        :param dependency_filename: name of dependency file
        :param jenkins_server: The url of the jenkins server
        :param repository_project: Name of repository project
    """
    logger.info("adding %s '%s' to %s" % (project_type, project_or_artifact, dependency_filename))
    dependency_list = None

    with open(dependency_filename) as fh:
        content = fh.read()

        main_project, dependencies = parse_dependency_string(jenkins_server, content, repository_project, jenkins_credentials=jenkins_credentials)

        dependency_list = DependencyList(jenkins_server, main_project[0], dependency_filename, repository_project, jenkins_credentials=jenkins_credentials, recursive=False)
        for dependency in dependencies:
            dependency_list.add_dependency(*dependency)

        project = _create_project(project_or_artifact, project_type, jenkins_server, repository_project, jenkins_credentials=jenkins_credentials)
        dependency_list.add_dependency(project, added_by=main_project[0].name)

        upstream_dependency_content = project.get_dependency_file_content(dependency_filename)
        if upstream_dependency_content:
            main_project, projects = parse_dependency_string(jenkins_server, upstream_dependency_content, repository_project, jenkins_credentials=jenkins_credentials)
            for project in [main_project] + projects:
                dependency_list.add_dependency(*project)
    dependency_list.tofile(dependency_filename)


def _create_project(project_or_artifact, project_type, jenkins_server, repository_project,jenkins_credentials=None):

    if project_type == 'project':
        logger.debug("Creating project")
        return JenkinsProject(jenkins_server, project_or_artifact, jenkins_credentials=jenkins_credentials)

    logger.debug("Creating repository project")
    return JenkinsRepositoryProject(jenkins_server, project_or_artifact, repository_project)


def build_dependency_file(job_name, build_number, dependency_filename, jenkins_server, repository_project, jenkins_credentials=None):
    """ Builds dependency file.

        :param job_name: name of master project to build dependency file for
        :param build_number: Build number of master project
        :param dependency_filename: name of dependency file
        :param jenkins_server: The url of the jenkins server
    """
    logger.info("Building dependency file for project %s-%s" % (job_name, build_number))
    project = JenkinsProject(jenkins_server, job_name, build_number, jenkins_credentials)
    try:

        dependency_list = DependencyList(jenkins_server, project, dependency_filename, repository_project, jenkins_credentials=jenkins_credentials)
        dependency_list.tofile(dependency_filename)
        logger.info("Dependency file '%s' created" % dependency_filename)
        return dependency_list
    except DependencyException as e:
        logger.warning("Aborting build %s-%s, dependency mismatch detected" % (job_name, build_number))
        project.abort_build()
        raise e


def cli():
    """ Commandline interface for dependency_manager
    """
    from optparse import OptionParser

    usage = "Adds dependent project artifacts to dependency file for master_project, if not already present. Can also download dependencies found in file."
    parser = OptionParser(usage="%prog [options] master_project master_build jenkins_user jenkins_pass" + usage)

    parser.add_option("-r", "--repository", type="string", action="store", dest="repository", default=None,
                      help="Add repository artifact to dependencies found in local dependency-file")

    parser.add_option("-a", "--add-project", type="string", action="store", dest="add_project", default=None,
                      help="Add project to  local dependency-file")

    parser.add_option("-d", "--download", type="string", action="store", dest="download_folder", default=None,
                      help="download project artifacts from dependency-file to specified folder")

    parser.add_option("-p", "--pattern", type="string", action="store", dest="pattern", default=None,
                      help="If this option is used (only applicable with the download options), only artifacts that match this regex are downloaded.")

    parser.add_option("-c", "--credentials", type="string", action="store", dest="jenkins_credentials", default=None,
                      help="Jenkins credentials. Ex.: 'someuser:somepass'")


    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      help="Verbose output.")

    (options, args) = parser.parse_args()

    if options.repository and options.download_folder:
        parser.error("cannot add repository artifact and download at the same time.")

    if options.add_project and options.download_folder:
        parser.error("cannot add project and download at the same time.")

    if not options.download_folder and options.pattern:
        parser.error("--pattern option is only applicable if using download")

    if not (options.repository or options.add_project or options.download_folder) and len(args) < 2:
        parser.error("Need master-project and master-build-number to do anything")

    if not (options.repository or options.add_project or options.download_folder):
        try:
            args[1] = int(args[1])
        except ValueError:
            parser.error("master-build-number must be an integer")

    return (options, args)


def setup_logger(verbose):
    logging.basicConfig(level=logging.DEBUG,
                        filename='dependency_manager.log',
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

    (options, args) = cli()
    setup_logger(options.verbose)

    if options.download_folder:

        pattern = ".*"
        if options.pattern:
            pattern = options.pattern

        download_artifacts(options.download_folder, pattern, DEPENDENCY_FILENAME, JENKINS_SERVER, REPOSITORY_PROJECT, jenkins_credentials=options.jenkins_credentials)

    elif options.repository:
        add_project_or_artifact(options.repository, 'repository artifact', DEPENDENCY_FILENAME, JENKINS_SERVER, REPOSITORY_PROJECT, jenkins_credentials=options.jenkins_credentials)

    elif options.add_project:
        add_project_or_artifact(options.add_project, 'project', DEPENDENCY_FILENAME, JENKINS_SERVER, REPOSITORY_PROJECT, jenkins_credentials=options.jenkins_credentials)

    else:
        job_name = args[0]
        build_number = args[1]

        build_dependency_file(job_name, build_number, DEPENDENCY_FILENAME, JENKINS_SERVER, REPOSITORY_PROJECT, jenkins_credentials=options.jenkins_credentials)

if __name__ == '__main__':
    main()
