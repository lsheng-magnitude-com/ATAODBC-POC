from __future__ import print_function

import glob

import ata.log
from Booster.Debug import Debug as Debugger
from BoosterError import BoosterTagError
from ssh_client import SSHClient

logger = ata.log.AtaLog(__name__)


def Execute(root):
    print('==============================')
    print('          Enter SSH')
    print('==============================')

    host = getHost(root)
    verbose = root.attrib.get('verbose', None)
    cmdList = getCmd(root)
    private_key = root.attrib.get('privateKey', None)
    ssh_client = SSHClient(private_key=private_key)
    if verbose == 'silent':
        for cmd in cmdList:
            ssh_client.execute_on_host_in_slient(host, cmd)
    else:
        for cmd in cmdList:
            ssh_client.execute_on_host(host, cmd)


def Debug(root):
    print('==============================')
    print('          Enter SSH')
    print('==============================')

    host = getHost(root)
    cmdList = getCmd(root)
    for cmd in cmdList:
        ssh_client.execute_on_host(host, cmd)


def getHost(root):
    host = root.attrib.get('host', None)
    if not host:
        raise BoosterTagError(__name__, "host is not specified")
    return host


def getCmd(root):
    cmdList = []
    for item in list(root):
        cmdList.append(item.text)
    return cmdList


def run(host, key, command, isDebug=False):
    if isDebug:
        logger.info("host={0} command={1}".format(host, command))
    else:
        ssh_client = SSHClient(private_key=key)
        ssh_client.execute_on_host(host, command)

