# =============================================================================
# Call regsvr32 to register the given DLL.
#
# Syntax of the configuration file XML tag:
# <RegisterDLL>full path to DLL</RegisterDLL>
# =============================================================================

from __future__ import print_function
import subprocess
import sys

import ata.log

logger = ata.log.AtaLog(__name__)


# Execute the action.
# root:     The root node of the parsed XML tag <RegisterDLL>full path to DLL</RegisterDLL>.
def _doExecute(root, isDebug):
    print('==============================')
    print('      Enter RegisterDLL')
    print('==============================')
    dllName = root.text
    ExecuteAndGetResult(dllName, isDebug)

def Execute(root):
    _doExecute(root, False)
    
def Debug(root):
    _doExecute(root, True)

# Unistall first a previous version of the DLL then install the new specified version.
# dllName:      Full path to the DLL.
def ExecuteAndGetResult(dllName):
    logger.info('Registering {}'.format(dllName))
    # print('Registering ' + dllName)

    if not isDebug:
        # First uninstall a previously installed version of that DLL (continue in case of error).
        result = ExecuteRegsvr32(dllName, False)
        if result is not None:
            logger.info('Failed to uninstall "{}" - Reason: {}'.format(dllName, result))
            # print('Fail to uninstall "{}" - Reason: {}'.format(dllName, result))

        # Install that version of the DLL (fail in case of error).
        result = ExecuteRegsvr32(dllName, True)
        if result is not None:
            message = 'Fail to install "{}" - Reason: {}'.format(dllName, result)
            logger.info(message)
            # print(message)
            raise Exception(message)


# Install or uninstall the given DLL
# dllName:      The full path to the DLL.
# isInstall:    True install the DLL, false unistall the DLL.
def ExecuteRegsvr32(dllName, isInstall):
    try:
        option = ''
        if not isInstall:
            option = '/u '

        command = 'regsvr32 /s {}"{}"'.format(option, dllName)
        print(command)

        subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)
        return None

    except subprocess.CalledProcessError as error:
        sys.stdout.flush()
        print(error.output)
        return error.output


# For local manual testing purpose (can be removed from final version).
if __name__ == "__main__":
    class TestNode:
        text = 'D:\\Perforce\\thierryg_win02\\Drivers\\SEN\\Maintenance\\10.1\\XMDriver\\C++\\Product\\Bin\\w2012r2\\vs2015\\debug32mt\\XMOLEDB32.dll'


    node = TestNode()
    print(node.text)
    Execute(node)
