#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
from datetime import datetime
import pkg_resources
import unittest
import requests
from requests.auth import HTTPBasicAuth
from mock import Mock
from mock import ANY

from dependency_manager.jenkins_project import JenkinsProject


class TestJenkinsProject(unittest.TestCase):

    def setUp(self):

        project_info_filename = pkg_resources.resource_filename('dependency_manager', 'tests/data/project_info.txt')
        self.project_info = None
        with open(project_info_filename, "rb") as fh:
            self.project_info = eval(fh.read())

        never_built_project_info_filename = pkg_resources.resource_filename('dependency_manager', 'tests/data/project_info_never_built.json')
        self.never_built_project_info = None
        with open(never_built_project_info_filename, "rb") as fh:
            self.never_built_project_info = eval(fh.read())

        self.project_config = None
        project_config_filename = pkg_resources.resource_filename('dependency_manager', 'tests/data/project_config.xml')
        with open(project_config_filename, "rb") as fh:
            self.project_config = fh.read()

        self.java_project_config = None
        project_config_filename = pkg_resources.resource_filename('dependency_manager', 'tests/data/java_config.xml')
        with open(project_config_filename, "rb") as fh:
            self.java_project_config = fh.read()

        self.unknown_project_config = None
        unknown_project_config_filename = pkg_resources.resource_filename('dependency_manager', 'tests/data/unknown_config_type.xml')
        with open(unknown_project_config_filename, "rb") as fh:
            self.unknown_project_config = fh.read()

        java_project_info_filename = pkg_resources.resource_filename('dependency_manager', 'tests/data/java_info.txt')
        self.java_project_info = None
        with open(java_project_info_filename, "rb") as fh:
            self.java_project_info = eval(fh.read())

        self.project_config_no_svn = None
        project_config_filename = pkg_resources.resource_filename('dependency_manager', 'tests/data/project_config_no_svn.xml')
        with open(project_config_filename, "rb") as fh:
            self.project_config_no_svn = fh.read()

        self.project_info_multiple_svn = None
        project_info_filename = pkg_resources.resource_filename('dependency_manager', 'tests/data/project_info_multiple_svn.txt')
        with open(project_info_filename, "rb") as fh:
            self.project_info_multiple_svn = eval(fh.read())

        self.project_config_multiple_svn = None
        project_config_filename = pkg_resources.resource_filename('dependency_manager', 'tests/data/project_config_multiple_svn.txt')
        with open(project_config_filename, "rb") as fh:
            self.project_config_multiple_svn = fh.read()

    def test_url_without_slash_looks_as_expected(self):
        """ Test that jenkins_url without slash looks as expected """
        JenkinsProject._get_project_info = Mock()
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)
        JenkinsProject.get_last_stable_build = Mock()

        jp = JenkinsProject("jenkins_url", "project_name")

        self.assertEqual("jenkins_url/", jp.url)

    def test_url_with_slash_looks_as_expected(self):
        """ Test that jenkins_url without slash looks as expected """
        JenkinsProject._get_project_info = Mock()
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)
        JenkinsProject.get_last_stable_build = Mock()

        jp = JenkinsProject("jenkins_url/", "project_name")

        self.assertEqual("jenkins_url/", jp.url)

    def test_build_number_looks_as_expected_if_supplied(self):
        """ Test that build number looks as expected if supplied """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name", build_number=2)

        self.assertEqual(2, jp.build_number)

    def test_build_numberlooks_as_expected_if_not_supplied(self):
        """ Test that build number looks as expected if not supplied """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        self.assertEqual(20, jp.build_number)

    def test_get_last_successful_build_returns_expected_build_number(self):
        """ Test that the expected build number is returned from get_last_successful_build """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        self.assertEqual(20, jp.get_last_successful_build())

    def test_get_last_successful_build_returns_none_if_never_built(self):
        """ Test that the expected build number is returned from get_last_successful_build """
        JenkinsProject._get_project_info = Mock(return_value=self.never_built_project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        self.assertEqual(None, jp.get_last_successful_build())

    def test_get_last_stable_build_returns_none_if_never_built(self):
        """ Test that the expected build number is returned from get_last_successful_build """
        JenkinsProject._get_project_info = Mock(return_value=self.never_built_project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        self.assertEqual(None, jp.get_last_stable_build())

    def test_that_the_expected_artifacts_are_returned_from_get_artifacts(self):
        """ Test that the expected artifacts are returned from get_artifacts """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        expected_artifact_dict = {'dependencies.txt': 'jenkins_url/job/project_name/20/artifact/dependencies.txt',
                                  'artifact-c.txt': 'jenkins_url/job/project_name/20/artifact/artifact-c.txt'}

        self.assertEqual(expected_artifact_dict, jp.get_artifacts())

    def test_unsupported_build_number_raises_if_supplied_to_get_artifacts(self):
        """ Test that unsupported build number raises if supplied to get_artifacts"""
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name", build_number=100)

        self.assertRaises(RuntimeError,  jp.get_artifacts)

    def test_that_the_expected_upstreams_are_returned_from_get_upstreams(self):
        """ Test that the expected upstream projects are returned from get_upstreams """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        self.assertEqual(['dependency-manager-test-A'], jp.get_upstreams())

    def test_that_the_expected_build_age_is_returned(self):
        """ Test that the expected upstream projects are returned from get_upstreams """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        now = datetime(2014, 1, 1)

        # timestamp in file: 1388405832175 : 2013-12-30T13:17:12
        # 124968 seconds from 1/1 2014
        self.assertEqual(124968, jp.get_seconds_since_build(now))

    def test_that_the_expected_build_age_is_returned(self):
        """ Test that the correct age is returned for the last stable build """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        now = datetime(2014, 1, 1)

        # timestamp in file: 1388405832175 : 2013-12-30T13:17:12
        # 124968 seconds from 1/1 2014
        self.assertEqual(124968, jp.get_seconds_since_build(now))

    def test_that_the_expected_build_age_is_returned_for_older_build(self):
        """ Test that the correct age is returned for an older build """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name", build_number=18)

        now = datetime(2014, 1, 1)
        self.assertEqual(130282, jp.get_seconds_since_build(now))

    def test_that_no_build_age_is_returned_if_never_built(self):
        """ Test that age is none if never built """
        JenkinsProject._get_project_info = Mock(return_value=self.never_built_project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        self.assertEqual(None, jp.get_seconds_since_build())

    def test_that_the_expected_svn_info_is_returned_from_get_scm_info(self):
        """ Test that the expected svn information is returned """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        self.assertEqual([('https://svn.dbc.dk/repos/new-dependency-manager/trunk', 67541)], jp.get_svn_info())

    def test_that_the_expected_svn_info_is_returned_from_java_project_with_get_scm_info(self):
        """ Test that the expected svn information is returned from a java project"""
        JenkinsProject._get_project_info = Mock(return_value=self.java_project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.java_project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        self.assertEqual([('https://svn.dbc.dk/repos/addi-service/trunk', 67812)], jp.get_svn_info())

    def test_that_an_error_is_raised_if_config_type_is_unknown(self):
        """ Test that an error is raised if the conif type is unknown """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.unknown_project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        self.assertEqual(None, jp.get_svn_info())

    def test_that_the_expected_svn_info_is_returned_from_get_scm_info_from_project_with_no_svn(self):
        """ Test that the expected svn information is returned from project with no svn """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config_no_svn)

        jp = JenkinsProject("jenkins_url/", "project_name")

        self.assertEqual(None, jp.get_svn_info())

    def test_that_the_expected_svn_info_is_returned_from_get_scm_info_from_project_with_multiple_svn(self):
        """ Test that the expected svn information is returned from project with no svn """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info_multiple_svn)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config_multiple_svn)

        jp = JenkinsProject("jenkins_url/", "project_name")

        expected_svn_info = [('https://svn.dbc.dk/repos/new-dependency-manager/trunk', 67623),
                             ('https://svn.dbc.dk/repos/dbc-python', 63555)]

        self.assertEqual(expected_svn_info, jp.get_svn_info())


    def test_get_dependency_file_content_requests_with_expected_url(self):
        """ Test that get_dependency_file_content requests and reads the expected url """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        url_object = Mock()
        url_object.read = Mock(return_value="DEPENDENCY-FILE CONTENT")
        requests.get = Mock(return_value=url_object)

        jp.get_dependency_file_content("dependencies.txt")
        requests.get.assert_called_once_with('jenkins_url/job/project_name/20/artifact/dependencies.txt')


    def test_get_dependency_file_content_do_not_request_if_no_dependency_file_is_among_artifacts(self):
        """ Test that get_dependency_file_content does not request if no dependency file is located among artifacts"""
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        url_object = Mock()
        url_object.read = Mock(return_value="DEPENDENCY-FILE CONTENT")
        requests.get = Mock(return_value=url_object)

        jp.get_dependency_file_content("dependencies")
        #self.assertEqual(None, requests.geturllib.request.urlopen.call_args)

    def test_that_abort_build_uses_expected_url(self):
        """ Test that abort_build uses the expected url """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name", jenkins_credentials=":")

        url_object = Mock()
        url_object.status_code = requests.codes.ok
        requests.get = Mock(return_value=url_object)

        jp.abort_build()

        requests.get.assert_called_once_with('jenkins_url/job/project_name/20/stop', auth=ANY)

    def test_that_abort_build_throws_error_if_return_code_is_different_from_200(self):
        """ Test that abort_build raises error if return code is different from 200 """
        JenkinsProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsProject("jenkins_url/", "project_name")

        url_object = Mock()
        url_object.status_code = requests.codes.not_found
        requests.get = Mock(return_value=url_object)

        self.assertRaises(RuntimeError, jp.abort_build)
