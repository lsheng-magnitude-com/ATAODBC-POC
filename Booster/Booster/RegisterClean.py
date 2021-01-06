from __future__ import print_function
import os

import ata.log
from BoosterError import BoosterTagError

logger = ata.log.AtaLog(__name__)

if os.name == 'nt':
    try:
        import _winreg
    except ImportError:
        import winreg


def Execute(root):
    print('==============================')
    print('     Clean Regedit')
    print('==============================')
    HKEY = getHKey(root)
    path = getPath(root)
    value = getValue(root)
    logger.info('In ' + HKEY + '\\' + path)
    logger.info('Clean => ' + value)
    deleteValue(HKEY, path, value)


def Debug(root):
    Execute(root)


def getHKey(root):
    key = root.attrib.get('key', 'undef')
    if key == 'undef':
        logger.error('key not specified')
        raise BoosterTagError(__name__, 'key not specified')
        # exit(-1)
    HKEY = key.split('\\', 1)[0]
    return HKEY


def getPath(root):
    key = root.attrib.get('key', 'undef')
    if key == 'undef':
        logger.error('key not specified')
        raise BoosterTagError(__name__, 'key not specified')
        # exit(-1)
    path = key.split('\\', 1)[1]
    return path

def getValue(root):
    value = root.text
    if value == 'undef':
        logger.error('value not specified')
        raise BoosterTagError(__name__, 'value not specified')
        # exit(-1)
    return value


def deleteValue(HKEY, path, value):
    key = eval('_winreg.' + HKEY)
    try:
        handle = _winreg.OpenKey(key, path, 0, _winreg.KEY_WOW64_64KEY | _winreg.KEY_ALL_ACCESS)
        _winreg.DeleteKeyEx(handle, value)
        _winreg.CloseKey(handle)
    except WindowsError:
        pass
