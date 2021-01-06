from __future__ import print_function

import glob

import ata.log
from Booster.Debug import Debug as Debugger
from BoosterError import BoosterTagError
from ssh_client import SSHClient

logger = ata.log.AtaLog(__name__)


def Execute(root):
    print('==============================')
    print('          Enter Scp')
    print('==============================')

    source_files = get_source(root)
    ignore_empty_source = root.attrib.get('ignoreEmptySource', 'false')
    if ignore_empty_source == 'true':
        source_exist = False
        for sourcefile in source_files:
            source = sourcefile.text
            if len(glob.glob(source)) != 0:
                source_exist = True
        if not source_exist:
            logger.info('source files are empty.')
            logger.info('skip the copy.')
            return
    dest = get_dest(root)
    if Debugger().skip('scp', '----Skip: Scp to {}'.format(dest)):
        return
    private_key = root.attrib.get('privateKey', None)
    ssh_client = SSHClient(private_key=private_key)
    for sourcefile in source_files:
        source = sourcefile.text
        ssh_client.scp(source, dest)


def Debug(root):
    print('==============================')
    print('          Enter Scp')
    print('==============================')

    dest = get_dest(root)
    sourcefiles = get_source(root)
    for sourcefile in sourcefiles:
        source = sourcefile.text
        logger.info("Scp {source} to {dest}".format(source=source, dest=dest))


def get_dest(root):
    dest = root.attrib.get('dest', None)
    if not dest:
        raise BoosterTagError(__name__, "dest attribute is missing")
    return dest


def get_source(root):
    return list(root)
