from __future__ import print_function
import glob
import os
import shutil
import stat

import ata.log
from Booster.Debug import Debug as Debugger

logger = ata.log.AtaLog(__name__)


def Execute(root):
    print('==============================')
    print('         Enter Remove')
    print('==============================')
    file = root.text
    exclude = root.attrib.get('exclude', 'None')
    if Debugger().skip('remove', '----Skip: remove {}'.format(file)):
        return
    logger.info('Remove ' + file)
    removeGlobFiles(file, exclude)


def Debug(root):
    print('==============================')
    print('         Enter Remove')
    print('==============================')

    file = root.text
    logger.info('Remove ' + file)


def removeSingleFile(file):
    if os.path.isfile(file):
        try:
            os.chmod(file, stat.S_IWRITE)
        except Exception:
            logger.warning('Failed to Remove %s' % file)
            pass
        try:
            os.remove(file)
        except Exception:
            logger.warning('Failed to Remove %s' % file)
    if os.path.islink(file):
        os.remove(file)


def removeGlobFiles(file, exclude):
    for item in glob.glob(file):
        if os.path.basename(item) == os.path.basename(exclude):
            logger.info('Keep ' + exclude)
        else:
            if os.path.isfile(item): removeSingleFile(item)
            if os.path.islink(item): removeSingleFile(item)
            if os.path.isdir(item): removeDir(item)


def removeDir(dir):
    if os.path.isdir(dir):
        for item in glob.glob(dir + '/*'):
            try:
                if os.path.isfile(item): removeSingleFile(item)
                if os.path.islink(item): removeSingleFile(item)
                if os.path.isdir(item): removeDir(item)
            except Exception:
                logger.warning('Failed to Remove %s' % item)
                continue
        for item in glob.glob(dir + '/.*'):
            try:
                if os.path.isfile(item): removeSingleFile(item)
                if os.path.islink(item): removeSingleFile(item)
                if os.path.isdir(item): removeDir(item)
            except Exception:
                logger.warning('Failed to Remove %s' % item)
                continue
        try:
            shutil.rmtree(dir)
        except Exception as e:
            print((e))
            try:
                os.rmdir(dir)
                logger.info("symlink removed using rmdir instead")
            except Exception as e:
                # still fail to delete, resort to continuing
                print(("*******************************"))
                logger.warning("failed to remove %s, continuing" % dir)
                print(("*******************************"))
                logger.exception(str(e))
