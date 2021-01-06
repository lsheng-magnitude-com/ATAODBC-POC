from __future__ import print_function

import os
import uuid
import ata.log

logger = ata.log.AtaLog(__name__)

def _doExecute(root):
    print('==============================')
    print('     Generate GUID_PPRODUCT')
    print('==============================')
    for element in list(root):
        varName = element.tag
        varValue = element.text
        if varValue.lower() == "hostid":
            varValue = getUuid1() 
            print(('Make a Product GUID based on the host ID and current time'))
            print((varName + ' = ' + varValue))
            logger.info(varName + ' = ' + varValue)
            os.environ[varName] = varValue
        elif varValue.lower() == "random":
            varValue = getUuid4()
            print(('Make a random Product GUID')            )
            print((varName + ' = ' + varValue))
            logger.info(varName + ' = ' + varValue)
            os.environ[varName] = varValue
        else:
            print(('Customize Product GUID') )
            print((varName + ' = ' + varValue))
            logger.info(varName + ' = ' + varValue)
            os.environ[varName] = varValue
            
def Execute(root):
    _doExecute(root)
    
def Debug(root):
    _doExecute(root)

# make a UUID based on the host ID and current time
def getUuid1():
    UUID = uuid.uuid1()
    return str(UUID)

# make a random UUID
def getUuid4():
    UUID = uuid.uuid4()
    return str(UUID)
    
