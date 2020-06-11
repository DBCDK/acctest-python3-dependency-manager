#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
:mod:`dependency_manager.repository_project` -- Wrapper for a repository project
================================================================================

==================
Repository Project
==================

Contains class used to wrap a repository project.

The class contains method to handle 3rd party repository artifacts,
and contains methods so it is compatible with the Jenkins_project
class.
"""
import os
import urllib.request, urllib.parse, urllib.error
import urllib.parse
import logging

from .common import die
from .common import NullHandler

# define logger
logger = logging.getLogger("dbc." + __name__)
logger.addHandler(NullHandler())


class JenkinsRepositoryProject(object):
    """ Wrapper class for repository project
    """
    def __init__(self, jenkins_url, artifact, repository_project, build_number=None):
        """ Initializes repository project

            :param jenkins_url: url of the jenkins server hosting project
            :param artifact: Name of the repository project
            :param repository_project
            :param build_number: build number of the project. If not specified,
                                 build number of last successful build is used.
        """
        self.name = artifact

        self.repository = repository_project
        self.url = jenkins_url
        if not self.url.endswith('/'):
            self.url += '/'

        self.info = self._get_project_info()

        self.build_number = build_number
        if not build_number:
            self.build_number = self.get_last_successful_build()

        artifacts = self._get_repository_artifacts()
        if not self.name in artifacts:
            die("Could not find repository artifact '%s' in repository '%s',\navailable artifacts %s" % (self.name, self.repository, str(list(artifacts.keys()))))

        self.artifacts = {}
        for type, value in artifacts[self.name].items():
            self.artifacts[value[0]] = value[1]

    def get_last_successful_build(self):
        """ Retrieves the last successful build for this project
            :return: The last successful build number
        """
        return int(self.info['lastSuccessfulBuild']['number'])

    def get_artifacts(self):
        """ Retrieves artifact list for project

           :return: list of tuples with two elements: artifactname, and download url
        """
        return self.artifacts

    def get_upstreams(self):
        """ returns upstreams for repository, which always an empty list (for compatibility with JenkinsProject)"""
        return []

    def get_scm_info(self):
        """ returns version management info for repository (for compatibility with JenkinsProject)"""
        return [(self.repository, "NA")]

    def get_dependency_file_content(self, dependency_file_name='dependencies.txt'):
        """ return dependency file content, which is always None (for compatibility with JenkinsProject)"""
        return None

    def _get_repository_artifacts(self):
        """ Retrieves artifact list for repository
        """
        build = self._get_build()
        return self._parse_artifacts(build['artifacts'])

    def _get_project_info(self, depth=1):
        """ retrieves information for repository"""
        logger.debug("Getting info for repository_artifact %s" % self.name)
        params = {'depth': depth}
        query_url = urllib.parse.urljoin(self.url, "job/%s/api/python?%s" %
                                     (self.repository, urllib.parse.urlencode(params)))
        return self._get_and_evaluate_url(query_url)

    def _get_and_evaluate_url(self, url):
        """ retrieve and evaluate url with eval"""
        logger.debug("Querying with url '%s'" % url)
        content = urllib.request.urlopen(url).read()
        try:
            return eval(content)
        except:
            die("Couldn't evaluate content from url '%s' (response '%s')" % (url, content))

    def _parse_artifacts(self, artifacts):
        """ Parses repository artifacts
        """
        base_url = urllib.parse.urljoin(self.url, "job/%s/%s/artifact/" % (self.repository, self.build_number))
        artifact_urls = dict()
        for artifact in artifacts:
            name = os.path.basename(os.path.dirname(artifact['relativePath']))
            if not name in artifact_urls:
                artifact_urls[name] = []
            artifact_urls[name].append((artifact['fileName'], base_url + artifact['relativePath']))

        artifact_dict = {}
        for artifact, content in artifact_urls.items():

            artifact_dict[artifact] = {}
            for filename, url in content:
                if filename.endswith('.md5'):
                    artifact_dict[artifact]['md5'] = (filename, url)
                else:
                    artifact_dict[artifact]['artifact'] = (filename, url)

        return artifact_dict

    def _get_build(self):
        """ retrieves build information from project"""
        build = [x for x in self.info['builds'] if x['number'] == self.build_number]

        if len(build) == 0:
            die("Build number %s is not a valid build-number for project %s. Valid build numbers are %s" %
                (self.build_number, self.repository, sorted([x['number'] for x in self.info['builds']])))

        return build[0]
    
    def __eq__(self, other):
        """ Equals operator for JenkinsRepositoryProject class"""
        if self.name == other.name:
            return True
        return False
