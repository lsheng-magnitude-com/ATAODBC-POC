from __future__ import print_function

import ata.log
from BoosterError import BoosterTagError
from ssh_client import SSHClient

logger = ata.log.AtaLog(__name__)


def Execute(root):
    print('==============================')
    print('        Enter RemoteCommand')
    print('==============================')

    command = root.text
    private_key = root.attrib.get('privateKey', None)
    host = root.attrib.get('host', None)
    if not host:
        raise BoosterTagError(__name__, "host attribute is missing")
    ssh_client = SSHClient(private_key=private_key)
    ssh_client.execute_on_host(host, command)


def Debug(root):
    print('==============================')
    print('        Enter RemoteCommand')
    print('==============================')

    command = root.text
    private_key = root.attrib.get('privateKey', None)
    host = root.attrib.get('host', None)
    if not host:
        raise BoosterTagError(__name__, "host attribute is missing")
    logger.info("Run {cmd} on {host} using private key {key}".format(cmd=command, host=host, key=private_key))
