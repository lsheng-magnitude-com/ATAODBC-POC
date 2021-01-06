# Execute command and print out error

from __future__ import print_function
import glob
import io
import os
import os.path
import platform
import shutil
import subprocess
import sys
import time
import Shared.CrashUtils as CrashUtils
import tempfile

import ata.log
from BoosterError import BoosterError

logger = ata.log.AtaLog(__name__)

def _cmdlog(cmd, cwd=None, title=None):
    c_cwd = os.getcwd()
    if title is not None and title != '':
        logger.info(title)
    if cwd is None:
        cwd = c_cwd
    logger.debug('Current cwd={cwd}'.format(cwd=c_cwd))
    logger.info('cwd={cwd}'.format(cwd=cwd))
    if type(cmd) == list or type(cmd) == tuple:
        logger.info(' '.join(cmd))
    else:
        logger.info(cmd)


def Execute(root):
    print('==============================')
    print('        Enter Command')
    print('==============================')

    command = root.text
    verbose = root.attrib.get('verbose', None)
    cwd = root.attrib.get('cwd')
    bash = getBash()
    if verbose == 'silent':
        ExecuteInSilentMode(command, cwd, bash)
    elif not verbose or verbose.lower() != 'true':
        ExecuteAndGetResult(command, cwd, bash)
    else:
        ExecuteAndLogVerbose(command, cwd, bash)

def Debug(root):
    print('==============================')
    print('        Enter Command')
    print('==============================')
    
    command = root.text
    cwd = root.attrib.get('cwd')
    _cmdlog(command, cwd)
	
def getBash():
	if platform.system() == 'AIX':
		return '/usr/bin/bash'
	elif platform.system == 'HP-UX':
		return '/usr/local/bin/bash'
	else:
		return None

def ExecuteAndGetResultAndCheckForCrash(command, params, cwd, outputDir, isDebug=False, procDump=None, coreFileName=None):
    tempDir = None
    try:
        if procDump is not None:
            tempDir = tempfile.mkdtemp(dir=outputDir) # Use a unique directory to avoid confusing a dump file created for some other reason as one our command created
            if not isinstance(procDump, list):
                procDump = procDump.split(' ')
            if len(procDump) == 1:
                procDump.extend(['-accepteula', '-ma', '-e'])
            commandAndParams = procDump + ['-x', tempDir, command] + params
        else:
            commandAndParams = [command] + params
            
        _cmdlog(commandAndParams, cwd)
        
        if not isDebug:
            proc = subprocess.Popen(commandAndParams, cwd=cwd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
            
            # Wait for command to exit
            returnedData, _ = proc.communicate()
            
            core = None
            stackTrace = None
            if procDump is not None:
                dumpFiles = glob.glob(os.path.join(tempDir, '*.dmp'))
                logger.info('dumpFiles={0}'.format(dumpFiles))
                if dumpFiles:
                    if coreFileName is None:
                        coreFileName = os.path.basename(dumpFiles[0])
                    core = CrashUtils.save_core_dump(dumpFiles[0], outputDir, coreFileName)
                    logger.info('core={0}'.format(core))
            elif proc.returncode != 0:
                try:
                    core = CrashUtils.find_and_save_core_dump(proc.pid, cwd, outputDir, coreFileName=coreFileName)
                except:
                    logger.warning('Can not find core file')
                
            if core is not None:
                stackTrace = CrashUtils.get_back_trace(command, core)
            return (proc.pid, proc.returncode, returnedData, core, stackTrace)
        return (None, None, None, None, None)
    finally:
        if tempDir is not None:
            shutil.rmtree(tempDir)


def ExecuteAndGetResult(command, cwd=None, bash=None, isDebug=False):
    _cmdlog(command, cwd)
    if not isDebug:
        try:
            result = subprocess.check_output(command, stderr=subprocess.STDOUT, cwd=cwd, executable=bash, shell=True)
            return result
        except subprocess.CalledProcessError as error:
            logger.critical("*** Command " + command + " failed with error output ***")
            logger.critical(error.output)
            raise error


def ExecuteAndLog(command, log, cwd=None, bash=None):
    _cmdlog(command, cwd, 'ExecuteAndLog')
    try:
        output = subprocess.check_output(command, cwd=cwd, executable=bash, stderr=subprocess.STDOUT, shell=True)
        with open(log, 'a') as f:
            f.write(output)
    except subprocess.CalledProcessError as error:
        logger.critical("*** Command " + command + " failed with error output ***")
        logger.critical(error.output)
        raise error


def ExecuteAndTail(command, log, checkreturncode=True, cwd=None, bash=None, isDebug=False):
    _cmdlog(command, cwd, 'ExecuteAndTail')
    if not isDebug:
        try:
            with io.open(log, 'wb') as writer, io.open(log, 'rb', 1) as reader:
                proc = subprocess.Popen(command, cwd=cwd, executable=bash, stdout=writer, stderr=subprocess.STDOUT, shell=True,
                                        universal_newlines=True)
                while proc.poll() is None:
                    sys.stdout.write(reader.read())
                    time.sleep(0.5)
                sys.stdout.write(reader.read())
                if checkreturncode == True:
                    rc = proc.returncode
                    if rc != 0:
                        raise Exception("Error: command %s returned error code %d\n" % (command, rc))
                    else:
                        logger.info("Command %s ended successfully" % command)
        except subprocess.CalledProcessError:
            raise


def ExecuteAndLogVerbose(command, cwd=None, bash=None, shell=True, isDebug=False):
    if shell:
        command_display = command
    else:
        command_display = ' '.join(command)
    _cmdlog(command_display, cwd, 'ExecuteAndLogVerbose')
    if not isDebug:
        proc = subprocess.Popen(command, cwd=cwd, executable=bash, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=shell)
        for line in iter(proc.stdout.readline, b''):
            logger.info(line.rstrip())
        # Wait for the process to get the return code
        proc.communicate()
        rc = proc.returncode
        if rc != 0:
            raise BoosterError(__name__, "Error: command {cmd} has failed\n".format(cmd=command_display))
        else:
            logger.info("Command {cmd} ended successfully".format(cmd=command_display))


def ExecuteInSilentMode(command, cwd=None, bash=None, shell=True):
    print('Silent Mode')
    if shell:
        command_display = command
        _cmdlog(command_display, cwd, 'ExecuteInSilentMode')
        proc = subprocess.Popen(command, cwd=cwd, executable=bash, stdout=None, stderr=None, shell=True)
    else:
        command_display = ' '.join(command)
        _cmdlog(command_display, cwd, 'ExecuteInSilentMode')
        proc = subprocess.Popen(command, cwd=cwd, executable=bash, stdout=None, stderr=None)
    for line in iter(proc.stdout.readline, b''):
        logger.info(line.rstrip())
    # Wait for the process to get the return code
    proc.communicate()
    rc = proc.returncode
    if rc != 0:
        raise BoosterError(__name__, "Error: command {cmd} has failed\n".format(cmd=command_display))
    else:
        logger.info("Command {cmd} ended successfully".format(cmd=command_display))


def ExecuteAndATALog(command, cwd=None, bash=None):
    _cmdlog(command, cwd, 'ExecuteAndATALog')
    try:
        output = subprocess.check_output(command, cwd=cwd, executable=bash, stderr=subprocess.STDOUT, shell=True)
        logger.debug(output)
    except subprocess.CalledProcessError as error:
        logger.critical(error.output)
        raise error
