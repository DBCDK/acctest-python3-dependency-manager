#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
import pkg_resources
import unittest
from mock import Mock

from dependency_manager.repository_project import JenkinsRepositoryProject


class TestRepositoryProject(unittest.TestCase):

    def setUp(self):
        project_info_filename = pkg_resources.resource_filename('dependency_manager', 'tests/data/repository_project_info.txt')
        self.project_info = None
        with open(project_info_filename) as fh:
            self.project_info = eval(fh.read())

        self.project_config = None
        project_config_filename = pkg_resources.resource_filename('dependency_manager', 'tests/data/repository_project_config.txt')
        with open(project_config_filename) as fh:
            self.project_config = fh.read()

    def test_url_without_slash_looks_as_expected(self):
        """ Test that jenkins_url without slash looks as expected """
        JenkinsRepositoryProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsRepositoryProject._get_project_config = Mock(return_value=self.project_config)
        JenkinsRepositoryProject.get_last_successful_build = Mock(return_value=57)

        jp = JenkinsRepositoryProject("jenkins_url", "apache-solr-4.4.0", "repository_name")

        self.assertEqual("jenkins_url/", jp.url)

    def test_url_with_slash_looks_as_expected(self):
        """ Test that jenkins_url without slash looks as expected """
        JenkinsRepositoryProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsRepositoryProject._get_project_config = Mock(return_value=self.project_config)
        JenkinsRepositoryProject.get_last_successful_build = Mock(return_value=57)

        jp = JenkinsRepositoryProject("jenkins_url/", "apache-solr-4.4.0", "repository_name")

        self.assertEqual("jenkins_url/", jp.url)

    def test_non_existing_argument_raises(self):
        """ test that non existing artifact raises error """

        JenkinsRepositoryProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsRepositoryProject._get_project_config = Mock(return_value=self.project_config)
        JenkinsRepositoryProject.get_last_successful_build = Mock(return_value=57)

        self.assertRaises(RuntimeError, JenkinsRepositoryProject, "jenkins_url/", "non-existing-artifact", "repository_name")
        # with self.assertRaises(RuntimeError):
        #     jp = JenkinsRepositoryProject("jenkins_url/", "non-existing-artifact", "repository_name")

    def test_build_number_looks_as_expected_if_supplied(self):
        """ Test that build number looks as expected if supplied """
        JenkinsRepositoryProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsRepositoryProject._get_project_config = Mock(return_value=self.project_config)
        JenkinsRepositoryProject.get_last_successful_build = Mock(return_value=57)

        jp = JenkinsRepositoryProject("jenkins_url/", "apache-solr-1.4.1", "repository_name", build_number=56)

        self.assertEqual(56, jp.build_number)

    def test_build_numberlooks_as_expected_if_not_supplied(self):
        """ Test that build number looks as expected if not supplied """
        JenkinsRepositoryProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsRepositoryProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsRepositoryProject("jenkins_url/", "apache-solr-1.4.1", "repository_name")

        self.assertEqual(57, jp.build_number)

    def test_get_last_successful_build_returns_expected_build_number(self):
        """ Test that the expected build number is returned from get_last_successful_build """
        JenkinsRepositoryProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsRepositoryProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsRepositoryProject("jenkins_url/", "apache-solr-1.4.1", "repository_name")

        self.assertEqual(57, jp.get_last_successful_build())

    def test_that_the_expected_artifacts_are_returned_from_get_artifacts(self):
        """ Test that the expected artifacts are returned from get_artifacts """
        JenkinsRepositoryProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsRepositoryProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsRepositoryProject("jenkins_url/", "apache-solr-1.4.1", "repository_name")

        expected_artifact_dict = {'apache-solr-1.4.1.zip.md5': 'jenkins_url/job/repository_name/57/artifact/trunk/ARTIFACTS/apache-solr-1.4.1/apache-solr-1.4.1.zip.md5',
                                  'apache-solr-1.4.1.zip': 'jenkins_url/job/repository_name/57/artifact/trunk/ARTIFACTS/apache-solr-1.4.1/apache-solr-1.4.1.zip'}

        self.assertEqual(expected_artifact_dict, jp.get_artifacts())

    def test_that_get_upstreams_returns_empty_list(self):
        """ Test that get_upstreams reutrn empty list """
        JenkinsRepositoryProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsRepositoryProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsRepositoryProject("jenkins_url/", "apache-solr-1.4.1", "repository_name")

        self.assertEqual([], jp.get_upstreams())

    def test_that_get_svn_info_returns_the_expected_list(self):
        """ Test that the get_svn_info method returns the expected list """
        JenkinsRepositoryProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsRepositoryProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsRepositoryProject("jenkins_url/", "apache-solr-1.4.1", "repository_name")

        self.assertEqual([('repository_name', 'NA')], jp.get_scm_info())

    def test_that_get_dependency_file_content_returns_none(self):
        """ Test that the method get_dependency_file_content returns None """
        JenkinsRepositoryProject._get_project_info = Mock(return_value=self.project_info)
        JenkinsRepositoryProject._get_project_config = Mock(return_value=self.project_config)

        jp = JenkinsRepositoryProject("jenkins_url/", "apache-solr-1.4.1", "repository_name")

        self.assertEqual(None, jp.get_dependency_file_content())
