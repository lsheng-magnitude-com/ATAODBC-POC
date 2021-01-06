from __future__ import print_function
import fileinput
import os
import Remove
import re
import ata.log
import sys
from BoosterError import BoosterTagError, FileNotFoundError

logger = ata.log.AtaLog(__name__)

def Execute(root):
    print('==============================')
    print('     Enter ReplaceInFile')
    print('==============================')

    files = getFile(root)
    for element in list(root):
        source = element.text
        dest = element.attrib.get('newstring', '')
        useRegex = element.attrib.get('regex', 'False')
        print(source + ' => ' + dest)
        for file in files:
            replace(file, source, dest, useRegex)


def Debug(root):
    print('==============================')
    print('     Enter ReplaceInFile')
    print('==============================')

    files = getFile(root)
    for element in list(root):
        source = element.text
        dest = element.attrib.get('newstring', '')
        print(source + ' => ' + dest)


def getFile(root):
    file = root.attrib.get('file', 'undef')
    bulkReplace = root.attrib.get('bulkReplace', 'false')
    fileLists = []
    if file == 'undef':
        print('file not specified')
        raise BoosterTagError(__name__, detail="file attribute is not specified")
        # exit(-1)

    if bulkReplace == 'false':
        logger.info("Replace in file : " + file)
        if not os.path.isfile(file):
            print('Can not find file ' + file)
            raise FileNotFoundError(__name__, detail=file)
            # exit(-1)
        else:
            fileLists.append(file)

    else:
        logger.info("Bulk Replace in all files under: " + file)
        for path, subdirs, files in os.walk(file):
            for name in files:
                fileLists.append(os.path.join(path, name))
    return fileLists


def replace(file, source, dest, useRegex=None, re_flags=0):
    Remove.removeSingleFile(file + '.bak')
    if isinstance(useRegex, basestring):
        useRegex = useRegex.upper() == 'TRUE'
    elif re_flags != 0:
        useRegex = True
    f = fileinput.FileInput(file, inplace=True, backup='.bak')
    try:
        for line in f:
            if useRegex:
                line = re.sub(source, dest, line, flags=re_flags)
                sys.stdout.write(line)
            else:
                sys.stdout.write(line.replace(source, dest))
    finally:
        f.close()
    Remove.removeSingleFile(file + '.bak')
