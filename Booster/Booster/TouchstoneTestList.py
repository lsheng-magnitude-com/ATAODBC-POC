from __future__ import print_function

import glob
import os
import re

from collections import namedtuple
import Copy
import ReplaceInFile
import TouchstoneMonitor
import ata.log

logger = ata.log.AtaLog(__name__)

_bamboo_working_directory_cleaned = False
def CopyTouchstoneOutputToDestination(outdir):
    Copy.copyGlobFiles(outdir + '/*', os.getcwd() + '/log/test_output/')

    # The following is a temporary solution so the JUnit bamboo task can find the results for current plans with
    # multiple checkout directories
    # These lines can be removed once the plans are updated to only use Booster's checkout directory
    if 'BAMBOO_WORKING_DIRECTORY' in os.environ:
        working_dir = os.environ['BAMBOO_WORKING_DIRECTORY']
        test_output = os.path.join(working_dir, 'log', 'test_output')
        
        global _bamboo_working_directory_cleaned
        if not _bamboo_working_directory_cleaned:
            # Cleanup the directory first so we don't copy old results
            logger.debug('test_output ' + test_output)
            for f in glob.glob(os.path.join(test_output, "*_summary.xml")):
                logger.debug('removing ' + f)
                os.remove(f)
            _bamboo_working_directory_cleaned = True
        logger.debug("Copy all files from %s to %s" % (outdir, test_output))
        Copy.copyGlobFiles(outdir + '/*', test_output)

def RunOneTestSuite(envFile, suiteFile, outputPrefix, touchstoneBinary, cwd=None, outdir=None, connectionstring=None, toolPrefix=None, dm_encoding=None, dsLocator=None, isDebug=False):
    if not os.path.exists(suiteFile):
        return False
        
    cwd = getWorkingDirectory(cwd, touchstoneBinary)
    if outdir is not None:
        outdir = cwd + '/test_output'
        
    if not isDebug:
        fixDMEncoding(envFile, dm_encoding)
        fixConnectionString(connectionstring, envFile, suiteFile)
        fixResultSetsDir(envFile, suiteFile)
        fixTestSetsDir(suiteFile)
        setSchemaMapDir(envFile, suiteFile, cwd)
        setSSLCertificatesDir(envFile, suiteFile, cwd)
        setDataSourceLocator(envFile, suiteFile, dsLocator)
        
    testoutput, log = getOutputPath(outputPrefix, outdir)
    memoryToolPrefix = fixMemoryTestPrefix(toolPrefix, outdir, outputPrefix)
    touchstone = getTouchstoneExeCommand(touchstoneBinary, memoryToolPrefix)
    abort, abort_reason = runTouchstoneMonitor(touchstone, cwd, envFile, suiteFile, testoutput, isDebug)
    if abort:
        raise AssertionError(abort_reason)
    
    return True

def _doExecute(root, isDebug):
    print('====================================')
    print('      Enter TouchstoneTestList')
    print('====================================')
    toolPrefix = getTouchstoneCommandPrefix()
    touchstoneBinary = getTouchstoneBinary(root)
    dm_encoding = getDMEncoding(root)
    cwd = getWorkingDirectory(root.attrib.get('cwd'), touchstoneBinary)
    outdir = cwd + '/test_output'
    connectionstring = root.attrib.get('connectionstring')
    datasourceLocator = None
    if 'true' == root.find('Locator').attrib.get('enable', 'true'):
        datasourceLocator = root.find('Locator').text
    testLists = getTestLists(cwd, root)
    if not testLists:
        print('No test list found')
    else:
        print('Executing testlists:')
        print(testLists)

        try:
            for testListName in testLists:
                testListFile = cwd + '/Tests/TouchstoneTestLists/' + testListName
                testfileList = getTestFiles(cwd, testListFile)

                if not testfileList:
                    print('No test file in ' + testListName)
                else:
                    for envFile, suiteFile, suiteOutput in testfileList:
                        if not RunOneTestSuite(envFile, suiteFile, suiteOutput, touchstoneBinary, cwd, outdir, connectionstring, toolPrefix, dm_encoding, datasourceLocator, isDebug):
                            print('Can not find ' + suiteFile)
        except AssertionError as err:
            print(err)

        if not isDebug:
            CopyTouchstoneOutputToDestination(outdir)

def Execute(root):
    _doExecute(root, False)
    
def Debug(root):
    _doExecute(root, True)

def getTestLists(cwd, root):
    testListFiles = root.find('TestList').text
    dataSourceVersion = root.findtext('DataSourceVersion')
    fileLists = []
    if testListFiles == 'all' or testListFiles == '' or testListFiles is None:
        if dataSourceVersion == 'default' or dataSourceVersion == '' or dataSourceVersion is None:
            for file in glob.glob(cwd + '/Tests/TouchstoneTestLists/*.testsuitelist'):
                fileLists.append(os.path.basename(file))
        else:
            for file in glob.glob(cwd + '/Tests/TouchstoneTestLists/*' + dataSourceVersion + '.testsuitelist'):
                fileLists.append(os.path.basename(file))
    else:
        for file in testListFiles.split(','):
            fileLists.append(file + '.testsuitelist')
    return fileLists


def getTestFiles(cwd, testListFile):
    fileList = []
    with open(testListFile, 'r') as fhandle:
        for line in fhandle:
            line = line.strip()
            lineArrary = line.split(',')
            if len(lineArrary) == 1:
                envFile = cwd + '/Tests/Envs/TestEnv.xml'
                suiteFile = cwd + '/Tests/TestDefinitions/' + lineArrary[0].strip() + '.xml'
                outputFile = lineArrary[0].strip().replace('/', '_')
            if len(lineArrary) == 2:
                envFile = cwd + '/Tests/Envs/' + lineArrary[0].strip() + '.xml'
                suiteFile = cwd + '/Tests/TestDefinitions/' + lineArrary[1].strip() + '.xml'
                outputFile = lineArrary[0].strip() + '_' + lineArrary[1].strip().replace('/', '_')
            fileList.append((envFile, suiteFile, outputFile))
    return fileList


def getTouchstoneBinary(root):
    default = os.environ.get('BOOSTER_VAR_TOUCHSTONEBINARY', 'Touchstone')
    touchstoneBinary = root.attrib.get('touchstone', default)
    os.umask(000)
    os.chmod(touchstoneBinary, 0o777)
    return touchstoneBinary


def getTouchstoneExeCommand(touchstoneBinary, toolPrefix):
    if toolPrefix is not None:
        touchstone = toolPrefix + touchstoneBinary
    else:
        touchstone = touchstoneBinary
    return touchstone


def getTouchstoneCommandPrefix():
    return os.environ.get('TOUCHSTONE_COMMAND_PREFIX', None)


def fixMemoryTestPrefix(toolPrefix, outdir, suiteOutput):
    placeholder = '[memorytestlogdir]'
    if toolPrefix is not None and placeholder in toolPrefix:
        os.makedirs(outdir + '/memoryReport/' + suiteOutput, 0o777)
        return toolPrefix.replace(placeholder, suiteOutput)
    else:
        return toolPrefix


def getDMEncoding(root):
    encoding = root.attrib.get('dm_encoding')
    return encoding


def getWorkingDirectory(cwd, touchstone):
    if cwd is not None:
        return cwd
    elif os.path.dirname(touchstone) != '':
        return os.path.dirname(touchstone)
    else:
        return os.getcwd()


def getOutputPath(suiteOutput, outputDir):
    outputName = outputDir + '/' + suiteOutput
    logPath = outputName + '.log'
    if not os.path.isdir(outputDir):
        os.umask(000)
        os.makedirs(outputDir, 0o777)
    return outputName, logPath


def fixDMEncoding(file, encoding):
    if encoding is not None:
        oldString = '<SqlWCharEncoding>([^<]+)</SqlWCharEncoding>'
        newString = '<SqlWCharEncoding>' + encoding + '</SqlWCharEncoding>'
        ReplaceInFile.replace(file, oldString, newString, re_flags=re.IGNORECASE)


def fixConnectionString(connectionString, env, suite):
    if connectionString is not None:
        oldString = '<ConnectionString>([^<]+)</ConnectionString>'
        newString = '<ConnectionString>' + connectionString + '</ConnectionString>'
        ReplaceInFile.replace(env, oldString, newString, re_flags=re.IGNORECASE)
        ReplaceInFile.replace(suite, oldString, newString, re_flags=re.IGNORECASE)


def fixResultSetsDir(env, suite):
    oldString = '>.*ResultSets/'
    suiteDir = os.path.dirname(suite)
    resultDir = suiteDir + '/ResultSets/'
    newString = '>' + resultDir
    logger.debug('Fixing result set path')
    logger.debug(oldString + ' => ' + newString)
    ReplaceInFile.replace(env, oldString, newString, 'True')
    ReplaceInFile.replace(suite, oldString, newString, 'True')

    oldString = '>.*ResultSets<'
    suiteDir = os.path.dirname(suite)
    resultDir = suiteDir + '/ResultSets'
    newString = '>' + resultDir + '<'
    # print('Fixing result set path')
    logger.debug('Fixing result set path')
    # print(oldString + ' => ' + newString)
    logger.debug(oldString + ' => ' + newString)
    ReplaceInFile.replace(env, oldString, newString, 'True')
    ReplaceInFile.replace(suite, oldString, newString, 'True')


def fixTestSetsDir(suite):
    oldString = 'SetFile="([^<]+)TestSets'
    suiteDir = os.path.dirname(suite)
    testsetsDir = suiteDir + '/TestSets'
    if os.path.exists(testsetsDir):
        newString = 'SetFile="' + testsetsDir
        logger.debug('Fixing result set path')
        logger.debug(oldString + ' => ' + newString)
        ReplaceInFile.replace(suite, oldString, newString, 'True')
    else:
        logger.warning(testsetsDir + ' does not exist, use test sets from Touchstone')


def setDataSourceLocator(env, suite, datasourceLocator):
    if datasourceLocator is not None:
        ds_values = datasourceLocator.split(',')
        ds_dict = {}
        for value in ds_values:
            k, v = value.split("=", 1)
            ds_dict[k] = v
        for key in ds_dict:
            ReplaceInFile.replace(env, "$(%s)" % key, ds_dict[key])
            ReplaceInFile.replace(suite, "$(%s)" % key, ds_dict[key])
            logger.info("replace the key: " + key + " with value: " + ds_dict[key])


def setSchemaMapDir(env, suite, cwd):
    SchemaFileDir = cwd + '/Tests/TestDefinitions/SchemaMap'
    ReplaceInFile.replace(env, "[schemaMapDir]", SchemaFileDir)
    ReplaceInFile.replace(suite, "[schemaMapDir]", SchemaFileDir)
    logger.info("Set  schemaMapDir:  " + SchemaFileDir)


def setSSLCertificatesDir(env, suite, cwd):
    SSLCertificatesDir = cwd + '/Tests'
    ReplaceInFile.replace(env, "[SSLDir]", SSLCertificatesDir)
    ReplaceInFile.replace(suite, "[SSLDir]", SSLCertificatesDir)
    logger.info("Set  SSLCertificatesDir:  " + SSLCertificatesDir)


def runTouchstoneMonitor(touchstone, cwd, env, suite, output, isDebug):
    monitor_args = {
        "outputPrefix": output,
        "testSuite": suite,
        "testEnv": env,
        "wd": cwd,
        "touchstone": touchstone
    }
    
    if isDebug:
        logger.info("monitor_args =" + str(monitor_args))
        abort = None
        abort_reason = None
    else:
        abort, abort_reason = TouchstoneMonitor.TouchstoneMonitor(**monitor_args).run()
    return abort, abort_reason
