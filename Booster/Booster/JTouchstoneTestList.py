import glob
import os
import re

import Command
import Copy
import ReplaceInFile
import ata.log
from Booster.Debug import Debug as Debugger

logger = ata.log.AtaLog(__name__)

defaults = {
    'test_list_path': 'Tests/TouchstoneTestLists',
}

def _doExecute(root, isDebug):
    print('=====================================')
    print('      Enter JTouchstoneTestList')
    print('=====================================')

    dbg = Debugger()
    java = getJava(root)
    jtouchstone = getJTouchstoneBinary(root)
    cwd = getWorkingDriectory(root, jtouchstone)
    classpath = getClassPath(root, jtouchstone)
    opt = getJavaOpt(root)
    jtouchstoneclass = getJtouchstoneClass(root)
    datasourceLocator = root.find('Locator').text
    (loglevel,logpath) = getTracelogSettings(cwd)
    enableLocator = root.find('Locator').attrib.get('enable', 'true')
    testLists = getTestLists(cwd, root)

    if not testLists:
        logger.warning('No test list found')
    else:
        logger.info('Executing testlists:')
        logger.info(testLists)

        outdir = cwd
        testListPath = root.attrib.get('testlistpath', defaults['test_list_path'])
        for testListName in testLists:
            testListFile = '{cwd}/{path}/{file}'.format(cwd=cwd, path=testListPath, file=testListName)
            testfileList = getTestFiles(cwd, testListFile)

            if not testfileList:
                logger.warning('No test suite in ' + testListName)
            else:
                for envFile, suiteFile, suiteOutput in testfileList:
                    if os.path.exists(suiteFile):
                        fixDriverCalss(root, envFile, suiteFile)
                        fixConnectionString(root, envFile, suiteFile)
                        fixResultSetsDir(root, envFile, suiteFile)
                        fixTestSetsDir(root, suiteFile)
                        setSchemaMapDir(envFile, suiteFile, cwd)
                        setDataSourceLocator(envFile, suiteFile, datasourceLocator, enableLocator)
                        setTraceLog(envFile, suiteFile, loglevel, logpath)
                        (outdir, testoutput, log) = getOutputPath(suiteOutput, cwd)
                        command = getJTouchstoneCommand(java, classpath, opt, jtouchstoneclass, envFile, suiteFile,
                                                        testoutput)
                        if dbg.skip('jts', 'skip jtouchstone\n{}'.format(command)):
                            continue
                        Command.ExecuteAndTail(command, log, checkreturncode=False, cwd=cwd, isDebug=isDebug)
                    else:
                        logger.warning('Can not find ' + suiteFile)
        if not isDebug:
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

def Execute(root):
    _doExecute(root, False)
    
def Debug(root):
    _doExecute(root, True)

def getTestLists(cwd, root):
    """
    parse test list from //TestList@text
     or
    glob test list files from Tests/TouchstoneTestsLists/
    by ds source and jdbc version
    :param cwd:
    :param root:
    :return:            list of test-list files
    """
    testListFiles = root.find('TestList').text
    fileLists = []
    dataSourceVersion = root.findtext('DataSourceVersion')
    testListPath = root.attrib.get('testlistpath', defaults['test_list_path'])
    if testListFiles == 'all' or testListFiles == '' or testListFiles is None:
        dsv_prefix = ''
        if not (dataSourceVersion is None or dataSourceVersion == 'default' or dataSourceVersion == ''):
            dsv_prefix = dataSourceVersion + '_'
        pattern = '{cwd}/{path}/{dsv}JDBC{jdbcv}{suffix}.testsuitelist'
        for suffix in ('', '_*'):
            gp = pattern.format(cwd=cwd, path=testListPath, dsv=dsv_prefix, jdbcv=os.environ['BOOSTER_VAR_JDBC_V'], suffix=suffix)
            logger.info('glob test list files: {pattern}'.format(pattern=gp))
            for file in glob.glob(gp):
                fileLists.append(os.path.basename(file))
    elif testListFiles == 'Smoke':
        fileLists.append('Smoke_JDBC' + os.environ['BOOSTER_VAR_JDBC_V'] + '.testsuitelist')
    else:
        for file in testListFiles.split(','):
            fileLists.append(file + '.testsuitelist')
    return fileLists


def getTestFiles(cwd, testListFile):
    """
    Parse test list file
    :param cwd:
    :param testListFile:
    :return:                    list of (env,suite,output)
    """
    fileList = []
    with open(testListFile, 'r') as fhandle:
        for line in fhandle:
            re.sub(r'#.*', '', line)        # strip comment and skip blank lines
            line = line.strip()
            if line == '': continue

            lineArrary = line.split(',')
            envFile, suiteFile, outputFile = 'JDBC' + os.environ['BOOSTER_VAR_JDBC_V'], None, None
            if len(lineArrary) == 1:
                suiteFile = lineArrary[0].strip()
                outputFile = suiteFile.replace('/', '_')
            elif len(lineArrary) == 2:
                envFile = lineArrary[0].strip()
                suiteFile = lineArrary[1].strip()
                outputFile = '{}_{}'.format(envFile, suiteFile.replace('/', '_'))
            else:
                envFile = lineArrary[0].strip()
                suiteFile = lineArrary[1].strip()
                outputFile = lineArrary[2].strip().replace('/', '_')

            fileList.append(('{}/Tests/Envs/{}.xml'.format(cwd, envFile),
                             '{}/Tests/TestDefinitions/{}.xml'.format(cwd, suiteFile),
                             outputFile))
    return fileList


def getJava(root):
    jre = os.environ.get('BOOSTER_VAR_JRE', 'undef').upper()
    if jre == 'undef':
        return java
    else:
        # global settings in cimpiler.settings
        jdk = jre.replace('JRE','JDK')
        bitness = os.environ.get('BOOSTER_VAR_BITNESS','64')
        if bitness == '64':
            javaHome=os.environ.get('BOOSTER_VAR_' + jdk + '_HOME', 'undef')
        else:
            javaHome = os.environ.get('BOOSTER_VAR_' + jdk + '_HOME32', 'undef')
        # if agent doesn't match global settings, give a warning and use capability
        if not os.path.exists(javaHome):
            logger.warning('standard java home does not exist, check capability')
            if bitness == '64':
                javaHome = os.environ.get('BAMBOO_CAPABILITY_SYSTEM_JDK_' + jdk + 'x64', os.environ.get('bamboo_capability_system_jdk_' + jdk + 'x64','undef'))
            else:
                javaHome = os.environ.get('BAMBOO_CAPABILITY_SYSTEM_JDK_' + jdk + 'x86', os.environ.get('bamboo_capability_system_jdk_' + jdk + 'x86','undef'))
        java = '"' + javaHome + '/bin/java' + '"'
        Command.ExecuteAndLogVerbose(java + ' -version')
        return java


def getJTouchstoneBinary(root):
    try:
        default = os.environ['BOOSTER_VAR_JTOUCHSTONEBINARY']
    except KeyError:
        default = 'JTouchstone.jar'
    jtouchstone = root.attrib.get('jtouchstone', default)
    os.umask(000)
    os.chmod(jtouchstone, 0o777)
    return jtouchstone


def getWorkingDriectory(root, jtouchstone):
    cwd = root.attrib.get('cwd')
    if cwd is not None:
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
        default = '-ea -Dfile.encoding=UTF-8'
    opt = root.attrib.get('opt', default)
    return opt


def getJtouchstoneClass(root):
    try:
        default = os.environ['BOOSTER_VAR_JTOUCHSTONE_CLASS']
    except KeyError:
        default = 'com.simba.testframework.framework.JTouchstone'
    jtouchstoneclass = root.attrib.get('jtouchstoneclass', default)
    return jtouchstoneclass


def getOutputPath(suiteOutput, cwd):
    outputDir = cwd + '/test_output'
    outputName = outputDir + '/' + suiteOutput
    logPath = outputName + '.log'
    if not os.path.isdir(outputDir):
        os.umask(000)
        os.makedirs(outputDir, 0o777)
    return outputDir, outputName, logPath

def getTracelogSettings(cwd):
    loglevel = os.environ.get('BOOSTER_VAR_LOG_LEVEL','0')
    logpath  = cwd + '/test_output'

    return loglevel,logpath


def fixDriverCalss(root, env, suite):
    driverclass = root.attrib.get('driverclass')
    if driverclass is not None:
        oldString = '<Driver>.*</Driver>'
        newString = '<Driver>' + driverclass + '</Driver>'
        ReplaceInFile.replace(env, oldString, newString, 'True')
        ReplaceInFile.replace(suite, oldString, newString, 'True')


def fixConnectionString(root, env, suite):
    connectionstring = root.attrib.get('connectionstring')
    if connectionstring is not None:
        oldString = '<ConnectionString>.*</ConnectionString>'
        newString = '<ConnectionString>' + connectionstring + '</ConnectionString>'
        ReplaceInFile.replace(env, oldString, newString, 'True')
        ReplaceInFile.replace(suite, oldString, newString, 'True')


def fixResultSetsDir(root, env, suite):
    fixpath = root.attrib.get('fixresultsets', 'true')
    if fixpath.lower() != 'false':  # fix by default
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


def fixTestSetsDir(root, suite):
    fixpath = root.attrib.get('fixtestset', 'true')
    if fixpath.lower() != 'false':      # fix by default
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


def setDataSourceLocator(envFile, suiteFile, datasourceLocator, enableLocator):
    if enableLocator == 'true':
        ds_values = datasourceLocator.split(',')
        ds_dict = {}
        for value in ds_values:
            p = value.split("=")
            if len(p) == 2:
                k = p[0].strip()
                v = p[1].strip()
                ds_dict[k] = v
        for k,v in ds_dict.iteritems():
            ReplaceInFile.replace(envFile, "$({key})".format(key=k), v)
            ReplaceInFile.replace(suiteFile, "$({key})".format(key=k), v)
            logger.info("replace the key: " + k + " with value: " + v)


def setTraceLog(envFile, suiteFile, loglevel, logpath):
    ReplaceInFile.replace(envFile, "[LOGLEVEL]", loglevel)
    ReplaceInFile.replace(envFile, "[LOGPATH]", logpath)
    ReplaceInFile.replace(suiteFile, "[LOGLEVEL]", loglevel)
    ReplaceInFile.replace(suiteFile, "[LOGPATH]", logpath)



def setSchemaMapDir(env, suite, cwd):
    SchemaFileDir = cwd + '/Tests/TestDefinitions/SchemaMap'
    ReplaceInFile.replace(env, "[schemaMapDir]", SchemaFileDir)
    ReplaceInFile.replace(suite, "[schemaMapDir]", SchemaFileDir)
    logger.info("Set  schemaMapDir:  " + SchemaFileDir)


def getJTouchstoneCommand(java, classpath, opt, jtouchstoneclass, envFile, suiteFile, output):
    command = java + ' -classpath ' + classpath + ' ' + opt + ' ' + jtouchstoneclass + ' ' + '-te ' + envFile + ' -ts ' + suiteFile + ' -o ' + output
    return command
