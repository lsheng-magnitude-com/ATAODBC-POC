from __future__ import print_function

import glob
import os
import xml.etree.ElementTree as ET
import Command
import shutil
import ata.log

logger = ata.log.AtaLog(__name__)

def _doExecute(root, isDebug):
    print('=========================')
    print('      Enter GTest        ')
    print('=========================')

    binary = getUnitTestBinary(root)
    opt = getUnitTestOpt(root)
    name = GetName(root)
    output = getTestOutput(root, name)
    if name is None:
        name = os.path.splitext(os.path.basename(output))[0]
    
    outDir = getOutputDir(root)
    checkFailure = getCheckFailureFlag(root)
    executeTest(binary,opt,name,output,outDir,checkFailure,isDebug)

def Execute(root):
    try:
        _doExecute(root, False)
    except:
        import traceback
        traceback.print_exc()
        exit(-1)


def Debug(root):
    _doExecute(root, True)


def getUnitTestBinary(root):
    return root.text


def getUnitTestOpt(root):
    return root.attrib.get('opt','')

def GetName(root):
    return root.attrib.get('name', None)

def getTestOutput(root, name):
    outDir = getOutputDir(root)
    if outDir is None:
        outDir = os.getcwd()
    if name is not None:
        if root.attrib.get('output', None) is not None:
            logger.error('both output and name specified, which is not allowed!');
            exit(-1)
        return os.path.join(outDir, name, 'summary.xml')
    return root.attrib.get('output', os.path.join(outDir, 'UnitTest_summary.xml'))

def getOutputDir(root):
    return root.attrib.get('outdir', None)

def getCheckFailureFlag(root):
    return root.attrib.get('checkfailure', 'false')

def _createFileFromString(filename, str):
    with open(filename, 'w') as f:
        f.write(str)

def IsWindows():
    return os.name == 'nt'

def executeTest(binary,opt,name,output,outDir,checkFailure,isDebug):
    command = binary
    params = opt.split()
    
    if outDir is not None:
        outDir = os.path.join(outDir, name)
        outputPath = os.path.join(outDir, output)
    else:
        outputPath = output
    
    params.append("--gtest_output=xml:{0}".format(outputPath));
    cwd = os.getcwd()
    
    core = None
    stackTrace = None
    if outDir is not None:
        if not os.path.exists(outDir) and not isDebug:
            os.makedirs(outDir)
        shutil.copy(binary, os.path.join(outDir, os.path.basename(binary)))
        
        procDump = None
        coreFileName = os.path.join(outDir, 'core')
        if IsWindows():
            coreFileName = coreFileName + '.dmp'
            pdbPath = binary[:-4] + '.pdb'
            if os.path.isfile(pdbPath):
                shutil.copy(pdbPath, os.path.join(outDir, os.path.basename(pdbPath)))
            else:
                logger.info("No PDB file found for GTest binary '{0}'".format(binary))
            
            if 'PROCDUMP' in os.environ:
                procDump = os.environ['PROCDUMP']
        
        pid, retcode, returnedData, core, stackTrace = Command.ExecuteAndGetResultAndCheckForCrash(command, params, cwd, outDir, isDebug=isDebug, coreFileName=coreFileName, procDump=procDump)
        _createFileFromString(os.path.join(outDir, 'output.log'), returnedData)
    else:
        ignoreParams = ["||"]
        if IsWindows():
            ignoreParams.append('ver>nul')
        else:
            ignoreParams.append('true')
        cmd = " ".join([command] + params + ignoreParams)
        retcode = Command.ExecuteAndGetResult(cmd,isDebug=isDebug)
    
    if not isDebug:
        outputCreated = os.path.isfile(outputPath)
        ranSuccessfully = core is None and outputCreated and retcode in (0, 1)
        generateConsoleSummary(outputPath, ranSuccessfully, checkFailure, stackTrace)
        if not outputCreated:
            logger.info("GTest failed to create expected output file '{0}'. Creating file containing error.".format(outputPath))
            _createFileFromString(outputPath, '<?xml version="1.0" encoding="UTF-8" ?><testsuite tests="1" failures="1" name="{0}"><testcase name="CreateOutputFile"><failure message="GTest did not create an output file ({1}), probably crashed (return code was {2})" /></testcase></testsuite>'.format(name, outputPath, retcode))


def generateConsoleSummary(output, ranSuccessfully, checkFailure, stackTrace):
    errMsg = 'Unit tests failed'
    if ranSuccessfully:
        tree = ET.parse(output)
        root = tree.getroot()
        tests = root.attrib.get('tests')
        failures = root.attrib.get('failures')
        failed = '0' != failures
        disabled = root.attrib.get('disabled')
        errors = root.attrib.get('errors')
        succeed = int(tests) - int(failures) - int(disabled) - int(errors)
        logger.info('---------------------------')
        logger.info('Total ' + tests)
        logger.info('SUCCEED ' + str(succeed))
        logger.info('FAILED ' + failures)
        logger.info('DISABLED ' + disabled)
        logger.info('ERRORS ' + errors)
        logger.info('---------------------------')
        logger.info('End of tests')
    else:
        failed = True
        if stackTrace is None:
            stackTrace = "<Failed to get stacktrace>"
        errMsg = "Unit tests crashed!\n" + stackTrace
        
    if failed:
        logger.error(errMsg)
        if checkFailure == 'true':
            exit(-1)


