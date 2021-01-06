from __future__ import print_function
import os
import Command
from Booster.Debug import Debug as Debugger

def Execute(root):
    print('==============================')
    print('     Enter Ant Process')
    print('==============================')

    dbg = Debugger()
    setAntHome(root)
    setJavaHome(root)
    compiler = getCompiler(root)
    option = getOption(root)
    targets = getTarget(root)
    buildfiles = list(root)
    for buildfile in buildfiles:
        file = buildfile.text
        optional = buildfile.attrib.get('optional', 'False')
        if optional.upper() == 'TRUE' and not(os.path.exists(file)):
            print('Optional file ' + file + ' does not exist')
        else:
            for target in targets:
                command = getCompileCommand(compiler, file, target, option)
                if dbg.skip('ant', 'skip ant\n{}'.format(command)):
                    continue
                Command.ExecuteAndATALog(command)


def Debug(root):
    print('==============================')
    print('     Enter Ant Process')
    print('==============================')

    setAntHome(root)
    setJavaHome(root)
    compiler = getCompiler(root)
    option = getOption(root)
    targets = getTarget(root)
    buildfiles = list(root)
    for buildfile in buildfiles:
        file = buildfile.text
        log = getLogPath(file)
        for target in targets:
            command = getCompileCommand(compiler, file, target, option)
            print(command + 'log to ' + log)


def setAntHome(root):
    antHome = root.attrib.get('ANT_HOME', '')
    os.environ['ANT_HOME']=antHome


def setJavaHome(root):
    javaHome = root.attrib.get('JAVA_HOME', '')
    os.environ['JAVA_HOME']=javaHome


def getCompiler(root):
    antHome = root.attrib.get('ANT_HOME', '')
    compiler = antHome + '/bin/ant'
    return compiler


def getOption(root):
    option = root.attrib.get('opt', '')
    return option


def getTarget(root):
    target = root.attrib.get('target', '')
    targetlist = target.split(',')
    return targetlist


def getCompileCommand(compiler, file, target, option):
    command = compiler + ' -f ' + file + ' ' + target + ' ' + option
    return command


def getLogPath(file):
    fileName = os.path.basename(file)
    logName = fileName.replace('.xml', '.log')
    logPath = 'log/' + logName
    return logPath
