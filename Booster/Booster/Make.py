from __future__ import print_function
import os

import Command
import ata.log
from Booster.Debug import Debug as Debugger

logger = ata.log.AtaLog(__name__)


def Execute(root):
    print('==============================')
    print('          Enter Make')
    print('==============================')
    logger.debug('Enter Make')
    dbg = Debugger()


    make = getMake(root)
    option = getOption(root)
    env = getEnv(root)
    targets = getTarget(root)
    archs = getArch(root)
    makefiles = list(root)
    wd = root.get('cwd')
    if wd and not os.path.exists(wd):
        os.makedirs(wd)
        logger.info('make working directory: ' + wd)
    for makefile in makefiles:
        file = makefile.text
        optional = makefile.attrib.get('optional', 'False')
        if optional.upper() == 'TRUE' and not (os.path.exists(file)):
            logger.info('Optional file ' + file + ' does not exist')
        else:
            log = getLogPath(file)
            for arch in archs:
                for target in targets:
                    if wd:
                        cwd = wd
                        makefile = file
                    else:
                        cwd = os.path.dirname(file)
                        makefile = os.path.basename(file)
                    command = getCompileCommand(make, makefile, arch, target, env, option)
                    if dbg.skip('make', '----Skip: {}'.format(command)):
                        continue
                    Command.ExecuteAndATALog(command, cwd=cwd)


def Debug(root):
    print('==============================')
    print('          Enter Make')
    print('==============================')

    make = getMake(root)
    option = getOption(root)
    env = getEnv(root)
    targets = getTarget(root)
    archs = getArch(root)
    makefiles = list(root)
    for makefile in makefiles:
        file = makefile.text
        log = getLogPath(file)
        for arch in archs:
            for target in targets:
                command = getCompileCommand(make, file, arch, target, env, option)
                print(command + 'log to ' + log)


def getMake(root):
    make = root.attrib.get('make', 'gmake')
    return make


def getOption(root):
    option = root.attrib.get('opt', '')
    extra_opt = root.attrib.get('extra_opt')
    if extra_opt is None or extra_opt == '':
        return option
    else:
        return option + ' ' + extra_opt


def getEnv(root):
    env = root.attrib.get('env', '')
    extra_env = root.attrib.get('extra_env', '')
    if extra_env == '':
        return env
    else:
        return env + ' ' + extra_env


def getTarget(root):
    target = root.attrib.get('target', '')
    targetlist = target.split(',')
    return targetlist


def getArch(root):
    arch = root.attrib.get('arch', '')
    archlist = arch.split(',')
    return archlist


def getCompileCommand(compiler, makefile, arch, target, env, option):
    command = env + ' ' + compiler + ' -f ' + makefile + ' ' + target + ' ARCH=' + arch + ' ' + option
    return command


def getLogPath(file):
    fileName = os.path.basename(file)
    logName = fileName.replace('.mak', '.log')
    logPath = 'log/' + logName
    return logPath
