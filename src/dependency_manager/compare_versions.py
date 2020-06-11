
import logging
import re
import subprocess

from .common import NullHandler


logger = logging.getLogger("dbc." + __name__)
logger.addHandler(NullHandler())

def svn_log( old_revision, new_revision, svn_path, options ):
    logger.debug("diff %s to %s for %s" % ( old_revision, new_revision, svn_path ) )
    revision_arg = "-r%s:%s" % ( int(old_revision) + 1, new_revision )

    if options.diff:
        command = "svn diff -r%s:%s %s" % ( int(old_revision) + 1, new_revision, svn_path)
    else:
        command = "svn log -r%s:%s %s" % ( int(old_revision) + 1, new_revision, svn_path)
    logger.debug("Execute %s"%command )
    #output = subprocess.check_output(  command )
    result = subprocess.Popen( command, shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE )
    ( stdout, stderr ) = result.communicate()

    if result.returncode != 0:
        mesg = "Error encountered during svn command. cmd = '%s'\nstdout = '%s'\nstderr = '%s'\nreturncode = '%s'"%( command, stdout, stderr, result.returncode )
        logger.error( mesg )
        raise RuntimeError( mesg )
    return stdout;

def compare_revisions( old_svn_info, new_svn_info, options ):
    print( "Modules:" )

    for (new_path, new_revision) in new_svn_info:
        for (old_path, old_revision) in old_svn_info:
            if new_path == old_path:
                if old_revision != new_revision:
                    print( "==========" )
                    print(( "%s: revision %s -> %s" % ( new_path, old_revision, new_revision ) ))
                    print( "----------" )
                    print( "Changes:" )
                    print(( svn_log( old_revision, new_revision, new_path, options ) ))

                else:
                    print(( "%s: revision %s same revision" % ( new_path, new_revision ) ))


def compare_versions( old_dependencies_file, new_dependencies_file, job_name, options ):
    logger.info( "Comparing %s to %s for job %s" % ( old_dependencies_file, new_dependencies_file, job_name ) )

    with open(new_dependencies_file) as fh:
        content_new = fh.read()

    with open(old_dependencies_file) as fh:
        content_old = fh.read()

    dependencies_old = parse_dependency_string( content_old )
    logger.debug("Old dependencies: %s" % dependencies_old )

    dependencies_new = parse_dependency_string( content_new )
    logger.debug("New dependencies: %s" % dependencies_new )

    project_old = [proj for proj in dependencies_old if proj['name'] == job_name] [0]
    project_new = [proj for proj in dependencies_new if proj['name'] == job_name] [0]

    svn_old = project_old['svn']
    build_old = project_old['build_number']
    logger.debug("Old svn info: %s" % svn_old )

    svn_new = project_new['svn']
    build_new = project_new['build_number']
    logger.debug("New svn info: %s" % svn_new )

    print(( "Revision information for changes in job '%s' between build %s and build %s:" % ( job_name, build_old, build_new) ))
    compare_revisions( svn_old, svn_new, options )


# Based on dependency_list.parse_dependency_string and loads svn revision data from file:
def parse_dependency_string( dependency_string):
    dependencies = []
    project = []

    for line in [x for x in dependency_string.split('\n') if x != ""]:
        if not line.startswith('#'):

            if not line.startswith(' '):

                if project:
                    dependencies.append(add_project(project))
                project = []
                project.append(line.strip())

            else:
                project.append(line.strip())

    if project:
        dependencies.append(add_project(project))

    return dependencies

def add_project(project):

    name = project[0]
    logger.debug("name: %s" % name )

    build_number = int(project[2].replace("Build: ", ""))
    logger.debug("build: %s" % build_number )

    svn = []

    for i in range(3, len(project) ):
        data = re.sub("(SVN/GIT|SVN): ", "", project[i]).split()
        url = data[0]
        revision = data[2].replace( ')', '' )
        logger.debug("Adding svn module: '%s', revision %s" % ( url, revision ) )
        svn.append( ( url, revision ) )

    return {
        'name': name,
        'build_number': build_number,
        'svn': svn }

def cli():

    from optparse import OptionParser

    usage = "Compare the version information for a named job in two different dependencies files\nPrint subversion log for changes in the modules used by the job"
    
    parser = OptionParser(usage="%prog old_dependencies_file new_dependencies_file job_name_to_filter" + usage)

    parser.add_option("-d", "--diff", action="store_true", dest="diff", default=False,
                      help="Include diff report in svn log")

    (options, args) = parser.parse_args()

    if len(args) < 3:
        parser.error("need old_dependencies_file, new_dependencies_file and job_name_to_filter")

    return (options, args[0], args[1], args[2])


def setup_logger():
    logging.basicConfig(level=logging.DEBUG,
                        filename='compare_versions.log',
                        filemode='w')

def main():
    logger.info("Starting version comparison")
    setup_logger()
    (options, old_dependencies_file, new_dependencies_file, job_name) = cli()
    compare_versions(old_dependencies_file, new_dependencies_file, job_name, options)


if __name__ == '__main__':
    main()
