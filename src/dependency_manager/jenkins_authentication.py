#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
:mod:`dependency_manager.jenkins_authentication` -- contains functions for accessing jenkins
==========================================================================

===============
Jenkins Authentication
===============

Contains functions for accessing Jenkins
"""
import os
import netrc
import logging
from .common import NullHandler
from requests.auth import HTTPBasicAuth

# define logger
logger = logging.getLogger("dbc." + __name__)
logger.addHandler(NullHandler())

#def url_with_credentials(url, credentials=None):
def jenkins_credentials(credentials=None):
    """ Creates an url with credentials added
        :credentials: string of format 'user:pass'
        If credentials is None, it will look in ~/.netrc file and if nothing is found
        It will look in env variable $JENKINS_CREDENTIALS
    """

    if credentials == None:
        logger.debug("No credentials provided, looking in .netrc")
        JENKINS_HOST = 'is.dbc.dk'
        try:
            n = netrc.netrc()
            if JENKINS_HOST in list(n.hosts.keys()):
                logger.debug("Found credentials in .netrc")
                jenkins_user = n.hosts[JENKINS_HOST][0]
                jenkins_pass = n.hosts[JENKINS_HOST][2]
                credentials = "%s:%s" % (jenkins_user, jenkins_pass)
        except:
            pass

    if credentials == None:
        logger.debug("No credentials provided, looking in env variable '$JENKINS_CREDENTIALS'")
        credentials = os.getenv("JENKINS_CREDENTIALS", None)

    result = None
    if credentials != None:
        split = credentials.split(":")
        result = HTTPBasicAuth(split[0], split[1])
        logger.debug("Using Jenkins credentials")
    else:
        logger.debug("No Jenkins credentials found")
    return result
