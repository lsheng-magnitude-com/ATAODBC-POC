from __future__ import print_function

import os
import Command
from Booster.Debug import Debug as Debugger
import os.path

import ata.log

logger = ata.log.AtaLog(__name__)


def Execute(root):
    """
    Get the user input for Maven (clean, package, clean package, or install).
    :param root: Maven tag content.
    :return: execution of Maven based on input.
    """
    logger.printHeader('Maven')

    dbg = Debugger()
    setMVNHome(root)
    setJavaHome(root)
    cmd = getCMD(root)
    buildfiles = list(root)
    for buildfile in buildfiles:
        file = buildfile.text
        mvnOpt = getMvnOpt(buildfile)
        pom = buildfile.attrib.get('pom')
        ExecuteCommand(file, mvnOpt, cmd, pom, dbg)


def Debug(root):
    """
    Sets up debug log for Maven.
    :param root:
    :return: log statements for Maven.
    """
    logger.printHeader('Maven')

    setMVNHome(root)
    setJavaHome(root)
    cmd = getCMD(root)
    buildfiles = list(root)
    for buildfile in buildfiles:
        file = buildfile.text
        cwd = buildfile.attrib.get('cwd')
        mvnOpt = getMvnOpt(buildfile)
        command = getCommand(file, mvnOpt, cmd)
        if cmd.upper() == 'CLEAN':
            Command.ExecuteAndGetResult(command, cwd)
        elif cmd.upper() == 'PACKAGE':
            Command.ExecuteAndGetResult(command, cwd)
        elif cmd[:7].upper() == 'INSTALL':
            command = getCompileCommandInstall(file, mvnOpt, cmd)
            Command.ExecuteAndATALog(command)
        else:
            Command.ExecuteAndATALog(command)
        print(command + 'log to ' + log)


def setMVNHome(root):
    """
    Set Maven Home path in the environmental variable.
    :param root: Maven tag root.
    :return: environmental variable for maven home is set to user's input.
    """
    m2Home = root.attrib.get('M2_HOME', '')
    os.environ['BOOSTER_VAR_M2_HOME'] = m2Home


def setJavaHome(root):
    """
    Set Java Home path in the environmental variable.
    :param root: Maven tag root.
    :return: environmental variable for jave home is set to user's input.
    """
    javaHome = root.attrib.get('JAVA_HOME', '')
    os.environ['BOOSTER_VAR_JAVA_HOME'] = javaHome


def getCMD(root):
    """
    Get user's input for maven action.
    :param root: Maven tag root.
    :return: the execution action for maven user inputted.
    """
    cmd = root.attrib.get('cmd', '')
    return cmd


def getMvnOpt(buildfile):
    """
    Get maven option attribute string for maven commands.
    :param buildfile: Source tag attribute.
    :return: string for command.
    """
    mvnOpt = buildfile.attrib.get('opt', '')
    return mvnOpt


def ExecuteCommand(file, mvnOpt, cmd, pom, dbg):
    """
    Compiles command and execute the command.
    :param file: path to file.
    :param mvnOpt: extra commands user includes.
    :param cmd: command for maven.
    :param pom: pom file if included.
    :return: execute the command from user input.
    """
    command = getCommand(file, mvnOpt, cmd)
    if cmd[:7].upper() == 'INSTALL':
        command = getCompileCommandInstall(file, mvnOpt, cmd)
        Command.ExecuteAndATALog(command)
    elif pom != "":
        command = getCompileCommandpom(mvnOpt, cmd, pom)
        Command.ExecuteAndGetResult(command, file)
    else:
        if dbg.skip('mvn', 'skip mvn\n{}'.format(command)):
            return
        Command.ExecuteAndGetResult(command, file)


def getCommand(file, mvnOpt, cmd):
    """
    Construct the maven command from user input.
    :param file: pom.xml files.
    :return: maven command to be executed.
    """
    command = 'mvn ' + mvnOpt + ' ' + file + ' ' + cmd
    return command


def getCompileCommandpom(mvnOpt, cmd, pom):
    """
    Construct the maven command from user input.
    :param file: pom.xml files.
    :return: maven command to be executed.
    """
    command = 'mvn ' + '-f ' + mvnOpt + ' ' + pom + ' ' + cmd
    return command


def getCompileCommandInstall(
        file, mvnOpt, cmd):
    """
    Construct the maven command for install from user input.
    :param file: file, DgroupId, DartifactId, Dversion, Dpackaging.
    :return: maven command to be executed.
    """
    command = ''.join(['mvn ' + cmd, ' ', '"-Dfile=', file, '" ', mvnOpt])
    return command


def getLogPath(file):
    fileName = os.path.basename(file)
    logName = fileName.replace('.xml', '.log')
    logPath = 'log/' + logName
    return logPath
