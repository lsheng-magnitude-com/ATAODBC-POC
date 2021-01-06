from __future__ import print_function
import os

import Remove
import ata.log

logger = ata.log.AtaLog(__name__)


def Execute(root):
    print('==============================')
    print('     Enter CreateFile')
    print('==============================')

    file = getFile(root)
    content = getContent(root)
    logger.info('Create ' + file)
    writeFile(file, content)


def Debug(root):
    Execute(root)


def getFile(root):
    file = root.attrib.get('file', 'undef')
    dir = os.path.dirname(file)
    if file == 'undef':
        logger.info('file not specified')
        exit(-1)
    if os.path.exists(file):
        Remove.removeSingleFile(file)
    if not os.path.exists(dir) and dir != '':
        os.umask(000)
        os.makedirs(dir, 0o777)
    return file


def getContent(root):
    c = [item.strip() for item in root.text.splitlines()]
    output = '\n'.join(c)
    return output


def writeFile(file, content):
    with open(file, 'w') as f:
        f.write(content)
