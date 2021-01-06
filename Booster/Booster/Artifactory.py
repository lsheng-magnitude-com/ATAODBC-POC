from __future__ import print_function

import os
import platform
import Command
import ata.log

logger = ata.log.AtaLog(__name__)


def _doExecute(root, isDebug):
    print('=========================')
    print('      Enter GTest        ')
    print('=========================')

    curl = getCurl(root)
    dest = getDest(root)
    request = getRequest(root)
    user, password = getCredential(root)
    files = list(root)
    for file in files:
        command = getCommand(curl, dest, request, user, password, file.text)
        if isDebug:
            logger.info(command)
        else:
            Command.ExecuteAndLogVerbose(command)

def Execute(root):
    try:
        _doExecute(root, False)
    except:
        import traceback
        traceback.print_exc()
        exit(-1)


def Debug(root):
    _doExecute(root, True)


def getCurl(root):
    if platform.system() == 'AIX':
        default = 'export LIBPATH=$LIBPATH:/bamboo/opt/curl/ && /bamboo/opt/curl/curl'
    elif platform.system() == 'HP-UX':
        default = 'export LD_LIBRARY_PATH=${LD_LIBRARY_PATH:+LD_LIBRARY_PATH:}:/bamboo/opt/curl/ && /bamboo/opt/curl/curl'
    elif os.environ.get('BOOSTER_VAR_DISTRIBUTION', 'undef') == 'solaris10sparc' or os.environ.get('BOOSTER_VAR_DISTRIBUTION', 'undef') == 'solaris10x86':
        default = '/opt/csw/bin//curl'
    elif platform.system() == 'Windows':
        default = 'C:/opt/curl/bin/curl'
    else:
        default = 'curl'
    return root.attrib.get('curl', default)


def getDest(root):
    return root.attrib.get('dest', 'undef')


def getRequest(root):
    return root.attrib.get('request', 'undef')


def getCredential(root):
    user = root.attrib.get('user', 'bamboo')
    default_pwd = os.environ.get('BAMBOO_ARTIFACTORY_PASSWORD', 'undef')
    password = root.attrib.get('password', default_pwd)
    return user, password


def getCommand(curl, dest, request, user, password, file):
    if request == 'upload':
        command = curl + ' -u ' + user + ':' + password + ' -X PUT ' + os.path.join(dest, os.path.basename(file)).replace('\\', '/') + ' -T ' + file
    if request == 'download':
        if not os.path.isdir(dest):
            os.umask(0o000)
            os.makedirs(dest, 0o0777)
        command = curl + ' -u ' + user + ':' + password + ' ' + file + ' -o ' + os.path.join(dest, os.path.basename(file))
    return command