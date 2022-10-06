import os
import sys
import tarfile
import zipfile
from shutil import copy
from Booster.Debug import Debug as Debugger
import ata.log
import BoosterError

logger = ata.log.AtaLog(__name__)



def Execute(root):
    print('==============================')
    print('     Enter Extract')
    print('==============================')
    dest = getDest(root)
    sourcefiles = getSource(root)
    debug_skip = Debugger().skip('extract')
    required = root.attrib.get('required', 'false')
    for sourcefile in sourcefiles:
        file = sourcefile.text
        if debug_skip:
            logger.info('----Skip: extract ' + file + ' to ' + dest)
        elif os.path.exists(file):
            copy(file, './')
            archive = os.path.basename(file)
            # print('extract ' + archive + ' to ' + dest)
            logger.info('extract ' + file + ' to ' + dest)
            extractArchive(archive, dest)
        else:
            logger.warning('attempt to extract ' + file + ' failed')
            if required.lower() == 'true':
                raise BoosterError.FileNotFoundError(__name__, 'the required package {} does not exist'.format(file))
            else:
                logger.warning('Warning: ' + file + ' does not exist\n')

def Debug(root):
    print('==============================')
    print('     Enter Extract')
    print('==============================')

    dest = getDest(root)
    sourcefiles = getSource(root)
    for sourcefile in sourcefiles:
        file = sourcefile.text
        archive = os.path.basename(file)
        print('extract ' + archive + ' to ' + dest)


def getDest(root):
    dest = root.attrib.get('dest', './')
    if not os.path.isdir(dest):
        os.makedirs(dest)
    return dest


def getSource(root):
    return list(root)


def extractArchive(archive, dest):
    if (zipfile.is_zipfile(archive) is True):
        with zipfile.ZipFile(archive, 'r') as zip:
            zip.extractall(dest)
    if (tarfile.is_tarfile(archive) is True):
        try:
            with tarfile.open(archive, 'r:gz') as tar:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tar, dest)
        except:
            try:
                with tarfile.open(archive, 'r') as tar:
                    def is_within_directory(directory, target):
                        
                        abs_directory = os.path.abspath(directory)
                        abs_target = os.path.abspath(target)
                    
                        prefix = os.path.commonprefix([abs_directory, abs_target])
                        
                        return prefix == abs_directory
                    
                    def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                    
                        for member in tar.getmembers():
                            member_path = os.path.join(path, member.name)
                            if not is_within_directory(path, member_path):
                                raise Exception("Attempted Path Traversal in Tar File")
                    
                        tar.extractall(path, members, numeric_owner=numeric_owner) 
                        
                    
                    safe_extract(tar, dest)
            except:
                pass