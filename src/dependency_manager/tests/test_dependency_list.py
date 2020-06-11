#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
import pkg_resources
import unittest

from mock import patch
from mock import call

from dependency_manager.dependency_list import parse_dependency_string


class TestDependencyList(unittest.TestCase):

    def setUp(self):
        depedency_filename = pkg_resources.resource_filename('dependency_manager', 'tests/data/dependencies.txt')
        self.dependency_string = None
        with open(depedency_filename) as fh:
            self.dependency_string = fh.read()

    @patch('dependency_manager.dependency_list.JenkinsProject')
    @patch('dependency_manager.dependency_list.JenkinsRepositoryProject')
    def test_that_the_main_project_is_created_as_expected(self, repo_mock, project_mock):
        """ Test that the dependency files main project is created as expected
        """
        parse_dependency_string("jenkins_url", self.dependency_string, 'opensearchdependencies-head-metode', jenkins_credentials="user:pass")
        self.assertTrue(call('jenkins_url', 'dependency-manager-test', build_number=38, jenkins_credentials="user:pass") in project_mock.call_args_list)

    @patch('dependency_manager.dependency_list.JenkinsProject')
    @patch('dependency_manager.dependency_list.JenkinsRepositoryProject')
    def test_that_a_project_is_created_as_expected(self, repo_mock, project_mock):
        """ Test that a project in the dependency is created as expected
        """
        parse_dependency_string("jenkins_url", self.dependency_string, 'opensearchdependencies-head-metode', jenkins_credentials="user:pass")
        self.assertTrue(call('jenkins_url', 'dbc-python-head', build_number=1432, jenkins_credentials="user:pass") in project_mock.call_args_list)

    @patch('dependency_manager.dependency_list.JenkinsProject')
    @patch('dependency_manager.dependency_list.JenkinsRepositoryProject')
    def test_that_a_repository_project_is_created_as_expected(self, repo_mock, project_mock):
        """ Test that a repository project in the dependency is created as expected
        """
        parse_dependency_string("jenkins_url", self.dependency_string, 'opensearchdependencies-head-metode')
        self.assertTrue(call('jenkins_url', 'apache-solr-4.5.0', 'opensearchdependencies-head-metode', build_number=57) in repo_mock.call_args_list)

    @patch('dependency_manager.dependency_list.JenkinsProject')
    @patch('dependency_manager.dependency_list.JenkinsRepositoryProject')
    def test_that_the_expected_added_bys_are_returned(self, repo_mock, project_mock):
        """ Test whether the expected main project is returned """
        main, projects = parse_dependency_string("jenkins_url", self.dependency_string, 'opensearchdependencies-head-metode')
        for added_by in [x[1] for x in projects]:
            self.assertEqual('dependency-manager-test', added_by)

    @patch('dependency_manager.dependency_list.JenkinsProject')
    @patch('dependency_manager.dependency_list.JenkinsRepositoryProject')
    def test_that_the_expected_number_of_dependendent_projects_are_returned(self, repo_mock, project_mock):
        """ Test whether the expected number of dependendent projects are returned """
        main, projects = parse_dependency_string("jenkins_url", self.dependency_string, 'opensearchdependencies-head-metode')
        self.assertEqual(2, len(projects))
