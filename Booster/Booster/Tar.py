from __future__ import print_function
import os

import Command
import platform
from Booster.Debug import Debug as Debugger


def Execute(root):
    print('==============================')
    print('          Enter Tar ')
    print('==============================')
    dbg = Debugger()

    exclude_root = root.attrib.get('exclude_root', 'false')
    tar_extension = root.attrib.get('tar_extension', 'false')
    archive = getDest(root)
    file = getSource(root)
    if dbg.skip('tar', '---- Skip tar {}'.format(archive)):
        return
    if not os.path.exists(file):
        print(file + ' does not exit')
        raise Exception('{} does not exist'.format(file))
        # exit(-1)
    if (tar_extension == 'true'):
        print('Create ' + archive + '.tar from ' + file)
    else:
        print('Create ' + archive + '.tar.gz from ' + file)
    
    if (exclude_root == 'true'):
        if (tar_extension == 'true'):
            createTar(archive, file, True, True)
        else:
            createTar(archive, file, True, False)
    else:
        if (tar_extension == 'true'):
            createTar(archive, file, False, True)
        else:
            createTar(archive, file)

def Debug(root):
    print('==============================')
    print('          Enter Tar ')
    print('==============================')

    archive = getDest(root)
    file = getSource(root)
    print('Create ' + archive + '.tar.gz from ' + file)


def getDest(root):
    tarball = root.attrib.get('dest', 'build.tar.gz')
    baseName = tarball[:-7]
    return baseName


def getSource(root):
    return root.text


def createTar(archive_name, source, exclude_root=False, extension=False):
    current_platform = platform.system()
    if exclude_root:
        if extension:
            if current_platform == 'Linux' or current_platform == 'AIX' or current_platform == 'HP-UX':
                command = "tar -vcf {}.tar *"
            else:
                command = "tar -vcf - * > {}.tar"
            Command.ExecuteAndGetResult(command.format(archive_name), cwd=source)
        else:
            if current_platform == 'Linux' or current_platform == 'AIX' or current_platform == 'HP-UX':
                command = "tar -vczf {}.tar.gz *"
            else:
                command = "tar -vcf - * | gzip > {}.tar.gz"
            Command.ExecuteAndGetResult(command.format(archive_name), cwd=source)
    else:
        rootDir = os.path.dirname(source)
        #if rootDir != '':
        #    os.chdir(rootDir)
        baseDir = os.path.basename(source)
        if extension:
            if current_platform == 'Linux' or current_platform == 'AIX' or current_platform == 'HP-UX':
                command = "tar -vcf {archive_name}.tar {baseDir}"
            else:
                command = "tar -vcf - {baseDir} > '{archive_name}.tar'"
            Command.ExecuteAndGetResult(command.format(baseDir=baseDir, archive_name=archive_name), cwd=rootDir)
        else:
            if current_platform == 'Linux' or current_platform == 'AIX' or current_platform == 'HP-UX':
                command = "tar -vczf {archive_name}.tar.gz {baseDir}"
            else:
                command = "tar -vcf - {baseDir} | gzip > '{archive_name}.tar.gz'"
            Command.ExecuteAndGetResult(command.format(baseDir=baseDir, archive_name=archive_name), cwd=rootDir)
