#!/usr/bin/env python
# -*- coding: utf-8 -*-
# -*- mode: python -*-
import logging
import os
import re
import requests
import shutil
import subprocess
from lxml import etree

from .common import NullHandler
from .common import die
from .dependency_manager import download_artifacts
from . import jenkins_authentication


logger = logging.getLogger("dbc." + __name__)
logger.addHandler(NullHandler())


def yield_view_jobs(jenkins_server, jenkins_user, view):
    logger.info("identifying jobs")
    if not jenkins_server.endswith('/'):
        jenkins_server += '/'
    url = "%suser/%s/my-views/view/%s/api/python" % (jenkins_server, jenkins_user, view)
    content = _get_and_evaluate_url(url)

    for job in content['jobs']:
        yield (job['name'], job['url'])


def _get_description_artifacts(name, url, artifact_keyword):
    logger.debug("identifying artifacts for %s" % name)
    authentication = jenkins_authentication.jenkins_credentials()
    xml_string = requests.get(url+"config.xml", auth=authentication).content

    xml = etree.fromstring(xml_string)

    config_types = {'project': '/project/description',
                    'maven2-moduleset': '/maven2-moduleset/description',
                    'flow-definition': '/flow-definition/description'}

    description_xpath = None

    for config_type, xpath in config_types.items():
        if xml.xpath('/%s' % config_type):
            description_xpath = xpath
            break

    if not description_xpath:
        die("Unknown configuration type: %s" % xml.tag)

    description = xml.xpath(description_xpath)[0].text
    artifacts = re.findall("%s:(.*?):" % artifact_keyword, description, re.DOTALL)
    return [x.split('=') for x in artifacts]


def get_md5_sum(filepath):
    result = subprocess.Popen(["md5sum", filepath], stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)

    out, err = result.communicate()
    return out.split()[0].strip()


def check_md5_sums(folder):

    logger.info("Checking md5 sums")
    files = []
    for filename in os.listdir(folder):
        if not filename.endswith('.md5'):

            if not os.path.exists(os.path.join(folder, filename + '.md5')):
                die("could not find md5 file for artifact %s" % filename)

            files.append([os.path.abspath(os.path.join(folder, x)) for x in [filename, filename + '.md5']])

    for file_path, md5_path in files:
        file_sum = get_md5_sum(file_path)
        md5_sum = None
        with open(md5_path) as fh:
            md5_sum = fh.read().strip()

        if not file_sum == md5_sum:
            die("md5 sum for file %s didn't match: %s != %s" % (file_path, file_sum, md5_sum) )

def create_symlinks(download_folder, symlink_list):
    files = os.listdir(download_folder)
    cur = os.getcwd()
    os.chdir(download_folder)
    for symlink_name, file_pattern in symlink_list:

        matched_pair = []
        for name in [x for x in files if not x.endswith('.md5')]:
            if re.match(file_pattern, name) and name != symlink_name:
                matched_pair.append((name, symlink_name))

        if len(matched_pair) > 1:
            die("Found multiple matching files for pattern %s, matches %s" % file_pattern, [x[0] for x in matched_pair])

        logger.debug("Creating symlink %s" % symlink_name)
        if matched_pair:
            retcode = subprocess.call(["ln", "-s", matched_pair[0][0], matched_pair[0][1]])
            if retcode != 0:
                die("could not create symlink for file %s" % matched_pair[0][0])

    os.chdir(cur)


def create_md5file(path):
    cmd = "md5sum %s > %s.md5" % (path, path)
    result = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    (stdout, stderr) = result.communicate()
    if result.returncode != 0:
        die("could not create md5sum for file %s, output: %s" % (path, stdout + "\n" + stderr))


def create_package(download_folder, package_name, dependency_file):
    logger.info("Creating tar archive")
    shutil.copy(dependency_file, download_folder)
    os.rename(download_folder, package_name)
    retcode = subprocess.call(["tar", "cvzf", "%s.tgz" % package_name, package_name], stdout=subprocess.PIPE)
    if retcode != 0:
        die("could not create tar archive of folder %s" % package_name)
    create_md5file("%s.tgz" % package_name)
    # retcode = subprocess.call(["md5sum", "%s.tgz" % package_name], stdout=subprocess.PIPE)
    # if retcode != 0:
    #     die("could not create md5sum for file %s" % "%s.tgz" % package_name)
    logger.info("package %s created" % package_name)


def _get_and_evaluate_url(url):
    """ retrieve and evaluate url with eval"""
    logger.debug("Querying with url '%s'" % url)
    content = requests.get(url).text

    try:
        return eval(content)
    except:
        die("Couldn't evaluate content from url '%s' (response '%s')" % (url, content))


def cli():

    from optparse import OptionParser

    usage = "Builds package containing artifacts pointed to by a specific view."
    parser = OptionParser(usage="%prog [options] view artifact-keyword package-name" + usage)

    parser.add_option("-d", "--download", type="string", action="store", dest="download_folder", default='resources',
                      help="download project artifacts from dependency-file to specified folder. default is 'resources'")

    parser.add_option("-p", "--pattern", type="string", action="store", dest="pattern", default=None,
                      help="Additional pattern used to expand pattern created by the package view")


    parser.add_option("-m", "--remove-md5s", action="store_true", dest="remove_md5s", default=False,
                      help="if set, removes md5s in file")

    parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                      help="Verbose output.")

    (options, args) = parser.parse_args()

    if len(args) < 3:
        parser.error("need view, artifact-keyword and package-name")

    return (options, args[0], args[1], args[2])


def setup_logger(verbose):
    logging.basicConfig(level=logging.DEBUG,
                        filename='create_package.log',
                        filemode='w')
    logger = logging.getLogger('')
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    if verbose:
        ch.setLevel(logging.DEBUG)
    logger.addHandler(ch)


def main():

    JENKINS_SERVER = 'http://is.dbc.dk'
    REPOSITORY_PROJECT = 'opensearch-3rd-party-dependencies'
    JENKINS_USER = 'opensearch'
    DEPENDENCY_FILENAME = 'dependencies.txt'

    (options, view, artifact_keyword, package_name) = cli()
    setup_logger(options.verbose)

    artifacts = []
    for name, url in yield_view_jobs(JENKINS_SERVER, JENKINS_USER, view):
        artifacts += _get_description_artifacts(name, url, artifact_keyword)

    pattern = "|".join([x[1] for x in artifacts])
    if options.pattern:
        pattern += "|" + options.pattern

    if not os.path.exists(options.download_folder):
        os.mkdir(options.download_folder)

    download_artifacts(options.download_folder, pattern, DEPENDENCY_FILENAME, JENKINS_SERVER, REPOSITORY_PROJECT)
    check_md5_sums(options.download_folder)

    create_symlinks(options.download_folder, artifacts)

    if options.remove_md5s:
        for f in os.listdir(options.download_folder):
            path = os.path.join(options.download_folder, f)
            if path.endswith('.md5'):
                os.remove(path)

    create_package(options.download_folder, package_name, DEPENDENCY_FILENAME)

if __name__ == '__main__':
    main()
