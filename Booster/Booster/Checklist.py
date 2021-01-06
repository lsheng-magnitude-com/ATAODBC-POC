from __future__ import print_function

import os
import ata.log
import fnmatch
from Booster.Debug import Debug as Debugger
from Booster.XMLFile import XMLFile, getFileName
from Booster.XMLFile import dumpXMLNode
from BoosterError import FileNotFoundError, AdditionalFileError, BoosterError

logger = ata.log.AtaLog(__name__)

def Execute(root):
    print('==============================')
    print('        Check List')
    print('==============================')
    
    basedir = getBaseDir(root)
    packageName = getPackageName(root)
    MissingFileErrorRaiseList = []
    AdditionalFileErrorRaiseList = []
    checklistfile = getChecklistFile(root)
    logger.info('--- Running current checklist: ' + checklistfile)
    (checklistSet, removeSet) = generateChecklistSet(checklistfile)
    checklist = combineChecklists(checklistSet, basedir)
    checklist = removeDuplicate(checklist)
    removelist = combineChecklists(removeSet,basedir)
    checklist = subtractChecklist(checklist,removelist)
    packagelist = list(scanFolder(basedir + '/' + packageName))
    missingfiles = validateChecklist(checklist, packagelist, MissingFileErrorRaiseList)
    print('==============================')
    logger.info('=== Scanning ' + packageName + ' ===')   
    additionalfiles = validatePackage(checklist, packagelist, AdditionalFileErrorRaiseList)
    if missingfiles != 0 or additionalfiles != 0:
        exit(-1)


def Debug(root):
    print('==============================')
    print('        Check List')
    print('==============================')

    basedir = getBaseDir(root)
    packageName = getPackageName(root)
    MissingFileErrorRaiseList = []
    AdditionalFileErrorRaiseList = []
    checklistfile = getChecklistFile(root)
    logger.info('--- checklist 1: ' + checklistfile)
    (checklistSet, removeSet)= generateChecklistSet(checklistfile, basedir)
    print('checklistSet' + str(checklistSet))
    checklist = combineChecklists(checklistSet, basedir)
    print('checklist' + str(checklist))
    checklist = removeDuplicate(checklist)
    removelist = combineChecklists(removeSet,basedir)
    checklist = subtractChecklist(checklist,removelist)
    print('checklist' + str(checklist))
    packagelist = list(scanFolder(basedir + '/' + packageName))
    validateChecklist(checklist, packagelist, MissingFileErrorRaiseList) 
    for item in checklist:
        logger.info("== Check files ==")
        logger.info(item)


def getBaseDir(root):
    return root.attrib.get('basedir', os.getcwd())


def getPackageName(root):
    return root.attrib.get('packageName')
   
   
def getChecklistFile(root):
    return root.text
    
def combineChecklists(checklistSet, cwd):
    checklist = []
    for file in checklistSet:
        checklist = checklist + generateChecklist(file, cwd)
    return checklist

def generateChecklist(inputFile, cwd):
    try:
        xml = XMLFile(inputFile)
    except Exception as e:
        logger.info("== Checklist File issue found ==")
        logger.info("%s is %s" % (inputFile, e))
    root = xml.root()
    root.attrib['name'] = cwd
    checklist=[]
    checklist = appendSubDir(root, checklist)
    return checklist

def appendSubDir(node, checklist):
    for child in list(node):
        if child.tag == 'directory':
            child.attrib['name'] = node.attrib.get('name') + '/' + child.attrib.get('name')
            if len(list(child)) == 0:
                folderPath = os.path.realpath(child.attrib.get('name'))
                checklist.append(folderPath)
            else:
                appendSubDir(child, checklist)    
        if child.tag == 'file':
            child.attrib['name'] = node.attrib.get('name') + '/' + child.attrib.get('name')
            filePath = os.path.realpath(child.attrib.get('name'))
            checklist.append(filePath)
        if child.tag == 'archive':
            child.attrib['name'] = node.attrib.get('name')
            appendSubDir(child, checklist)
    return checklist

def generateChecklistSet(inputFile):
    try:
        xml = XMLFile(inputFile)
    except Exception as e:
        logger.info("== Checklist File issue found ==")
        logger.info("%s is %s" % (inputFile, e))
    root = xml.root()
    checklistSet = set()
    removeSet = set()
    checklistSet.add(inputFile)
    (checklistSet, removeSet) = appendChecklist(root, checklistSet, removeSet)
    return (checklistSet, removeSet)
    
def appendChecklist(node, checklistSet, removeSet):
    findRemoveSet(node, removeSet)
    for child in list(node):
        if child.tag == 'append':
            if child.text in checklistSet:
                continue
            checklistSet.add(child.text)
            try:
                xml = XMLFile(child.text)
            except Exception as e:
                logger.info("== Checklist File issue found ==")
                logger.info("%s is %s" % (child.text, e))    
            root = xml.root()
            logger.info('=== Finding <append> checklist: ' + child.text + ' ===')
            (checklistSet, removeSet)= appendChecklist(root, checklistSet, removeSet)          
    return (checklistSet, removeSet)

def findRemoveSet(node, removeSet):
    for child in list(node):
        if child.tag == 'subtract':
            if child.text in removeSet:
                continue
            removeSet.add(child.text)
            try:
                xml = XMLFile(child.text)
            except Exception as e:
                logger.info("== Checklist File issue found ==")
                logger.info("%s is %s" % (child.text, e))    
            root = xml.root()
            logger.info('=== Finding <subtract> checklist: ' + child.text + ' ===')
            for child in list(root):
                if child.tag == 'subtract':
                    logger.error ('=== Unexpected <subtract> tag within subtracting file ===')
                elif child.tag == 'append':
                    logger.error ('=== Unexpected <append> tag within subtracting file ===')
    return removeSet 
            
def removeDuplicate(checklist):
    list = []
    for item in checklist:
        if item not in list:
            list.append(item)
    return list

def subtractChecklist(checklist,removelist):
    list = []
    for item in checklist:
        if item not in removelist:
            list.append(item)
    return list

def scanFolder(directory_path, pattern="*"):
    for dirpath, dirnames, filenames in os.walk(directory_path):
        for file_name in filenames:
            yield os.path.join(os.path.realpath(dirpath), file_name)
        for dir_name in dirnames:
            if not os.listdir(os.path.join(dirpath, dir_name)):
                yield os.path.join(os.path.realpath(dirpath), dir_name)
        

def validateChecklist(checklist, packagelist, MissingFileErrorRaiseList):
    missingfiles = 0
    missingfilelist = []
    existingfilelist = []
     
    for item in checklist:
        if item not in packagelist:
            logger.info(item + ' does not exist')
            missingfiles = missingfiles + 1
            missingfilelist.append(item)
            MissingFileErrorRaiseList.append(item)
        else:
            existingfilelist.append(item)
    for fileName in existingfilelist:
        logger.info (fileName)
    if missingfiles == 0:
        logger.info ('=== Base on checklists, All ' + str(len(checklist)) + ' files exist ===')
    else:
        logger.critical ('=== Missing '+ str(missingfiles) + ' files ===')
        for file in MissingFileErrorRaiseList:
            logger.critical(file)
    return missingfiles


def validatePackage(checklist, packagelist, AdditionalFileErrorRaiseList):
    additionfiles = 0
    additionfileslist = []
    existingfilelist = []
    
    for item in packagelist:
        if item not in checklist:
            logger.info(item + ' is additional file/folder')
            additionfiles = additionfiles + 1
            additionfileslist.append(item)
            AdditionalFileErrorRaiseList.append(item)
        else:
            existingfilelist.append(item)
    for fileName in existingfilelist:
        logger.info (fileName)        
    if additionfiles == 0:
        logger.info ('=== Scan package folder ' + str(len(packagelist)) + ' files , No additional files ===')
    else:
        logger.critical ('=== Additional '+ str(additionfiles) + ' files/folders ===')
        for file in AdditionalFileErrorRaiseList:
            logger.critical(file)
    return additionfiles
        
        
        

