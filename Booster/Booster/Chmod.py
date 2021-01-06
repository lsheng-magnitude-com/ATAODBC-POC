import os
import sys

import ata.log

logger = ata.log.AtaLog(__name__)


def Execute(root):
    print('==============================')
    print('     Enter Chmod')
    print('==============================')
    names = getSource(root)
    mode = getMode(root)
    intMode = int(mode, 8)  # convert to octal from string

    for name in names:
        if os.path.isdir(name):
            os.chmod(name, intMode)
            runRecursively(name, intMode)
            logger.info('change permission of ' + name + ' to ' + mode + ' for all files and subfolders')
        elif os.path.exists(name):
            os.chmod(name, intMode)
            logger.info('change permission of ' + name + ' to ' + mode)
        else:
            logger.warning('attempt to change permission of ' + name + ' failed')
            logger.error('**Error** ' + name + ' does not exist\n')


def Debug(root):
    print('==============================')
    print('     Enter Chmod')
    print('==============================')

    names = getSource(root)
    mode = getMode(root)
    intMode = int(mode, 8)  # convert to octal from string

    for name in names:
        if os.path.isdir(name):
            os.chmod(name, intMode)
            runRecursively(name, intMode)
            logger.info('change permission of ' + name + ' to ' + mode + ' for all files and subfolders')
        elif os.path.exists(name):
            os.chmod(name, intMode)
            logger.info('change permission of ' + name + ' to ' + mode)
        else:
            logger.warning('attempt to change permission of ' + name + ' failed')
            logger.error('**Error** ' + name + ' does not exist\n')


def getMode(root):
    mode = root.attrib.get('mode', './')
    return mode


def getSource(root):
    sources = list(root)
    names = []
    for source in sources:
        name = source.text
        names.append(name)
    return names


def runRecursively(name, mode):
    for root, dirs, files in os.walk(name):
        for dir in dirs:
            os.chmod(os.path.join(root, dir), mode)
        for file in files:
            os.chmod(os.path.join(root, file), mode)
