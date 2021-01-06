from __future__ import print_function
import os
import zipfile
import Command
import ata.log

from contextlib import contextmanager
from shutil import make_archive

logger = ata.log.AtaLog(__name__)

def Execute(root):
    print('==============================')
    print('          Enter Zip')
    print('==============================')

    archive = getDest(root)
    file = getSource(root)
    password = getPassword(root)
    exclude_root = root.attrib.get('exclude_root', 'false')
    if not os.path.exists(file):
        print(file + ' does not exit')
        raise Exception('{} does not exist'.format(file))
        # exit(-1)
    print('Create ' + archive + '.zip from ' + file)
    if (exclude_root == 'true') :
        createZip(archive, file, password, True)
    else:
        createZip(archive, file, password)


def Debug(root):
    print('==============================')
    print('          Enter Zip')
    print('==============================')

    archive = getDest(root)
    file = getSource(root)
    print('Create ' + archive + '.zip from ' + file)


def getDest(root):
    zip = root.attrib.get('dest', 'build.zip')
    baseName = zip[:-4]
    return baseName


def getSource(root):
    sourceDir = root.text
    return sourceDir


def getPassword(root):
    password = root.attrib.get('password', 'undef')
    return password


def createZip64(archiveName, source, exclude_root=False):
    if (exclude_root):
        lenDirPath = len(source)
    else:
        lenDirPath = len(os.path.dirname(source))

    with zipfile.ZipFile(archiveName + '.zip', 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for root, dirs, files in os.walk(source):
            for file in files:
                filePath = os.path.join(root, file)
                zf.write(filePath, filePath[lenDirPath:])
    zf.close()


def createZip(archiveName, source, password, exclude_root=False):
    if password == 'undef':
        try:
            if (exclude_root):
                make_archive(archiveName, 'zip', source)
            else:
                rootDir = os.path.dirname(source)
                if (rootDir == ''): rootDir = './'
                baseDir = os.path.basename(source)
                make_archive(archiveName, 'zip', rootDir, baseDir)
        except:
            createZip64(archiveName, source, exclude_root)

    else:
        outputzip = archiveName + '.zip'
        #unzipcommand = '7z x ' + outputzip + ' -o' + archiveName + 'temp'
        rootDir = os.path.dirname(source)
        baseDir = os.path.basename(source)
        if (exclude_root):
            src = os.path.join(rootDir, baseDir) + '/*'
        else:
            src = os.path.join(rootDir, baseDir)
        if os.name == 'nt':
            zipcommand = '7z a ' + outputzip + ' -p' + password + ' ' + src
        else:
            zipcommand = '7za a ' + outputzip + ' -p' + password + ' ' + src
        try:
            #Command.ExecuteAndGetResult(unzipcommand)
            Command.ExecuteAndGetResult(zipcommand)
        except:
            logger.warning ('Unable to add password. Make sure 7z is installed.')

