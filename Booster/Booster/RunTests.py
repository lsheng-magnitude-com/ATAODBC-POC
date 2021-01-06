from __future__ import print_function

import glob
import os
import stat
import traceback

import AtaUtil
import ata.log as ataloggers
import Copy
import ReplaceInFile
import TouchstoneMonitor

DEFAULT_TEST_ENV_VAR = 'BAMBOO_TESTSUITE_LIST'


def _doExecute(root, isDebug):
    print('==============================')
    print('      Enter RunTests')
    print('==============================')
    touchstone = getTouchstoneBinary()
    dm_encoding = getDMEncoding(root)
    cwd = getWorkingDriectory(root, touchstone)
    testdefinitions = os.environ['TESTDEFINITIONS_DIR']
    ds_locator = root.find('locator').text
    test_files = getTestFiles()

    for test in test_files:
        env, testsuitelist = test
        testsuites = []
        with open(testsuitelist, 'r') as fhandle:
            for line in fhandle:
                testsuites.append(line.strip())
        if not testsuites:
            #print('Cannot find test suite lists for env %s' % env)
            ataloggers.err_logger.warning('Cannot find test suite lists for env %s' % env)
            continue
        fixDMEncoding(env, dm_encoding)
        replaceDsVariables(env, ds_locator)
        for suite_file in testsuites:
            output_prefix=suite_file.split('/')[0]
            suite_file=testdefinitions + "/" + suite_file + ".xml"
            replaceDsVariables(suite_file, ds_locator)
            fixResultSetsDir(env, suite_file)
            fixTestSetsDir(suite_file)
            (outdir, output, log) = getOutputPath(root, suite_file, cwd,output_prefix)
            runTouchstoneMonitor(touchstone, cwd, env, suite_file, output, isDebug)
            if not isDebug:
                Copy.copyGlobFiles(outdir + '/*', os.getcwd() + '/log/test_output/')
                
    if not isDebug:
        # The following is a temporary solution so the JUnit bamboo task can find the results for current plans with
        # multiple checkout directories
        # These lines can be removed once the plans are updated to only use Booster's checkout directory
        if 'BAMBOO_WORKING_DIRECTORY' in os.environ:
            working_dir = os.environ['BAMBOO_WORKING_DIRECTORY']
            test_output = os.path.join(working_dir, 'log', 'test_output')
            # Cleanup the directory first so we don't copy old results
            #print('test_output', test_output)
            ataloggers.logger.debug('test_output ' + test_output)
            for f in glob.glob(os.path.join(test_output, "*_summary.xml")):
                #print('removing', f)
                ataloggers.logger.debug('removing ' + f)
                os.remove(f)
            ataloggers.logger.debug("Copy all files from %s to %s" % (outdir, test_output))
            Copy.copyGlobFiles(outdir + '/*', test_output)

def Execute(root):
    _doExecute(root, False)
    
def Debug(root):
    _doExecute(root, True)
        
def getTestFiles():
    if DEFAULT_TEST_ENV_VAR in os.environ and os.environ[DEFAULT_TEST_ENV_VAR] is not None and \
                    os.environ[DEFAULT_TEST_ENV_VAR] != '':
        test_files = []
        for subset in os.environ[DEFAULT_TEST_ENV_VAR].split(','):
            env_file = "%s/%s.xml" % (os.environ['TESTENV_DIR'], subset)
            test_file = "%s/%s.testsuitelist" % (os.environ['TESTSUITE_LIST_DIR'], subset)
            test_files.append((env_file, test_file))
        return test_files
    else:
        return [(os.environ['TESTENV'], os.environ['TESTSUITELIST'])]

def getTouchstoneBinary():
    touchstone = os.environ['TOUCHSTONE_BIN']
    # Set the permissions as rx for owner and x for everyone else
    permissions = stat.S_IREAD | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH
    os.chmod(touchstone, permissions)
    return touchstone


def getDMEncoding(root):
    encoding = root.attrib.get('dm_encoding', '')
    return encoding


def getWorkingDriectory(root, touchstone):
    cwd = root.attrib.get('cwd', 'undef')
    if cwd != 'undef':
        return cwd
    elif os.path.dirname(touchstone) != '':
        return os.path.dirname(touchstone)
    else:
        return os.getcwd()


def getOutputPath(root, testsuite, cwd,output_prefix):
    output = os.path.basename(testsuite)[:-4]
    outputPrefix = output_prefix+'_'
    outputSuffix = root.attrib.get('output_suffix', '')
    outputDir = cwd + '/test_output'
    outputName = outputDir + '/' + outputPrefix + output + outputSuffix
    logPath = outputName + '.log'
    if not os.path.isdir(outputDir):
        os.umask(000)
        os.makedirs(outputDir, 0o777)
    return outputDir, outputName, logPath


def fixDMEncoding(file, encoding):
    oldString_upper = '<SqlWCharEncoding>([^<]+)</SqlWCharEncoding>'
    oldString_lower = '<SqlWcharEncoding>([^<]+)</SqlWcharEncoding>'
    newString = '<SqlWCharEncoding>' + encoding + '</SqlWCharEncoding>'
    ReplaceInFile.replace(file, oldString_upper, newString, 'True')
    ReplaceInFile.replace(file, oldString_lower, newString, 'True')


def fixResultSetsDir(env, suite):
    oldString = '>.*ResultSets/'
    suiteDir = os.path.dirname(suite)
    resultDir = suiteDir + '/ResultSets/'
    newString = '>' + resultDir
    ataloggers.logger.debug('Fixing result set path')
    ataloggers.logger.debug(oldString + ' => ' + newString)
    ReplaceInFile.replace(env, oldString, newString, 'True')
    ReplaceInFile.replace(suite, oldString, newString, 'True')

    oldString = '>.*ResultSets<'
    suiteDir = os.path.dirname(suite)
    resultDir = suiteDir + '/ResultSets'
    newString = '>' + resultDir + '<'
    #print('Fixing result set path')
    ataloggers.logger.debug('Fixing result set path')
    #print(oldString + ' => ' + newString)
    ataloggers.logger.debug(oldString + ' => ' + newString)
    ReplaceInFile.replace(env, oldString, newString, 'True')
    ReplaceInFile.replace(suite, oldString, newString, 'True')


def fixTestSetsDir(suite):
    oldString = 'SetFile="([^<]+)TestSets'
    suiteDir = os.path.dirname(suite)
    testsetsDir = suiteDir + '/TestSets'
    if os.path.exists(testsetsDir):
        newString = 'SetFile="' + testsetsDir
        #print('Fixing test set path')
        ataloggers.logger.debug('Fixing result set path')
        #print(oldString + ' => ' + newString)
        ataloggers.logger.debug(oldString + ' => ' + newString)
        ReplaceInFile.replace(suite, oldString, newString, 'True')
    else:
        #print(testsetsDir + ' does not exist, use test sets from Touchstone')
        ataloggers.err_logger.warning(testsetsDir + ' does not exist, use test sets from Touchstone')

def replaceDsVariables(env, locator):
    if locator:
        ds_values = locator.split(',')
        ds_dict = {}
        for value in ds_values:
            k, v = value.split("=")
            ds_dict[k] = v
        for key in ds_dict:
            ReplaceInFile.replace(env, "$(%s)" % key, ds_dict[key])
            ataloggers.logger.info("replace the key: " + key + " with value: " + ds_dict[key])
        SchemaFileDir = os.environ['TESTDEFINITIONS_DIR'] + "/SchemaMap"
        ReplaceInFile.replace(env, "[schemaMapDir]", SchemaFileDir)
        ataloggers.logger.info("This file will be replaced: "+env)
        ataloggers.logger.info("SchemaFileDir is from:  " + SchemaFileDir)


def runTouchstoneMonitor(touchstone, cwd, env, suite, output, isDebug):
    monitor_args = {
        "outputPrefix": output,
        "testSuite": suite,
        "testEnv": env,
        "wd": cwd,
        "touchstone": touchstone
    }
    
    if isDebug:
        ataloggers.logger.debug('monitor_args = ' + str(monitor_args))
    else:
        TouchstoneMonitor.run(monitor_args)
