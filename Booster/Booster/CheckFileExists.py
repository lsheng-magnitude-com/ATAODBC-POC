from __future__ import print_function

import glob
import os
import time
from distutils.file_util import copy_file
from BoosterError import FileNotFoundError, BoosterError

import Command
import ata.log

logger = ata.log.AtaLog(__name__)
from Booster.Debug import Debug as Debugger

def _do_execute(root, isDebug):
    print('==============================')
    print('    Check File Exists')
    print('==============================')

    timeout = getTimeout(root)
    basedir = getBaseDir(root)
    checklist = getCheckList(root)
    
    Run(checklist, basedir, timeout, isDebug)
        
def Run(fileList, basedir='', timeout=None, isDebug=False):
    if isDebug:
        for file in fileList:
            filePath = os.path.join(basedir, file)
            logger.info('check ' + filePath)
    else:
        checkFiles(basedir, fileList, timeout)
    
def Execute(root):
    _do_execute(root, False)

def Debug(root):
    _do_execute(root, True)

def getTimeout(root):
    timeout = root.attrib.get('timeout')
    if (timeout is not None):
        return int(timeout)
    return None
        
def getBaseDir(root):
    return root.attrib.get('basedir', '')


def getCheckList(root):
    checklist = []
    for item in list(root):
        if item.tag == 'File':
            checklist = addFileToCheckList(item.text, checklist)
        if item.tag == 'List':
            checklist = addFileListToCheckList(item.text, checklist)

    return checklist


def addFileToCheckList(file, checklist):
    checklist.append(file)
    return checklist


def addFileListToCheckList(filelist, checklist):
    with open(filelist, 'r') as fhandle:
        for line in fhandle:
            line = line.strip()
            checklist.append(line)
    return checklist


def checkFiles(basedir, checklist, timeout):
    def FindMissingFile():
        for file in checklist:
            filePath = os.path.join(basedir, file)
            logger.info('check ' + filePath)
            if not os.path.exists(filePath):
                return filePath
        return None
    
    start_time = time.time()
    missing = None
    while True:
        missing = FindMissingFile()
        if (missing is None):
            return
        
        elapsed = time.time() - start_time
        if timeout is None or elapsed > timeout:
            print("{} contains {}".format(os.path.dirname(missing), os.listdir(os.path.dirname(missing))))
            raise FileNotFoundError(missing)
        else:
            logger.info('missing ' + missing + ' but timeout has not yet elapsed, sleeping for 1 second and retrying...')
            time.sleep(1)



