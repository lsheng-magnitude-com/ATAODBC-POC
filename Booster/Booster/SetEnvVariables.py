from __future__ import print_function

import os

import ata.log

logger = ata.log.AtaLog(__name__)


def _doExecute(root):
    print('==============================')
    print('     Enter SetEnvVariables')
    print('==============================')
    for element in list(root):
        varName = element.tag
        varValue = element.text or ''
        # print(varName + ' = ' + varValue)
        logger.info(varName + ' = ' + varValue)
        os.environ[varName] = varValue

def Execute(root):
    _doExecute(root)
    
def Debug(root):
    _doExecute(root)
    
