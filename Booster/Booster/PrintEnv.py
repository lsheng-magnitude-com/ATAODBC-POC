from __future__ import print_function
import os
import Command
from BoosterError import FileNotFoundError, BoosterError
import ata.log

logger = ata.log.AtaLog(__name__)


def _doExecute(root, isDebug):
    print('==============================')
    print('       Enter PrintEnv')
    print('==============================')
    printAllExceptBamboo()


def Execute(root):
    _doExecute(root, False)


def Debug(root):
    _doExecute(root, True)


def printAll():
    for key in os.environ.keys():
        logger.info(key + ':' + os.environ[key])


def printAllExceptBamboo():
    for key in os.environ.keys():
        if 'bamboo_' in key or 'BAMBOO_' in key:
            pass
        else:
            logger.info(key + ':' + os.environ[key])
