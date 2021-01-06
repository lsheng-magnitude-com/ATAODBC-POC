from __future__ import print_function
import os
import ReplaceInFile
import ata.log
import SSH
import Docker
import Command

try:
    import YAML
except:
    pass

logger = ata.log.AtaLog(__name__)


def _doExecute(root, isDebug):
    print('====================================')
    print('        Enter PerfTestList')
    print('====================================')

    cwd = getcwd(root)
    docker = getDocker(root)
    testListFile = getTestList(cwd, root)
    print("Finish getTestList")
    testinfo_dict = getTestInfo(testListFile)
    print("Finish getTestInfo")
    tests = getTests(testinfo_dict)
    print("Finish getTests")
    if docker == 'true':
        (host, sshKey, dockerPullCmd, dockerRunCmd, dsCheckScript) = getHostInfo(root, testinfo_dict)
        print("Finish getHostInfo")
        startHost(cwd, host, sshKey, dockerPullCmd, dockerRunCmd, dsCheckScript, isDebug)
    for test in tests:
        testsuite = getTestSuite(test)
        # dumpBambooVarToTestFile(cwd, testsuite)
        connection = getConnection(root, test)
        runPerfTest(cwd, testsuite, connection, isDebug)
    if not isDebug and docker == 'true':
        stopHost(host, sshKey)


def Execute(root):
    _doExecute(root, False)


def Debug(root):
    _doExecute(root, True)


def getcwd(root):
    return root.attrib.get('cwd', os.environ['BOOSTER_VAR_STAGING_DIR'])


def getDocker(root):
    return root.attrib.get('docker', 'true')


def getTestList(cwd, root):
    print("------------------")
    testList = root.findtext('TestList')
    if os.path.isfile(cwd + '/' + testList + '.yaml'):
        testListFilePath = cwd + '/' + testList + '.yaml'
    else:
        testListFilePath = cwd + "/drv/PerfTest/TestSuiteList/" + testList + '.yaml'
    return testListFilePath


def getTestInfo(testListFile):
    return YAML.YAML(testListFile)._dict


def getTests(testInfo):
    tests = []
    testlist = testInfo["testsuites"]
    for listElement in testlist:
        suite = listElement["matrix"]
        if isinstance(suite, list):
            for suiteElement in suite:
                conneciton = listElement["connection-string"]
                if isinstance(conneciton, list):
                    for connecitonElement in conneciton:
                        tests.append([suiteElement, connecitonElement])
                else:
                    tests.append([suiteElement, conneciton])
        else:
            conneciton = listElement["connection-string"]
            if isinstance(conneciton, list):
                for connecitonElement in conneciton:
                    tests.append([suite, connecitonElement])
            else:
                tests.append([suite, conneciton])
    return tests


def getHostInfo(root, testInfo):
    host = root.findtext("Host", "undef")
    sshKey = root.findtext("Credential", "undef")
    # imageName = testInfo["tests"].get("image-name" , "undef")
    # imageTag = testInfo["tests"].get("image-tag" , "undef")
    dockerPullCmd = testInfo["utilities"].get("docker-image-pull", "undef")
    dockerRunCmd = testInfo["utilities"].get("docker-image-run", "undef")
    if os.name == 'nt':
        dsCheckScript = testInfo["utilities"].get("ds-check-windows", "undef")
    else:
        dsCheckScript = testInfo["utilities"].get("ds-check-linux", "undef")
    return (host, sshKey, dockerPullCmd, dockerRunCmd, dsCheckScript)


def getPerfTestCommand(testFile, connection):
    if 'odbc' in connection:
        return "python perfrun.py -c " + connection + " " + os.path.splitext(testFile)[0]
    elif 'jdbc' in connection:
        return "python perfrun.py -j -c " + connection + " " + os.path.splitext(testFile)[0]


def startHost(cwd, host, sshKey, dockerPullCmd, dockerRunCmd, dsCheckScript, isDebug):
    # print(docker.getStopAllCmd())
    # print(docker.getRmAllCmd())
    # print(docker.getPullCmd())
    # print(dockerRunCmd)
    SSH.run(host, sshKey, "uname -a", isDebug=isDebug)
    docker = Docker.Docker('default', 'default')
    SSH.run(host, sshKey, docker.getStopAllCmd(), isDebug=isDebug)
    SSH.run(host, sshKey, docker.getRmAllCmd(), isDebug=isDebug)
    SSH.run(host, sshKey, docker.getRmVolumesCmd(), isDebug=isDebug)
    SSH.run(host, sshKey, dockerPullCmd, isDebug=isDebug)
    SSH.run(host, sshKey, dockerRunCmd, isDebug=isDebug)
    Command.ExecuteAndLogVerbose(dsCheckScript, cwd, isDebug=isDebug)


def stopHost(host, sshKey):
    docker = Docker.Docker('default', 'default')
    SSH.run(host, sshKey, docker.getStopAllCmd())
    SSH.run(host, sshKey, docker.getRmAllCmd())
    SSH.run(host, sshKey, docker.getRmVolumesCmd())


def runPerfTest(cwd, testsuite, connection, isDebug):
    Command.ExecuteAndLogVerbose(getPerfTestCommand(testsuite, connection), cwd, isDebug=isDebug)


def getTestSuite(test):
    return test[0]


def getConnection(root, test):
    return (root.findtext('Connection', 'default') + '-' + test[1])


def dumpBambooVarToTestFile(cwd, testsuite):
    for key in os.environ.keys():
        os.environ[key.upper()] = os.environ[key]
    dict = {}
    dict['session-info'] = {}
    for key in os.environ.keys():
        if 'BAMBOO_' in key:
            newkey = key.split('_', 1)[1]
            dict['session-info'][newkey] = os.environ[key]
    testyaml = YAML.YAML(cwd + '/' + testsuite + '.yaml')
    testyaml.update(dict)
