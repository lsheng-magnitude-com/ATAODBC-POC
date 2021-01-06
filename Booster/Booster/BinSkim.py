from __future__ import print_function
import os
import Command
from XMLFile import XMLFile
from BoosterError import FileNotFoundError, BoosterError
import ata.log

logger = ata.log.AtaLog(__name__)


def _doExecute(root, isDebug):
    print('==============================')
    print('       Enter BinSkim')
    print('==============================')

    binskim = getBinSkim()
    binary = getTargetBinary(root)
    log = getLogPath(binary, root)
    cmd = getBinSkimCommand(binskim, binary, log)
    if not isDebug:
        Command.ExecuteAndATALog(cmd)
    else:
        logger.info(Command)


def Execute(root):
    _doExecute(root, False)

def Debug(root):
    _doExecute(root, True)


def getBinSkim():
    binscope = os.environ.get('BOOSTER_VAR_BINSKIM', 'binskim.exe')
    binscope = '"' + binscope + '"'
    return binscope


def getTargetBinary(root):
    target = root.text
    if not os.path.exists(target):
        raise BoosterError(__name__, 'Can not find ' + target)
    else:
        return target


def getLogPath(tagretBinary, root):
    fileName = os.path.basename(tagretBinary) + '.sarif'
    fileBasedir = root.attrib.get('logdir', os.environ.get('BOOSTER_VAR_STAGING_DIR',os.path.dirname(tagretBinary)) + '/log')
    logDir = os.path.normpath(fileBasedir + '/Report/binskim')
    if not os.path.exists(logDir):
        os.umask(0o000)
        os.makedirs(logDir, 0o0777)
    LogPath = logDir + '/' + fileName
    return LogPath


def getBinSkimCommand(binskim, binary, log):
    Command = binskim + ' analyze ' + binary + ' --verbose --output ' + log
    return Command

