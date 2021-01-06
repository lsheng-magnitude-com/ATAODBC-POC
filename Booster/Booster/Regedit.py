from __future__ import print_function
import os

import ata.log

logger = ata.log.AtaLog(__name__)

if os.name == 'nt':
    try:
        import _winreg
    except ImportError:
        import winreg


def Execute(root):
    print('==============================')
    print('     Enter Regedit')
    print('==============================')
    HKEY = getHKey(root)
    subKey = getSubKey(root)
    valueName = getValueName(root)
    valueData = getValueData(root)
    if valueName is not None:
        logger.info('In ' + HKEY + '\\' + subKey)
        logger.info(valueName + '=>' + valueData)
        setValue(HKEY, subKey, valueName, valueData)


def Debug(root):
    Execute(root)

def shouldConvertSlashes(root):
    val = root.attrib.get('ConvertSlashes')
    return val is not None and val.lower() == 'true'
    
def getHKey(root):
    key = root.attrib.get('key')
    if key is None:
        logger.error('key not specified')
        raise Exception('key not specified')
        # exit(-1)
    HKEY = key.split('\\', 1)[0]
    return HKEY


def getSubKey(root):
    key = root.attrib.get('key')
    if key is None:
        logger.error('key not specified')
        raise Exception('key not specified')
        # exit(-1)
    subKey = key.split('\\', 1)[1]
    return subKey


def getValueName(root):
    valueName = root.attrib.get('valueName')
    if valueName is None:
        logger.info('valueName not specified')
    return valueName


def getValueData(root):
    valueData = root.text
    if valueData == '' or valueData == None:
        logger.info('valueData not specified')
        return ""
    else:
        if shouldConvertSlashes(root):
            valueData = valueData.replace('/', '\\')
    
        return valueData



def setValue(HKEY, subKey, valueName, valueData):
    key = eval('_winreg.' + HKEY)
    with _winreg.CreateKeyEx(key, subKey, 0,
                             _winreg.KEY_WOW64_64KEY | _winreg.KEY_ALL_ACCESS) as key:
        _winreg.SetValueEx(key, valueName, 0, _winreg.REG_SZ, valueData)
