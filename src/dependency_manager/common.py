#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
:mod:`dependency_manager.common` -- common functions
====================================================

================
Common Functions
================

Contains common functions and classes for the dependency-manager project.
"""
import logging


class NullHandler(logging.Handler):
    """ Nullhandler for logging. """
    def emit(self, record):
        pass

# define logger
logger = logging.getLogger("dbc." + __name__)
logger.addHandler(NullHandler())


def die(mesg, error_class=RuntimeError):
    """ Logs mesg and raises Error. """
    logger.error(mesg)
    raise error_class(mesg)


class DependencyException(Exception):
    """ Exception class to signal dependency build number mismatch
    """
    pass
