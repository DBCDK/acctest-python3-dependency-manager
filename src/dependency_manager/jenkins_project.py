#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
:mod:`dependency_manager.jenkins_project` -- Wrapper for a jenkins project
==========================================================================

===============
Jenkins Project
===============

Contains class used to wrap a jenkins project.

The class contains method to et artifact urls, upstream projects,
last successful build number and other common project functions.
"""
import requests
from requests.auth import HTTPBasicAuth

import logging
import os
import netrc
from lxml import etree

from .common import die
from .common import NullHandler
from datetime import datetime
from . import jenkins_authentication

# define logger
logger = logging.getLogger("dbc." + __name__)
logger.addHandler(NullHandler())


class JenkinsProject(object):
    """ Wrapper class for jenkins project
    """
    def __init__(self, jenkins_url, project_name, build_number=None, jenkins_credentials=None):
        """ Initializes Jenkins project

            :param jenkins_url: url of the jenkins server hosting project
            :param project_name: Name of the jenkins project
            :param build_number: build number of the project. If not specified,
                                 build number of last successful build is used.
        """
        self.url = jenkins_url
        if not self.url.endswith('/'):
            self.url += '/'

        self.name = project_name
        self.jenkins_credentials = jenkins_credentials

        self.build_number = build_number

        self.info = self._get_project_info()

        if not self.build_number:
            self.build_number = self.get_last_stable_build()

        logger.debug("name %s, build-number %s" % (self.name, self.build_number))

        self.config = etree.fromstring(self._get_project_config())

    def get_last_successful_build(self):
        """ Retrieves the last successful build number for this project
            :return: The last successful build number
        """
        info = self.info['lastSuccessfulBuild']
        if info:
            return int(info['number'])
        else:
            logger.warning("Could not find last successfull build for jenkins project '%s'" % self.name)
            return None

    def get_last_stable_build(self):
        """ Retrieves the last successful build number for this project
            :return: The last successful build number
        """
        info = self.info['lastStableBuild']
        if info:
            return int(info['number'])
        else:
            logger.warning("Could not find last stable build for jenkins project '%s'" % self.name)

            return None

    def get_seconds_since_build(self, now=None):
        """ Retrieves the number of seconds since (last stable or specified) build was made for this project.
            :param now: The time now (used for unittesting - if None datetime.datetime.now() is used)
            :return: The number of seconds since last stable build or None if never
        """

        if self.build_number:
            info = self._get_build()
            if info:
                timestamp = info['timestamp']
                logger.debug("Timestamp: %s"%timestamp)
                build_time = datetime.fromtimestamp(int(timestamp)/1000)
                logger.debug("Build time: %s"%build_time)
                if now is None:
                    now = datetime.now()
                delta = now - build_time
                seconds = delta.total_seconds() # not available in python 2.6
                logger.debug("Seconds: %s"%seconds)
                return round(seconds);
            else:
                logger.warning("Could not find last stable build for jenkins project '%s'" % self.name)
        else:
            logger.warning("Project has never been built '%s'" % self.name)
        return None

    def get_artifacts(self):
        """ Retrieves artifact list for project

            :return: list of tuples with two elements: artifactname, and download url
        """
        build = self._get_build()
        return self._parse_artifacts(build['artifacts'])

    def get_upstreams(self):
        """ Retrieves upstream project names for project

            :return: list of upstream project names
        """
        upstreams = [x['name'] for x in self.info['upstreamProjects']]
        logger.debug("get_upstreams for %s: %s"%(self.name, upstreams))

        if len(upstreams) <= 0:
            build = self._get_build()
            logger.debug("get_upstreams for: %s"%build)
            for action in build['actions']:
                if 'causes' in action:
                    for cause in action['causes']:
                        if 'upstreamProject' in cause:
                            upstreams.append(cause['upstreamProject'].replace("/", "/job/"))

        logger.debug("get_upstreams for %s: %s"%(self.name, upstreams))

        return upstreams

    def get_svn_info(self):
        """ Retrieves svn information for project

            :return: list of tuples with two elements: svn path, and svn revision
        """
        config_types = {'project': '/project/scm/locations/hudson.scm.SubversionSCM_-ModuleLocation/remote',
                        'maven2-moduleset': '/maven2-moduleset/scm/locations/hudson.scm.SubversionSCM_-ModuleLocation/remote',
                            }

        def get_nodes(self, paths):
            for config_type, xpath in paths.items():
                if self.config.xpath('/%s' % config_type):
                    return xpath

        config_xpath = get_nodes(self, config_types)

        if config_xpath:
            svn_nodes = self.config.xpath(config_xpath)
            if len(svn_nodes) == 0:
                logger.warning("Could not find svn location for project '%s'" % self.name)
                # logger.debug(etree.tostring(self.config))
                return None

            build = self._get_build()

            svn_info = []

            for svn_node in svn_nodes:
                revision = [x for x in build['changeSet']['revisions'] if x['module'] == svn_node.text]

                if revision:
                    svn_info.append((svn_node.text, revision[0]['revision']))
                else:
                    logger.warning("Could not find revision for svn project '%s' for build '%s' - jenkins project '%s'" % (svn_node.text, self.build_number, self.name))
            return svn_info

    def get_git_info(self):
        """ Retrieves git information for project

            :return: list of tuples with two elements: git path, and git commit
        """
        config_types = {'flow-definition': '/flow-definition/properties/org.jenkinsci.plugins.workflow.multibranch.BranchJobProperty/branch/scm/userRemoteConfigs/hudson.plugins.git.UserRemoteConfig/url',
                        'maven2-moduleset': '/maven2-moduleset/scm/userRemoteConfigs/hudson.plugins.git.UserRemoteConfig/url'}

        def get_nodes(self, paths):
            for config_type, xpath in paths.items():
                if self.config.xpath('/%s' % config_type):
                    #logger.debug("configs '%s'" % xpath)
                    return xpath

        config_xpath = get_nodes(self, config_types)

        if config_xpath:
            git_nodes = self.config.xpath(config_xpath)
            if len(git_nodes) == 0:
                logger.warning("Could not find git location for project '%s'" % self.name)
                # logger.debug(etree.tostring(self.config))
                return None

            build = self._get_build()

            git_info = []

            for git_node in git_nodes:

                # TODO: Handle multiple changeSets?
                # build['changeSets/changeSet'][0]['items'][0]['commitId']
                if 'changeSets' in build:
                    sets = [x for x in build['changeSets'] if x['kind'] == 'git']
                    if sets:
                        git_info.append((git_node.text, sets[0]['items'][0]['commitId']))
                    else:
                        logger.warning("Could not find revision for git project '%s' for build '%s' - jenkins project '%s'" % (git_node.text, self.build_number, self.name))

                if 'changeSet' in build:
                    sets = [x for x in build["actions"] if '_class' in x and x['_class'] == 'hudson.plugins.git.util.BuildData']
                    if sets:
                        value = "%s - %s" % (sets[0]['lastBuiltRevision']['branch'][0]['name'], sets[0]['lastBuiltRevision']['SHA1'])
                        git_info.append((git_node.text, value))
                    else:
                        logger.warning("Could not find revision for git project '%s' for build '%s' - jenkins project '%s'" % (git_node.text, self.build_number, self.name))

            return git_info

    def get_scm_info(self):
        """ Retrieves version management information for project

            :return: list of tuples with two elements: svn path, and svn revision
        """
        scm_info = self.get_svn_info()

        if scm_info is None:
            scm_info = self.get_git_info()

        #if scm_info is None:
        #    die("Unknown configuration type for %s:%s: %s" % (self.name, self.build_number ,self.config.tag))

        return scm_info;


    def get_dependency_file_content(self, dependency_file_name):
        """ Retrieves the content of dependency file for project, if present.

            :return: content of dpeendency file, None if no dependency file is present
        """
        artifacts = self.get_artifacts()
        if dependency_file_name in artifacts:
            url = artifacts[dependency_file_name]
            logger.debug("Querying with url '%s'" % url)
            content = requests.get(url).text
            return content

        logger.warning('No %s found among artifacts for project %s-%s' % (dependency_file_name, self.name, self.build_number))
        return None

    def abort_build(self):
        """ Aborts the specific project build.
        """
        logger.debug("Aborting build of %s-%s" % (self.name, self.build_number))
        abort_url = requests.compat.urljoin(self.url, "job/%s/%s/stop" % (self.name, self.build_number))
        authentication = jenkins_authentication.jenkins_credentials(self.jenkins_credentials)
        response = requests.get(abort_url, auth=authentication)

        if response.status_code != requests.codes.ok:
            die("Something went wrong during abort. abort-url: '%s', answer from server: '%s'" % (abort_url, response.text))

    def __eq__(self, other):
        """ Equals operator for JenkinsProject class"""
        if self.name == other.name:
            return True
        return False

    def _get_project_config(self):
        """ retrieves project configuration """
        logger.debug("Getting config for project %s" % self.name)
        query_url = requests.compat.urljoin(self.url, "job/%s/config.xml" % self.name)
        logger.debug("Getting url %s" % query_url)
        authentication = jenkins_authentication.jenkins_credentials(self.jenkins_credentials)
        response = requests.get(query_url, auth=authentication)
        return response.content

    def _get_project_info(self, depth=1):
        """ retrieves project information """
        logger.debug("Getting info for project %s" % self.name)
        params = {'depth': depth}
        query_url = requests.compat.urljoin(self.url, "job/%s/api/python" % (self.name))
        return self._get_and_evaluate_url(query_url, params=params)

    def _get_and_evaluate_url(self, url, params=None):
        """ retrieve and evaluate url with eval"""
        logger.debug("Querying with url '%s'" % url)
        authentication = jenkins_authentication.jenkins_credentials(self.jenkins_credentials)
        response = requests.get(url, params=params, auth=authentication)
        try:
            return eval(response.content)
        except:
            die("Couldn't evaluate content from url '%s' (response '%s')" % (url, response.text))

    def _parse_artifacts(self, artifacts):
        """ parses artifact dictionary and returns list of tuples with name and url for each artifact"""
        base_url = requests.compat.urljoin(self.url, "job/%s/%s/artifact/" % (self.name, self.build_number))
        artifact_urls = dict()
        for artifact in artifacts:
            artifact_urls[artifact['fileName']] = base_url + artifact['relativePath']
        return artifact_urls

    def _get_build(self):
        """ retrieves build information from project"""
        build = [x for x in self.info['builds'] if x['number'] == self.build_number]
        logger.debug("Build %s: %s" % (self.name, build))

        if len(build) == 0:
            die("Build number %s is not a valid build-number for project %s. Valid build numbers are %s" %
                (self.build_number, self.name, sorted([x['number'] for x in self.info['builds']])))

        return build[0]
