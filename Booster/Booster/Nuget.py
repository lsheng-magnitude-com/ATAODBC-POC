from __future__ import print_function
import os
import Command

from contextlib import contextmanager

def Execute(root):
    print('==============================')
    print('          Enter Nuget')
    print('==============================')

    archive = getDest(root)
    source = getSource(root)
    spec = root.attrib.get('spec', '')
    version = root.attrib.get('version', '1.0.0')
    if not os.path.exists(spec):
        print(spec + ' does not exit')
        exit(-1)
    print('Create ' + archive + '.nupkg from ' + spec)
    createNuget(archive, spec, source, version)


def Debug(root):
    print('==============================')
    print('          Enter Nuget')
    print('==============================')

    archive = getDest(root)
    file = getSource(root)
    print('Create ' + archive + '.nupkg from ' + file)


def getDest(root):
    baseName = root.attrib.get('dest', 'Packages')
    return baseName


def getSource(root):
    sourceDir = root.text
    return sourceDir


def createNuget(dest, nugetPath, source, version='1.0.0'):
    command = 'nuget pack ' + nugetPath + ' -Version ' + version + ' -BasePath ' + source + ' -OutputDirectory ' + dest
    return Command.ExecuteAndGetResult(command)
