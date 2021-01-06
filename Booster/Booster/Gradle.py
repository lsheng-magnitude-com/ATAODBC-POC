from __future__ import print_function
import os
import Command
import ata.log
from Booster.Debug import Debug as Debugger

logger = ata.log.AtaLog(__name__)

def _doExecute(root, isDebug):
    print('==============================')
    print('     Enter Gradle Process')
    print('==============================')

    setJavaHome(root)
    tasks = getTask(root)
    buildsources = list(root)
    for buildsource in buildsources:
        source=buildsource.text
        for task in tasks:
            try:
                command = getCompileCommand(task)
                logger.info(command)
                if not isDebug:
                    Command.ExecuteAndATALog(command, source)
                else:
                    logger.info('cwd:' + source)
                    logger.info('Executing ' + command)
            except:
                stopGradleDaemons(source)
                exit(-1)
        stopGradleDaemons(source)



def Execute(root):
    _doExecute(root, False)


def Debug(root):
    _doExecute(root, True)


def setJavaHome(root):
    javaHome = root.attrib.get('JAVA_HOME', '')
    os.environ['JAVA_HOME']=javaHome


def getTask(root):
    task = root.attrib.get('task', '')
    tasklist = task.split(',')
    return tasklist


def getCompileCommand(task):
    if task == 'setup':
        if os.name == 'nt': command = 'gradlew.bat'
        else: command = 'gradlew'
    else:
        command = 'gradlew ' + task
    return command


def stopGradleDaemons(source):
    stopcommand = 'gradlew --stop'
    Command.ExecuteAndATALog(stopcommand, source)
