#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
import pkg_resources
import unittest
from mock import Mock
from mock import call
import os
import shutil
import tempfile
import urllib.request, urllib.parse, urllib.error

from dependency_manager.dependency_manager import download_artifacts
from dependency_manager.dependency_manager import build_dependency_file
from dependency_manager.common import DependencyException
import dependency_manager.dependency_list


class TestDependencyManager(unittest.TestCase):

    def setUp(self):
        self.depedency_filename = pkg_resources.resource_filename('dependency_manager', 'tests/data/dependencies.txt')
        self.dependency_string = None
        with open(self.depedency_filename) as fh:
            self.dependency_string = fh.read()

        self.test_folder = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_folder)

    def test_download_artifacts_creates_download_folder_if_it_does_not_exist(self):
        """ Test that download folder is created if it does not exist """

        main_mock = Mock()
        project1_mock = Mock()
        main_mock.get_artifacts = Mock(return_value={'artifact-name-1': 'artifact-url-1'})
        project1_mock.get_artifacts = Mock(return_value={'artifact-name-2': 'artifact-url-2'})

        download_folder = os.path.join(self.test_folder, "download_folder")
        self.assertFalse(os.path.exists(download_folder))

        dependency_manager.dependency_manager.parse_dependency_string = Mock(return_value=((main_mock, None), [(project1_mock, None)]))
        urllib.request.urlretrieve = Mock()
        download_artifacts(download_folder, ".*", self.depedency_filename, "jenkins_server", "repo_name")

        self.assertTrue(os.path.exists(download_folder))
        
    def test_download_artifacts_retrieves_expected_artifacts(self):
        """ Test that the expected artifacts are retrieved """
        main_mock = Mock()
        project1_mock = Mock()
        main_mock.get_artifacts = Mock(return_value={'artifact-name-1': 'artifact-url-1'})
        project1_mock.get_artifacts = Mock(return_value={'artifact-name-2': 'artifact-url-2'})

        download_folder = os.path.join(self.test_folder, "download_folder")

        dependency_manager.dependency_manager.parse_dependency_string = Mock(return_value=((main_mock, None), [(project1_mock, None)]))
        urllib.request.urlretrieve = Mock()
        download_artifacts(download_folder, ".*", self.depedency_filename, "jenkins_server", "repo_name")

        expected_calls = [call('artifact-url-1', os.path.join(download_folder, 'artifact-name-1')),
                          call('artifact-url-2', os.path.join(download_folder, 'artifact-name-2'))]

        self.assertEqual(expected_calls, urllib.request.urlretrieve.call_args_list)

    def test_download_artifacts_retrieves_artifacts_matching_pattern(self):
        """ Test that the artifacts matching the pattern are retrieved """
        main_mock = Mock()
        project1_mock = Mock()
        main_mock.get_artifacts = Mock(return_value={'artifact-name-1': 'artifact-url-1'})
        project1_mock.get_artifacts = Mock(return_value={'artifact-name-2': 'artifact-url-2'})

        download_folder = os.path.join(self.test_folder, "download_folder")

        dependency_manager.dependency_manager.parse_dependency_string = Mock(return_value=((main_mock, None), [(project1_mock, None)]))
        urllib.request.urlretrieve = Mock()
        download_artifacts(download_folder, ".*?1.*", self.depedency_filename, "jenkins_server", "repo_name")

        expected_calls = [call('artifact-url-1', os.path.join(download_folder, 'artifact-name-1'))]

        self.assertEqual(expected_calls, urllib.request.urlretrieve.call_args_list)

    def test_dependency_file_is_not_downloaded(self):
        """ Test that dependency file artifact is not downloaded """
        main_mock = Mock()
        project1_mock = Mock()
        main_mock.get_artifacts = Mock(return_value={'artifact-name-1': 'artifact-url-1'})
        project1_mock.get_artifacts = Mock(return_value={'artifact-name-2': 'artifact-url-2', self.depedency_filename: 'dependency_file'})

        download_folder = os.path.join(self.test_folder, "download_folder")

        dependency_manager.dependency_manager.parse_dependency_string = Mock(return_value=((main_mock, None), [(project1_mock, None)]))
        urllib.request.urlretrieve = Mock()

        download_artifacts(download_folder, ".*", self.depedency_filename, "jenkins_server", "repo_name")

        expected_calls = [call('artifact-url-1', os.path.join(download_folder, 'artifact-name-1')),
                          call('artifact-url-2', os.path.join(download_folder, 'artifact-name-2'))]

        self.assertEqual(expected_calls, urllib.request.urlretrieve.call_args_list)

    def test_build_is_aborted_if_dependency_mismatch_is_detected(self):
        """ Test that build is aborted if dependency mismatch is detected """

        dependency_manager.dependency_manager.JenkinsProject = Mock()
        dependency_manager.dependency_manager.JenkinsProject.abort_build = Mock()
        dependency_manager.dependency_manager.DependencyList = Mock(side_effect=dependency_manager.dependency_manager.DependencyException)

        self.assertRaises(DependencyException, build_dependency_file, "job_name", 12, self.depedency_filename, "jenkins_url", "repo_name")
        # with self.assertRaises(DependencyException):
        #     build_dependency_file("job_name", 12, self.depedency_filename, "jenkins_url", "repo_name")
