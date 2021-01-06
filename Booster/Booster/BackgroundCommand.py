from __future__ import print_function
"""Execute a command in the backgound"""

__all__ = ['Execute', 'Debug', 'run']
import os

import ata.log
from BoosterError import BoosterError
import Booster.Shared.BackgroundCommands

logger = ata.log.AtaLog(__name__)
_is_win = os.name == 'nt'


def _log_command(cmd, name, output, cwd):
    c_cwd = os.getcwd()
    if cwd is None:
        cwd = c_cwd
    logger.debug('Current cwd={cwd}'.format(cwd=c_cwd))
    logger.info('cwd={cwd} name={name} outputFile={output}'.format(cwd=cwd, name=name, output=output))
    logger.info(cmd)


def _do_execute(root, isDebug):
    print('==============================')
    print('        Enter BackgroundCommand')
    print('==============================')

    name = None
    command = []
    option = {}

    for k, v in root.attrib.items():
        if k == 'command':
            command.append(v)
            for param in list(root):
                command.append(param.text)
        elif k == 'cwd':
            option['cwd'] = v
        elif k == 'name':
            name = v
        elif k == 'output':
            pass
        elif k == 'shell':
            option['shell'] = v.lower() == 'true'
        else:
            option[k] = v

    if name is None:
        raise ValueError('name attribute is required!')
    if not command:
        raise ValueError('command attribute is expected')
    if 'output' not in option:
        option['stdout'] = 'BackgroundCommandOutput_{0}.txt'.format(name)

    if isDebug:
        logger.info('name={} command={}'.format(name, command[0]))
        if len(command) > 1:
            logger.info('    parameters')
            for p in command[1:]:
                logger.info('        ' + p)
        if option:
            logger.info('    options')
            for k, v in option.items():
                logger.info('        {}: {}'.format(k, v))
    else:
        Booster.Shared.BackgroundCommands.start(name, command, **option)


def Execute(root):
    _do_execute(root, False)


def Debug(root):
    _do_execute(root, True)


def run(name, command, cwd=None, outputFile=None, shell=False, isDebug=False):
    if name is None:
        raise RuntimeError("Name attribute must be provided!")
    if outputFile is None:
        outputFile = "BackgroundCommandOutput_{0}.txt".format(name)
    _log_command(cmd=command, name=name, output=outputFile, cwd=cwd)
    if not isDebug:
        Booster.Shared.BackgroundCommands.start(name, command, cwd, outputFile, shell=shell)
