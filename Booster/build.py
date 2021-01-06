# This script is used to initialize all configurations for the build
# We can have multiple ways to get configurations
# Read from config file
# Read from Skipper
# Read from env variable
from __future__ import print_function
import glob
import os
import os.path
import weakref
import xml.etree.ElementTree as ET
from Booster.XMLFile import XMLFile

import Booster
import ata.log
logger = ata.log.AtaLog(__name__)
from Booster.Debug import Debug as Debugger
from Booster.Var import VarMgr

_skipNodeList = ('variables', 'bamboovariables')
def skipnode(e):
    if e.tag.lower() in _skipNodeList:
        return True
    p = e.parent
    if p is None or p().tag.lower() in _skipNodeList:
        return True
    return False


def Execute(configfile):
    #print('Start executing all build files')
    logger.info('Start executing all build files')
    process(configfile)
    #print('Finish executing all build files')
    logger.info('Finish executing all build files')
    #createArtifacts()

# Start executing all the actions defined in build file in sequence
def process(file):
    xml = XMLFile(file)
    dbg = Debugger()
    logger.info('--Enter ' + os.path.basename(file) + '--')
    for element in xml.iter():
        if (element.tag == 'Import'):
            process(element.text)
            logger.info('--Enter ' + os.path.basename(file) + '--')
            continue

        if skipnode(element): continue

        if element.tag == 'Debug':
            # TODO - insert Debug tag
            if Debugger().trace('exec'):
                d = VarMgr()
                d.dumpAll()
                d.dumpOverride()

        module_name = 'Booster.' + element.tag
        brk = element.attrib.get('break', '')
        if brk.lower() == 'true':
            pass
        try:
            if dbg.trace('var'):
                print('+++++ process: {}:{} ....'.format(file, element.tag))
            if ('BOOSTERDEBUG' in os.environ):
                eval(module_name + '.Debug')(element)
            else:
                eval(module_name + '.Execute')(element)
                pass # just a breakpoint holder
        except (AttributeError, SyntaxError):
            continue


def createArtifacts():
    baseDir = os.getcwd()
    #buildFileDir = baseDir + '/build'
    logDir = baseDir + '/log'
    # Change file type to xml for easy reading
    #for file in glob.glob(buildFileDir + '/*'):
    #    newFileName = file + '.xml'
    #    os.rename(file, newFileName)
    # Zip up log
    Booster.Zip.createZip('log', logDir)



