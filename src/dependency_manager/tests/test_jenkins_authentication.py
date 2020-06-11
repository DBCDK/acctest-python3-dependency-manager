#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
import unittest
from requests.auth import HTTPBasicAuth

import dependency_manager.jenkins_authentication as jenkins_authentication


class TestJenkinsProject(unittest.TestCase):

    def setUp(self):
        pass

    def test_url_with_credentials(self):
        """ Test creation of url with credentials """

        self.assertEqual(HTTPBasicAuth("user", "pass"),
                         jenkins_authentication.jenkins_credentials("user:pass"))

