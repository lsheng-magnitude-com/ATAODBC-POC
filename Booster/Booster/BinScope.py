from __future__ import print_function
import os
import Command
from XMLFile import XMLFile
from BoosterError import FileNotFoundError, BoosterError
import ata.log

logger = ata.log.AtaLog(__name__)


def _doExecute(root, isDebug):
    print('==============================')
    print('       Enter BinScope')
    print('==============================')

    binscope = getBinScope()
    binary = getTargetBinary(root)
    symbol = getSymbolFile(root)
    skip = getSkippedChecks(root)
    (htmlLog, xmlLog) = getLogPath(binary, root)
    (htmlCommand, xmlCommand) = getBinScopeCommand(binscope, binary, symbol, skip, htmlLog, xmlLog)
    if not isDebug:
        Command.ExecuteAndATALog(htmlCommand)
        Command.ExecuteAndATALog(xmlCommand)
        parseLog(binary,xmlLog)
    else:
        logger.info(htmlCommand)
        logger.info(xmlCommand)


def Execute(root):
    _doExecute(root, False)

def Debug(root):
    _doExecute(root, True)


def getBinScope():
    binscope = os.environ.get('BOOSTER_VAR_BINSCOPE', 'C:\Program Files\Microsoft BinScope 2014\Binscope.exe')
    binscope = '"' + binscope + '"'
    return binscope


def getTargetBinary(root):
    target = root.text
    if not os.path.exists(target):
        raise BoosterError(__name__, 'Can not find ' + target)
    else:
        return target


def getSymbolFile(root):
    return root.attrib.get('symbol', 'default')


def getSkippedChecks(root):
    return root.attrib.get('skip', 'default')


def getLogPath(tagretBinary, root):
    fileName = os.path.basename(tagretBinary)
    fileBasedir = root.attrib.get('logdir', os.environ.get('BOOSTER_VAR_STAGING_DIR',os.path.dirname(tagretBinary)) + '/log')
    htmlLogName = fileName + '.html'
    xmlLogName = fileName + '.xml'
    htmlLogPath = fileBasedir + '/Report/binscope/' + htmlLogName
    xmlLogPath = fileBasedir + '/Report/binscope/' + xmlLogName
    return htmlLogPath, xmlLogPath


def getBinScopeCommand(binscope, tagretBinary, SymbolFile, skipChecks, htmlLog, xmlLog):
    Options = ''
    if SymbolFile != 'default':
        Options = Options + ' /SymPath ' + SymbolFile
    if skipChecks != 'default':
        skipCheckList = skipChecks.split(',')
        for item in skipCheckList:
            Options = Options + ' /SkippedChecks ' + item
    htmlCommand = binscope + ' /Target ' + tagretBinary + ' /LogFile ' + htmlLog + ' /Verbose' + Options
    xmlCommand = binscope + ' /Target ' + tagretBinary + ' /LogFile ' + xmlLog + ' /Red /Verbose' + Options
    return htmlCommand, xmlCommand


def parseLog(tagretBinary, log):
    xml = XMLFile(log)
    root = xml.root()
    for node in root.iter():
        if node.tag == 'result' and node.text != 'PASS':
            raise BoosterError(__name__, 'BinScope test failed on ' + tagretBinary)
    logger.info('BinScope test succeeded on ' + tagretBinary)

