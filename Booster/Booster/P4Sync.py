from __future__ import print_function
import os
import Command
from Booster.Debug import Debug as Debugger


def Execute(root):
    print('==============================')
    print('          Enter P4Sync')
    print('==============================')

    longLabel = root.attrib.get('label', 'head')
    (label, changelists) = parseLabel(longLabel)
    p4 = getP4Exe()
    for element in list(root):
        depot = element.text
        sync(p4, depot, label)
    for cl in changelists:
        unshelve(p4, cl)


def Debug(root):
    print('==============================')
    print('          Enter P4Sync')
    print('==============================')

    longLabel = root.attrib.get('label', 'head')
    (label, changelists) = parseLabel(longLabel)
    p4 = getP4Exe()
    for element in list(root):
        depot = element.text
        print(p4 + ' sync -f ' + depot + label)
    for cl in changelists:
        print(p4 + ' unshelve -s ' + cl)


def sync(p4, depot, label):
    revertCommand = p4 + ' revert ' + depot
    cleanCommand = p4 + ' -s sync -f ' + depot + '#0'
    SyncCommand = p4 + ' -s sync ' + depot + label
    if Debugger().skip('p4sync', '----Skip: {}'.format(SyncCommand)):
        return
    Command.ExecuteAndGetResult(revertCommand)
    Command.ExecuteAndGetResult(cleanCommand)
    Command.ExecuteAndGetResult(SyncCommand)


def unshelve(p4,changelist):
    command = p4 + ' -s unshelve -f -s ' + changelist
    if (changelist != ''):
        if Debugger().skip('p4sync', '----Skip: {}'.format(command)):
            return
        Command.ExecuteAndGetResult(command)


def unshelvedepot(p4exe, changelist, depot):
    command = p4exe + ' unshelve -s ' + changelist + ' ' + depot
    if (changelist != ''):
        if Debugger().skip('p4sync', '----Skip: {}'.format(command)):
            return
        Command.ExecuteAndGetResult(command)


def tag():
    print('')


def parseLabel(longLabel):
    longLabel = longLabel.replace('__CL', '__')
    labelArray = longLabel.split('__')
    if 'head' in longLabel:
        return '#' + labelArray[0], labelArray[1:]
    else:
        return '@' + labelArray[0], labelArray[1:]


def getP4Exe(quoted=True):
    p4Exe = os.environ.get('BAMBOO_CAPABILITY_SYSTEM_P4EXECUTABLE','p4')
    if quoted:
        p4Exe = '"' + p4Exe + '"'
    return p4Exe
