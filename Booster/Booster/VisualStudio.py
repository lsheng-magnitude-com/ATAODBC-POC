from __future__ import print_function
import os
import Command


def Execute(root):
    print('==============================')
    print('          Enter VS')
    print('==============================')

    msbuild = getMsbuild(root)
    targets = getTarget(root)
    archs = getArch(root)
    opt = getOption(root)
    solutions = list(root)
    for solution in solutions:
        file = solution.text
        optional = solution.attrib.get('optional', 'False')
        if optional.upper() == 'TRUE' and not (os.path.exists(file)):
            print('Optional file ' + file + ' does not exist')
        else:
            for arch in archs:
                for target in targets:
                    command = getCompileCommand(msbuild, file, arch, target, opt)
                    Command.ExecuteAndATALog(command)


def Debug(root):
    print('==============================')
    print('  Enter VS')
    print('==============================')

    msbuild = getMsbuild(root)
    targets = getTarget(root)
    archs = getArch(root)
    solutions = list(root)
    for solution in solutions:
        file = solution.text
        log = getLogPath(file)
        for arch in archs:
            for target in targets:
                command = getCompileCommand(msbuild, file, arch, target, opt)
                print(command + 'log to ' + log)


def getMsbuild(root):
    msbuild = root.attrib.get('msbuild', '')
    msbuild = '"' + msbuild + '"'
    return msbuild


def getTarget(root):
    target = root.attrib.get('target', '')
    targetlist = target.split(',')
    return targetlist


def getArch(root):
    arch = root.attrib.get('arch', '')
    archlist = arch.split(',')
    return archlist


def getOption(root):
    option = root.attrib.get('opt', '')
    if option == '':
        return option
    else:
        return ';' + option


def getCompileCommand(compiler, file, arch, target, opt):
    command = compiler + ' /p:Configuration=' + target + ';Platform=' + arch + opt + ' ' + file + ' /v:d /m:2'
    return command


def getLogPath(file):
    fileName = os.path.basename(file)
    logName = fileName.replace('.sln', '.log')
    logPath = 'log/' + logName
    return logPath
