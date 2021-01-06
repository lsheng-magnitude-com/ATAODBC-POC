from __future__ import print_function
import Command
import ata.log
from Booster.Debug import Debug as Debugger

logger = ata.log.AtaLog(__name__)

def Execute(root):
    print(('=============================='))
    print(('          Enter P4Revert'))
    print(('=============================='))
    logger.debug("Start P4Revert")
    command = 'p4 revert //...'
    if Debugger().skip('p4revert', '----Skip: revert'):
        return
    Command.ExecuteAndGetResult(command)




def Debug(root):
    print(('=============================='))
    print(('          Enter P4Revert'))
    print(('=============================='))

    command = 'p4 revert //...'
    print(command)
