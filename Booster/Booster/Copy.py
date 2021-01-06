from __future__ import print_function

import glob
import os
from distutils.file_util import copy_file

import Command
import ata.log

logger = ata.log.AtaLog(__name__)
from Booster.Debug import Debug as Debugger


def Execute(root):
    print('==============================')
    print('          Enter Copy')
    print('==============================')

    sourcefiles = getSource(root)
    ignoreEmptySource = root.attrib.get('ignoreEmptySource', 'false')
    if (ignoreEmptySource == 'true'):
        source_exist = False
        for sourcefile in sourcefiles:
            source = sourcefile.text
            if len(glob.glob(source)) != 0:
                source_exist = True
        if not source_exist:
            logger.info('source files are empty.')
            logger.info('skip the copy.')
            return
    dest = getDest(root)
    if Debugger().skip('copy', '----Skip: copy to {}'.format(dest)):
        for s in sourcefiles:
            logger.info('          {}'.format(s.text))
        return
    required = root.attrib.get('required', 'false')

    for sourcefile in sourcefiles:
        source = sourcefile.text
        # print('Copy ' + source + ' to ' + dest)
        logger.info('Copy ' + source + ' to ' + dest)
        try:
            copyGlobFiles(source, dest, required)
        except IOError as err:
            if (required == 'true'):
                raise err
            else:
                logger.warning('WARNING: {}'.format(err))


def Debug(root):
    print('==============================')
    print('          Enter Copy')
    print('==============================')

    dest = getDest(root)
    sourcefiles = getSource(root)

    for sourcefile in sourcefiles:
        source = sourcefile.text
        print('Copy ' + source + ' to ' + dest)


def getDest(root):
    dest = root.attrib.get('dest', './')
    try:
        if not os.path.isdir(dest):
            os.umask(0o000)
            os.makedirs(dest, 0o0777)
        return dest
    except OSError as err:
        logger.warning('WARNING: {}'.format(err))
        exit(0)

def getSource(root):
    return list(root)


def copySingleFile(source, dest, required='false'):
    checkItem(source, required)
    file = os.path.basename(source)
    try:
        if not os.path.isdir(dest):
            os.umask(0o000)
            os.makedirs(dest, 0o0777)
        destFile = dest + '/' + file
        if os.path.isfile(destFile):
            os.umask(0o000)
            try:
                os.chmod(destFile, 0o0777)
            except Exception:
                pass
            os.remove(destFile)
        os.umask(0o000)
        copy_file(source, destFile, preserve_mode=True)
        os.chmod(destFile, 0o0777)
    except OSError as e:
        logger.exception(
            "Failed to copy {src} to {dst}: {error}".format(src=source, dst=dest, error=str(e)))


def copyLink(source, dest, required='false'):
    checkItem(source, required)
    file = os.path.basename(source)
    try:
        if not os.path.isdir(dest):
            os.umask(0o000)
            os.makedirs(dest, 0o0777)
        destFile = dest + '/' + file
        if os.path.exists(destFile):
            os.umask(0o000)
            try:
                os.chmod(destFile, 0o0777)
            except Exception:
                pass
            os.remove(destFile)
        os.umask(0o000)
        Command.ExecuteAndGetResult('cp -RfP ' + source + ' ' + dest)
        #os.chmod(destFile, 0o0777)
    except OSError as e:
        logger.exception(
            "Failed to copy symlink {src} to {dst}: {error}".format(src=source, dst=dest, error=str(e)))


def copyGlobFiles(source, dest, required='false'):
    if len(glob.glob(source)) == 0:
        raise IOError('No paths match {}'.format(source))
    for item in glob.glob(source):
        #On some platform, isfile and islink return both ture for link
        #So we need check both to make sure it's actually a file
        if os.path.isfile(item) and not os.path.islink(item):
            copySingleFile(item, dest, required)
        if os.path.islink(item):
            copyLink(item, dest, required)
        if os.path.isdir(item):
            copyDir(item, dest, required)


def copyDir(source, dest, required='false'):
    checkItem(source, required)
    folder = os.path.basename(source)
    destFolder = dest + '/' + folder
    try:
        if not os.path.isdir(destFolder):
            os.umask(0o000)
            os.makedirs(destFolder, 0o0777)

        try:
            copyGlobFiles(source + '/*', destFolder)
        except IOError as err:
            logger.warning('WARNING: {}'.format(err))
        try:
            copyGlobFiles(source + '/.*', destFolder)
        except IOError:
            logger.debug('No hidden files in {}'.format(source))

    except OSError as e:
        logger.exception(
            "Failed to copy {src} to {dst}: {error}".format(src=source, dst=dest, error=str(e)))


def checkItem(source, required='false'):
    if required == 'false' or os.path.lexists(source):
        return
    else:
        raise IOError('{} does not exist'.format(source))
