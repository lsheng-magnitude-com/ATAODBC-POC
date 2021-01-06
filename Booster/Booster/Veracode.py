from __future__ import print_function
import os
import time
import xml.etree.ElementTree as ET
import ata.log
import Command
import subprocess
from XMLFile import XMLFile
from Remove import removeSingleFile
logger = ata.log.AtaLog(__name__)
PRESCAN_RESULT_LOG = 'prescanresult.xml'

def _doExecute(root, isDebug):
    print('==============================')
    print('       Enter Veracode')
    print('==============================')

    appid = getAppID(root)
    print((appid))
    file = getFile(root)
    print((file))
    autoscan = getAutoscan(root)
    userid = getUserID()
    print((userid))
    pwd = getPWD()
    print((pwd))
    java = getjava(root)
    print((java))
    restclient = getRestClient(root)
    print((restclient))
    if not isDebug:
        runUpload(appid, file, userid, pwd, java, restclient)
        runBeginprescan(appid, userid, pwd, java, restclient, autoscan)
        runGetprescanresults(appid, userid, pwd, java, restclient)
        modules = parsePreScanResult()
        runBeginscan(appid, userid, pwd, java, restclient, modules)
    else:
        runVeracodeDebug(id, pwd)


def Execute(root):
    _doExecute(root, False)


def Debug(root):
    _doExecute(root, True)


def getjava(root):
    default = '"' +os.path.join(os.environ.get('BOOSTER_VAR_JDK1_8_HOME','undef'),'bin','java') + '"'
    return root.attrib.get('java',default)


def getRestClient(root):
    default = os.path.join(os.environ.get('BOOSTER_VAR_BTAUTILS_DIR','undef'),'VeracodeRestClient','VeracodeJavaAPI.jar')
    return root.attrib.get('restclient',default)


def getAppID(root):
    id = root.attrib.get('appid', 'undef')
    return id


def getFile(root):
    return root.text


def getAutoscan(root):
    return root.attrib.get('autoscan', 'false')


def getUserID():
    pwd = os.environ.get('BAMBOO_VERACODE_ID', 'undef')
    if pwd == 'undef':
        logger.error('*** Missing Veracode Password ***')
    else:
        return pwd


def getPWD():
    pwd = os.environ.get('BAMBOO_VERACODE_PASSWORD', 'undef')
    if pwd == 'undef':
        logger.error('*** Missing Veracode Password ***')
    else:
        return pwd


def parseResult(result, action):
    root = ET.fromstring(result)
    if root.tag == 'error':
        logger.error('*** Veracode ' + action + ' failed ***')
        logger.error(result)
        exit(-1)
    else:
        logger.info(result)


def runUpload(appid, file, userid, pwd, java, restclient):
    command = java + ' -jar ' + restclient + ' -vid ' + userid + ' -vkey ' + pwd + ' -action uploadfile -appid ' + appid + ' -filepath ' + file
    Command.ExecuteAndLogVerbose(command)


def runBeginprescan(appid, userid, pwd, java, restclient, autoscan):
    command = java + ' -jar ' + restclient + ' -vid ' + userid + ' -vkey ' + pwd + ' -action beginprescan -appid ' + appid + ' -autoscan ' + autoscan
    Command.ExecuteAndLogVerbose(command)


def runGetprescanresults(appid, userid, pwd, java, restclient):
    command = java + ' -jar ' + restclient + ' -vid ' + userid + ' -vkey ' + pwd + ' -action getprescanresults -appid ' + appid
    if os.path.exists(PRESCAN_RESULT_LOG):
        removeSingleFile(PRESCAN_RESULT_LOG)
    try:
        Command.ExecuteAndLog(command, PRESCAN_RESULT_LOG)
    except subprocess.CalledProcessError as error:
        if 'Prescan results not available' in error.output:
            logger.info('Prescan still in progress. Try in 120s')
            time.sleep(120)
            runGetprescanresults(appid, userid, pwd, java, restclient)
        else:
            logger.critical('Prescan Failed')
            exit(-1)


def parsePreScanResult():
    with open(PRESCAN_RESULT_LOG, 'r') as fin:
        print(fin.read())
    try:
        xml = XMLFile(PRESCAN_RESULT_LOG)
    except Exception as e:
        logger.info('Failed to parse prescanresult.xml')
        logger.error(e)
        exit(-1)
    root = xml.root()
    modules = ''
    for element in root.iter():
        if element.attrib.get('is_dependency', 'true') == 'false':
            modules = modules + ',' + element.attrib.get('id')
    return modules[1:]


def runBeginscan(appid, userid, pwd, java, restclient, modules):
    command = java + ' -jar ' + restclient + ' -vid ' + userid + ' -vkey ' + pwd + ' -action beginscan -appid ' + appid + ' -modules ' + modules
    Command.ExecuteAndLogVerbose(command)
