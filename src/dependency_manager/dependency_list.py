#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
:mod:`dependency_manager.dependency_list` -- list structure containing dependencies
===================================================================================

==============
Depedency List
==============

Class uses to contain and build dependencies for the dependency manager.

The constructor can be called with the recursive argument set to
True, the main projects upstream projects are examined for
dependency files, and the contents of these files are added to
the created dependency file. If a dependency mismatch is detected
during creation a DependencyException is raised. The class also
contains a add_depedency method that allows to build/add
dependencies 'by hand'.
"""
import logging
import re
from datetime import datetime

from .jenkins_project import JenkinsProject
from .repository_project import JenkinsRepositoryProject
from .common import die
from .common import NullHandler
from .common import DependencyException

# define logger
logger = logging.getLogger("dbc." + __name__)
logger.addHandler(NullHandler())


def pad(string, size, pad_char=" ", direction='left'):
    """ Padding function

        :param string: The string to pad
        :param size: length of padded string
        :param pad_char: character to pad string with, default is ' '
        :param direction: padding direction. default is 'left'

        :return: padded string
    """
    padding = pad_char * (size - len(string))

    if direction == 'left':
        return padding + string
    return string + padding


class DependencyList(object):
    """ Dependencylist for jenkins projects
    """
    def __init__(self, jenkins_server, jenkins_project, dependency_filename, repository_project, jenkins_credentials=None, recursive=True):
        """ Initializes dependency list

            :param jenkins_server: url of the jenkins server hosting projects
            :param jenkins_project: The master project for dependency list
            :param depedency_filename: Name of the dependency file to check
                                       upstream projects for.
            :param repository_project: Name of the jenkins repository project
            :param recursive: if True the upstream projects for specified
                              jenkins_projects are examined for dependency files
                              and these are incorperated into the dependency list.
                              Default is True.
        """
        self.jenkins_server = jenkins_server
        self.master_project = jenkins_project
        self.jenkins_credentials = jenkins_credentials
        self.dependency_filename = dependency_filename
        self.repository_project = repository_project
        #TODO: Support GIT
        self.scm_info = self.master_project.get_scm_info()

        self.dependencies = []
        self.recursive = recursive

        if self.recursive:
            self._add_upstream_dependencies()

    def add_dependency(self, jenkins_project, added_by=None):
        """ adds project to dependency list.

            :param jenkins_project: The project to add to dependency list
            :param added_by: The project adding this dependency.
                             If None the master project for this list is used
        """
        if self.dependencies and jenkins_project in [x[0] for x in self.dependencies]:
            self._check_for_dependency_mismatch(jenkins_project)

        else:
            self.dependencies.append((jenkins_project, added_by))

    def tostring(self):
        """ Returns string representation of dependency list

            :return: string representation of dependency list
        """
        string = self._create_head_string() + "\n"
        for dependency in self.dependencies:
            string += self._create_dependency_string(*dependency) + "\n"
        return string

    def tofile(self, filename):
        """ Writes dependency  list to file
        """
        with open(filename, 'w') as fh:
            fh.write(self.tostring())

    def get_dependency(self, name):
        """ Retrieves project with name from internal list of dependencies
        """
        return self._get_dependency(name)

    def _check_for_dependency_mismatch(self, jenkins_project):
        """ Checks for dependency mismatch between supplied jenkins_project and already present project"""
        project = self._get_dependency(jenkins_project.name)

        if project.build_number == jenkins_project.build_number:
            logger.debug('project %s already present, with same build-number' % jenkins_project.name)
        else:
            die('project %s already present, with different build-number (new build-number %s, present build-number %s)' %
                (jenkins_project.name, jenkins_project.build_number, project.build_number), error_class=DependencyException)

    def _add_upstream_dependencies(self):
        """ Adds upstream projects and their dependencies to local dependency list
        """
        upstream_projects = []

        if 'upstreamProjects' in self.master_project.info:
            for upstream_name in self.master_project.get_upstreams():

                upstream_project = JenkinsProject(self.jenkins_server, upstream_name, jenkins_credentials=self.jenkins_credentials )
                upstream_projects.append(upstream_project)
                self.add_dependency(upstream_project, None)

        for upstream_dependency_content in [x.get_dependency_file_content(self.dependency_filename) for x in upstream_projects]:

            if upstream_dependency_content:
                main_project, projects = parse_dependency_string(self.jenkins_server, upstream_dependency_content, self.repository_project, jenkins_credentials=self.jenkins_credentials)
                for project in [main_project] + projects:
                    self.add_dependency(*project)

    def _get_dependency(self, name):
        """ Retrieves project with name from internal list of dependencies
        """
        project = None
        for dependency in [x[0] for x in self.dependencies]:
            if dependency.name == name:
                project = dependency
                break
        return project

    def _create_dependency_string(self, project, added_by):
        """ Creates dependency string for project entry"""
        if not added_by:
            added_by = self.master_project.name
        #TODO: Support GIT
        scm_info = project.get_scm_info()

        dependency_string = "%s\n" % project.name
        dependency_string += "   Added by: %s\n" % added_by
        dependency_string += "   Build: %s\n" % project.build_number

        svn_strings = []
        if scm_info:
            info_len = max([len(x[0]) for x in scm_info])
            svn_strings = ["%s     (rev: %s)" % (pad(x[0], info_len, direction='right'), x[1]) for x in scm_info]
            dependency_string += "   SVN/GIT: %s" % svn_strings[0]
            svn_strings = svn_strings[1:]

        for svn_project in svn_strings:
            dependency_string += "\n        %s" % svn_project

        return dependency_string.strip()

    def _create_head_string(self):
        """ creates dependency string for master project """
        creation_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        info_len = 0
        svn_strings = []
        if self.scm_info:
            info_len = max([len(x[0]) for x in self.scm_info])
            svn_strings = ["%s     (rev: %s)" % (pad(x[0], info_len, direction='right'), x[1]) for x in self.scm_info]

        head = "\n".join(["### File created: %s" % creation_date,
                          "### Project: %s" % self.master_project.name,
                          "### Build: %s" % self.master_project.build_number])

        if self.scm_info:
            head += "\n### SVN: %s" % svn_strings[0]
            svn_strings = svn_strings[1:]

        for svn_project in svn_strings:
            head += "\n###      %s" % svn_project

        head += "\n"
        return head

    def __str__(self):
        return self.tostring()


def parse_dependency_string(jenkins_url, dependency_string, repository_project, jenkins_credentials=None):
    """ Parses depedency string as outputtet by the DependencyList class.

        :param jenkins_url: The jenkins server containing the projects
        :param dependency_string: The dependency string to parse
        :param repository_project: The name of the jenkins project
               used as repository for 3rd party artifacts
        :return: Tuple where first entry is the master project,
                 and the second is a list of dependent projects.
    """

    projects = []
    project = []

    main_project = _create_main_project(dependency_string, jenkins_url, jenkins_credentials=jenkins_credentials)

    for line in [x for x in dependency_string.split('\n') if x != ""]:
        if not line.startswith('#'):

            if not line.startswith(' '):

                if project:
                    projects.append(_add_jenkins_project(project, jenkins_url, repository_project, jenkins_credentials=jenkins_credentials))
                project = []
                project.append(line.strip())

            else:
                project.append(line.strip())

    if project:
        projects.append(_add_jenkins_project(project, jenkins_url, repository_project, jenkins_credentials=jenkins_credentials))

    return main_project, projects


def _create_main_project(dependency_string, jenkins_url, jenkins_credentials=None):
    main_project_regex = "^### Project: (.+)$"
    build_regex = "^### Build: (.+)$"

    main_project_name = re.search(main_project_regex, dependency_string, re.M).group(1)
    main_build = int(re.search(build_regex, dependency_string, re.M).group(1))

    return (JenkinsProject(jenkins_url, main_project_name, jenkins_credentials=jenkins_credentials, build_number=main_build), None)


def _add_jenkins_project(project, jenkins_url, repository_project, jenkins_credentials=None):

    name = project[0]
    added_by = project[1].replace("Added by: ", "")
    build_number = int(project[2].replace("Build: ", ""))

    svn = None
    if len(project) > 3:
        svn = project[3].replace('(SVN|SVN/GIT): ', '').split()[1]

    if svn != repository_project:
        return (JenkinsProject(jenkins_url, name, jenkins_credentials=jenkins_credentials, build_number=build_number), added_by)
    else:
        return(JenkinsRepositoryProject(jenkins_url, name, repository_project, build_number=build_number), added_by)
