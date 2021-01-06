from __future__ import print_function
import os
import Command
import platform
from BoosterError import FileNotFoundError, BoosterError
import ata.log

logger = ata.log.AtaLog(__name__)


def _doExecute(root, isDebug):
    print('==============================')
    print('    Enter CheckDependency')
    print('==============================')

    commandPrefix = getCommandPrefix()
    binary = getTargetBinary(root)
    command = commandPrefix + ' ' + binary
    if not isDebug:
        Command.ExecuteAndLogVerbose(command)
    else:
        logger.info (command)


def Execute(root):
    _doExecute(root, False)

def Debug(root):
    _doExecute(root, True)


def getCommandPrefix():
    if os.name == 'nt':
        return 'echo Please use dependency walker on Windows to check'
    elif platform.system() == 'Darwin':
        return 'otool -L'
    else:
        return 'ldd'


def getTargetBinary(root):
    target = root.text
    if not os.path.exists(target):
        raise BoosterError(__name__, 'Can not find ' + target)
    else:
        return target


