from __future__ import print_function
import glob
import os
import Copy
import ReplaceInFile
import TouchstoneMonitor
import ata.log

logger = ata.log.AtaLog(__name__)


def Execute(root):
    print('==============================')
    print('      Enter Touchstone')
    print('==============================')

    touchstone = getTouchstoneBinary(root)
    dm_encoding = getDMEncoding(root)
    cwd = getWorkingDriectory(root, touchstone)
    touchstoneScript = getTouchstoneScript(cwd)
    envFile = getEnv(root)
    if not os.path.exists(envFile):
        print('Can not find ' + envFile)
        return
    fixDMEncoding(envFile, dm_encoding)
    suites = list(root)
    outdir = cwd
    for suite in suites:
        suiteFile = suite.text
        if os.path.exists(suiteFile):
            suiteFile = suite.text
            fixResultSetsDir(envFile, suiteFile)
            fixTestSetsDir(suiteFile)
            (outdir, output, log) = getOutputPath(suite, cwd)
            runTouchstoneMonitor(touchstone, cwd, envFile, suiteFile, output)
        else:
            print('Can not find ' + suiteFile)
    # TODO - outdir is changing in the loop
    Copy.copyGlobFiles(outdir + '/*', os.getcwd() + '/log/test_output/')

    # The following is a temporary solution so the JUnit bamboo task can find the results for current plans with
    # multiple checkout directories
    # These lines can be removed once the plans are updated to only use Booster's checkout directory
    if 'BAMBOO_WORKING_DIRECTORY' in os.environ:
        working_dir = os.environ['BAMBOO_WORKING_DIRECTORY']
        test_output = os.path.join(working_dir, 'log', 'test_output')
        # Cleanup the directory first so we don't copy old results
        # print('test_output', test_output)
        logger.debug('test_output ' + test_output)
        for f in glob.glob(os.path.join(test_output, "*_summary.xml")):
            # print('removing', f)
            logger.debug('removing ' + f)
            os.remove(f)
        logger.debug("Copy all files from %s to %s" % (outdir, test_output))
        Copy.copyGlobFiles(outdir + '/*', test_output)


def Debug(root):
    print('==============================')
    print('      Enter Touchstone')
    print('==============================')

    touchstone = getTouchstoneBinary(root)
    cwd = getWorkingDriectory(root, touchstone)
    touchstoneScript = getTouchstoneScript(cwd)
    envFile = getEnv(root)
    suites = list(root)
    for suite in suites:
        suiteFile = suite.text + '.xml'
        output, _, _ = getOutputPath(suite, cwd)
        command = getTouchstoneCommand(touchstoneScript, touchstone, cwd, envFile, suiteFile, output)
        print(command)


def getTouchstoneBinary(root):
    touchstone = root.attrib.get('touchstone', 'Touchstone')
    os.umask(000)
    os.chmod(touchstone, 0o777)
    return touchstone


def getDMEncoding(root):
    encoding = root.attrib.get('dm_encoding', 'UTF-16')
    return encoding


def getTouchstoneScript(cwd):
    touchstoneScript = cwd + '/Touchstone_Server.pl'
    return touchstoneScript


def getWorkingDriectory(root, touchstone):
    cwd = root.attrib.get('cwd')
    if cwd is not None:
        return cwd
    elif os.path.dirname(touchstone) != '':
        return os.path.dirname(touchstone)
    else:
        return os.getcwd()


def getEnv(root):
    env = root.attrib.get('env', 'undef')
    if env == 'undef':
        print('Test Env not defined')
        raise Exception('Test Env Undefined')
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
    print('Fixing result set path')
    print(oldString + ' => ' + newString)
    ReplaceInFile.replace(env, oldString, newString, 'True')
    ReplaceInFile.replace(suite, oldString, newString, 'True')

    oldString = '>.*ResultSets<'
    suiteDir = os.path.dirname(suite)
    resultDir = suiteDir + '/ResultSets'
    newString = '>' + resultDir + '<'
    print('Fixing result set path')
    print(oldString + ' => ' + newString)
    ReplaceInFile.replace(env, oldString, newString, 'True')
    ReplaceInFile.replace(suite, oldString, newString, 'True')


def fixTestSetsDir(suite):
    oldString = 'SetFile=".*TestSets'
    suiteDir = os.path.dirname(suite)
    testsetsDir = suiteDir + '/TestSets'
    if os.path.exists(testsetsDir):
        newString = 'SetFile="' + testsetsDir
        print('Fixing test set path')
        print(oldString + ' => ' + newString)
        ReplaceInFile.replace(suite, oldString, newString, 'True')
    else:
        print(testsetsDir + ' does not exist, use test sets from Touchstone')


def getTouchstoneCommand(touchstoneScript, touchstone, cwd, env, suite, output):
    command = 'perl ' + touchstoneScript + ' ' + touchstone + ' ' + cwd + ' ' + env + ' ' + suite + ' 8080 ' + output
    return command


def runTouchstoneMonitor(touchstone, cwd, env, suite, output):
    monitor_args = {
        "outputPrefix": output,
        "testSuite": suite,
        "testEnv": env,
        "wd": cwd,
        "touchstone": touchstone
    }
    TouchstoneMonitor.TouchstoneMonitor(**monitor_args).run()
