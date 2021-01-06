from __future__ import print_function
import os
import Command
import ata.log


def Execute(root):
    print('==============================')
    print('     Enter PackageRenamer')
    print('==============================')

    java = getJave(root)
    jarFileList = getJarFile(root)
    packageRenamer = getPackageRenamer(root)
    oldPkgName = getOldPackageName(root)
    newPkgName = getNewPackageName(root)
    replaceOldJar = getReplaceOldJarFlag(root)
    useOldBehaviour = getUseOldBehaviourFlag(root)
    for element in jarFileList:
        jarFile = element.text
        command = getRenameComamnd(java, jarFile, packageRenamer, oldPkgName, newPkgName, useOldBehaviour)
        RenamePackage(command, jarFile, replaceOldJar)


def Debug(root):
    print('==============================')
    print('     Enter PackageRenamer')
    print('==============================')

    java = getJave(root)
    jarFileList = getJarFile(root)
    packageRenamer = getPackageRenamer(root)
    oldPkgName = getOldPackageName(root)
    newPkgName = getNewPackageName(root)
    replaceOldJar = getReplaceOldJarFlag(root)
    useOldBehaviour = getUseOldBehaviourFlag(root)
    for element in jarFileList:
        jarFile = element.text
        command = getRenameComamnd(java, jarFile, packageRenamer, oldPkgName, newPkgName, useOldBehaviour)
        print(command)


def getJave(root):
    default = os.environ.get('BOOSTER_VAR_JAVAEXE','java')
    java = root.attrib.get('java', default)
    return java


def getJarFile(root):
    return list(root)


def getPackageRenamer(root):
    return root.attrib.get('packageRenamer', 'SimbaPackageRenamer.jar')


def getOldPackageName(root):
    return root.attrib.get('oldPackageName', 'undef')


def getNewPackageName(root):
    return root.attrib.get('newPackageName', 'undef')


def getReplaceOldJarFlag(root):
    return root.attrib.get('replaceOldJar', 'true')


def getUseOldBehaviourFlag(root):
    if root.attrib.get('useOldBehaviour', 'false') == 'true':
        return ' -useOldBehaviour '
    else:
        return ' '


def getRenameComamnd(java, jarFile, packageRenamer, oldPkgName, newPkgName, useOldBehaviour):
    if oldPkgName == 'undef':
        command = java + ' -jar ' + packageRenamer + useOldBehaviour + jarFile + ' ' + newPkgName
    else:
        command = java + ' -jar ' + packageRenamer + useOldBehaviour + '-packageToRename ' + oldPkgName + ' ' + jarFile + ' ' + newPkgName
    return command


def RenamePackage(command, jarFile, replaceOldJar='true'):
    Command.ExecuteAndLogVerbose(command)
    if replaceOldJar == 'true':
        newJar = jarFile.replace('.jar', '_new.jar')
        os.remove(jarFile)
        os.rename(newJar, jarFile)




