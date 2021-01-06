"""Run some python code defined in the booster script directly"""

__all__ = ['Execute', 'Debug']

import ata.log
from BoosterError import BoosterError

logger = ata.log.AtaLog(__name__)

def _do_execute(root, isDebug):
    print '=============================='
    print '        Enter Eval'
    print '=============================='

    code = root.text
    
    if isDebug:
        compile(code, '<string>', 'exec')
    else:
        exec(code)

def Execute(root):
    _do_execute(root, False)
    
def Debug(root):
    _do_execute(root, True)
    
    
