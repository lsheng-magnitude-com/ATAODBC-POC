from __future__ import print_function
import os

import ata.log

logger = ata.log.AtaLog(__name__)

def Execute(root):
    print('==============================')
    print('          Enter Rename')
    print('==============================')

    File = getSource(root)
    baseDir = os.path.dirname(File)
    newFile = getDest(root, baseDir)
    logger.info('Rename ' + File + ' to ' + newFile)
    if os.path.exists(newFile):
        logger.info('A file with same name already exists')
    elif os.path.exists(File):
        os.rename(File, newFile)


def Debug(root):
    print('==============================')
    print('          Enter Rename')
    print('==============================')

    File = getSource(root)
    baseDir = os.path.dirname(File)
    newFile = getDest(root, baseDir)
    logger.info('Rename ' + File + ' to ' + newFile)


def getSource(root):
    source = root.text
    if (not os.path.exists(source)):
        logger.info(source + ' not exist')
    return source


def getDest(root, baseDir):
    newName = root.attrib.get('newname', 'undef')
    newFile = os.path.join(baseDir, newName)
    return newFile
