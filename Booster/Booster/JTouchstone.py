from __future__ import print_function
import glob
import os
import re

import Command
import Copy
import ReplaceInFile
import ata.log

logger = ata.log.AtaLog(__name__)


def Execute(root):
    print('==============================')
    print('      Enter JTouchstone')
    print('==============================')

    java = getJava(root)
    jtouchstone = getJTouchstoneBinary(root)
    cwd = getWorkingDriectory(root, jtouchstone)
    classpath = getClassPath(root, jtouchstone)
    opt = getJavaOpt(root)
    jtouchstoneclass = getJtouchstoneClass(root)
    envFile = getEnv(root)
    if not os.path.exists(envFile):
        logger.warning('Can not find ' + envFile)
        return
    suites = list(root)
    for suite in suites:
        suiteFile = suite.text
        if os.path.exists(suiteFile):
            fixDriverCalss(root, envFile, suiteFile)
            fixConnectionString(root, envFile, suiteFile)
            fixResultSetsDir(envFile, suiteFile)
            fixTestSetsDir(suiteFile)
            (outdir, output, log) = getOutputPath(suite, cwd)
            command = getJTouchstoneCommand(java, classpath, opt, jtouchstoneclass, envFile, suiteFile, output)
            Command.ExecuteAndTail(command, log, checkreturncode=False, cwd=cwd)
        else:
            logger.info('Can not find ' + suiteFile)
    Copy.copyGlobFiles(outdir + '/*', os.getcwd() + '/log/test_output/')

    # Copy the test results to Bamboo's working dir to prevent the plan to fail
    if 'BAMBOO_WORKING_DIRECTORY' in os.environ:
        working_dir = os.environ['BAMBOO_WORKING_DIRECTORY']
        test_output = os.path.join(working_dir, 'log', 'test_output')
        # Cleanup the directory first so we don't copy old results
        logger.debug('test_output ' + test_output)
        for f in glob.glob(os.path.join(test_output, "*_summary.xml")):
            logger.debug('removing ' + f)
            os.remove(f)
        logger.debug("Copy all files from %s to %s" % (outdir, test_output))
        Copy.copyGlobFiles(outdir + '/*', test_output)


def Debug(root):
    print('==============================')
    print('      Enter JTouchstone')
    print('==============================')

    java = getJava(root)
    jtouchstone = getJTouchstoneBinary(root)
    cwd = getWorkingDriectory(root, jtouchstone)
    classpath = getClassPath(root, jtouchstone)
    opt = getJavaOpt(root)
    jtouchstoneclass = getJtouchstoneClass(root)
    envFile = getEnv(root)
    suites = list(root)
    for suite in suites:
        suiteFile = suite.text
        output, _, _ = getOutputPath(suite, cwd)
        command = getJTouchstoneCommand(java, classpath, opt, jtouchstoneclass, envFile, suiteFile, output)
        logger.info(command)


def getJava(root):
    try:
        default = os.environ['BOOSTER_VAR_JAVAEXE']
    except KeyError:
        logger.error('default java is not set')
        default = 'java'
    java = root.attrib.get('javaexe', default)
    return java


def getJTouchstoneBinary(root):
    try:
        default = os.environ['BOOSTER_VAR_JTOUCHSTONEBINARY']
    except KeyError:
        logger.error('default jtouchstone binary is not set')
        default = 'JTouchstone.jar'
    jtouchstone = root.attrib.get('jtouchstone', default)
    os.umask(000)
    os.chmod(jtouchstone, 0o777)
    return jtouchstone


def getWorkingDriectory(root, jtouchstone):
    cwd = root.attrib.get('cwd', 'undef')
    if cwd != 'undef':
        return cwd
    elif os.path.dirname(jtouchstone) != '':
        return os.path.dirname(jtouchstone)
    else:
        return os.getcwd()


def getClassPath(root, jtouchstone):
    driver = root.attrib.get('driver', '')
    if os.name == 'nt':
        connector = ';'
    else:
        connector = ':'
    try:
        default = os.path.basename(jtouchstone) + connector + os.environ['BOOSTER_VAR_JTOUCHSTONE_CLASSPATH'] + connector + driver
    except KeyError:
        default = os.path.basename(jtouchstone) + connector + '"./*"' + connector + driver
    classpath = root.attrib.get('classpath', default)
    return classpath


def getJavaOpt(root):
    try:
        default = os.environ['BOOSTER_VAR_JTOUCHSTONE_OPT']
    except KeyError:
        logger.error('default java runtime option is not set')
        default = '-ea -Dfile.encoding=UTF-8'
    opt = root.attrib.get('opt', default)
    return opt


def getJtouchstoneClass(root):
    try:
        default = os.environ['BOOSTER_VAR_JTOUCHSTONE_CLASS']
    except KeyError:
        logger.error('default Jtouchstone class is not set')
        default = 'com.simba.testframework.framework.JTouchstone'
    jtouchstoneclass = root.attrib.get('jtouchstoneclass', default)
    return jtouchstoneclass


def getEnv(root):
    env = root.attrib.get('env', 'undef')
    if env == 'undef':
        logger.error('Test Env not defined')
        raise Exception('Test Env not defined')
    return env


def getOutputPath(suite, cwd):
    testsuite = suite.text
    output = os.path.basename(testsuite)[:-4]
    outputPrefix = suite.attrib.get('output_prefix', '')
    outputSuffix = suite.attrib.get('output_suffix', '')
    outputDir = cwd + '/test_output'
    outputName = outputDir + '/' + outputPrefix + output + outputSuffix
    logPath = outputName + '.log'
    if not os.path.isdir(outputDir):
        os.umask(000)
        os.makedirs(outputDir, 0o777)
    return outputDir, outputName, logPath


def fixDriverCalss(root, env, suite):
    driverclass = root.attrib.get('driverclass', 'default')
    if driverclass != 'default':
        oldString = '<Driver>.*</Driver>'
        newString = '<Driver>' + driverclass + '</Driver>'
        ReplaceInFile.replace(env, oldString, newString, 'True')
        ReplaceInFile.replace(suite, oldString, newString, 'True')


def fixConnectionString(root, env, suite):
    connectionstring = root.attrib.get('connectionstring', 'default')
    if connectionstring != 'default':
        oldString = '<ConnectionString>.*</ConnectionString>'
        newString = '<ConnectionString>' + connectionstring + '</ConnectionString>'
        ReplaceInFile.replace(env, oldString, newString, 'True')
        ReplaceInFile.replace(suite, oldString, newString, 'True')


def fixResultSetsDir(env, suite):
    oldString = '>.*ResultSets/'
    suiteDir = os.path.dirname(suite)
    resultDir = suiteDir + '/ResultSets/'
    newString = '>' + resultDir
    logger.info('Fixing result set path')
    logger.info(oldString + ' => ' + newString)
    ReplaceInFile.replace(env, oldString, newString, 'True')
    ReplaceInFile.replace(suite, oldString, newString, 'True')

    oldString = '>.*ResultSets<'
    suiteDir = os.path.dirname(suite)
    resultDir = suiteDir + '/ResultSets<'
    newString = '>' + resultDir
    logger.info('Fixing result set path')
    logger.info(oldString + ' => ' + newString)
    ReplaceInFile.replace(env, oldString, newString, 'True')
    ReplaceInFile.replace(suite, oldString, newString, 'True')


def fixTestSetsDir(suite):
    oldString = 'SetFile=".*TestSets'
    suiteDir = os.path.dirname(suite)
    testsetsDir = suiteDir + '/TestSets'
    if os.path.exists(testsetsDir):
        newString = 'SetFile="' + testsetsDir
        logger.info('Fixing test set path')
        logger.info(oldString + ' => ' + newString)
        ReplaceInFile.replace(suite, oldString, newString, 'True')
    else:
        logger.warning(testsetsDir + ' does not exist, use test sets from Touchstone')


def getJTouchstoneCommand(java, classpath, opt, jtouchstoneclass, envFile, suiteFile, output):
    command = java + ' -classpath ' + classpath + ' ' + opt + ' ' + jtouchstoneclass + ' ' + '-te ' + envFile + ' -ts ' + suiteFile + ' -o ' + output
    return command
