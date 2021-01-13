# This script is used to initialize all configurations for the build
# We can have multiple ways to get configurations
# Read from config file
# Read from Skipper
# Read from env variable
from __future__ import print_function
import os
import os.path
import platform
import shutil
import xml.etree.ElementTree as ET
import socket

import errno

from Booster import Command
import ata.log
from Booster.Var import VarMgr
from Booster.Debug import Debug as Debugger
import Booster.Var as Var
from Booster.Debug import Debug as Debugger
from Booster.XMLFile import XMLFile, getFileName
from Booster.XMLFile import dumpXMLNode
from Booster import P4Sync
from Booster.P4Sync import getP4Exe
from Booster.P4Label import P4Label
from Booster.Remove import removeSingleFile
from ata import bamboo

logger = ata.log.AtaLog(__name__)
BOOSTER_DIR = os.path.dirname(os.path.realpath(__file__))


def ExecuteInputFile(configfile):
    logger.info('=========== Executing ============')
    logger.info(configfile)
    logger.info('=========== ========= ============')
    initBuildDir()
    upperEnvVariables()
    setP4Env()
    planSettings = initPlanSettings()
    fileBaseNme = os.path.basename(configfile)
    buildFile = 'build/' + fileBaseNme
    dependencySettings = {}
    dependencySettings = getDependencyFiles(configfile, planSettings, dependencySettings)
    compilersettings = initCompilerSettings(planSettings)
    setBuildFile(configfile, planSettings, dependencySettings, buildFile)
    setCompilerSettings(buildFile, planSettings, dependencySettings)
    logger.info('=========== plan filters ============')
    displayDict(planSettings)
    logger.info('=========== dependencies from product props file ============')
    displayDict(dependencySettings)
    logger.info('=========== compilers from bamboo capability ============')
    displayDict(compilersettings)
    logger.info('=========== booster variables ============')
    dumpVariables()
    dumpBoosterVariables()
    dumpBambooVariables()
    dumpPlanSettings(planSettings)
    return buildFile


def ExecuteTask(configfile):
    planSettings = initPlanSettings()
    fileBaseNme = os.path.basename(configfile)
    parent_dir = os.path.basename(os.path.abspath(os.path.join(configfile, os.pardir)))
    buildFile = 'build/' + parent_dir + '/' + fileBaseNme
    dependencySettings = {}
    dependencySettings = getDependencyFiles(configfile, planSettings, dependencySettings)
    setBuildFile(configfile, planSettings, dependencySettings)
    return buildFile


def ExecuteBambooBuild():
    getip()
    initBuildDir()
    upperEnvVariables()
    setP4Env()
    planSettings = initPlanSettings()
    configfileName = planSettings['product']
    try:
        if os.environ.get('BAMBOO_BOOSTER_CONFIG_REPO', '') != '':
            planSettings['booster_config_repo'] = os.environ['BAMBOO_BOOSTER_CONFIG_REPO']
            configbase = os.path.join(os.environ['P4ROOT'],os.environ['BAMBOO_BOOSTER_CONFIG_REPO'])
            configfile = os.path.join(configbase, configfileName) + '.' + planSettings['plantype']
            if not existsConfigFile(configfile):
                logger.info( configfile + ' does not exist. Use the default config file from booster repo')
                configfile = os.path.join('Config', 'Projects', planSettings['project'], configfileName) + '.' + planSettings['plantype']
        else:
            configbase = 'Config'
            configfile = os.path.join(configbase, 'Projects', planSettings['project'], configfileName) + '.' + planSettings['plantype']

        logger.info('=========== Executing ============')
        logger.info(configfile)
        logger.info('=========== ========= ============')
    except KeyError:
        print('Project config file for ' + configfileName + ' does not exist')
        print('config file is ' + os.path.join('Config', 'Projects', planSettings['project'], configfileName) + '.' + planSettings['plantype'])
        exit(0)
    if not existsConfigFile(configfile):
        print('Can not load ' + configfile)
        exit(-1)
    fileBaseNme = os.path.basename(configfile)
    parent_dir = os.path.basename(os.path.abspath(os.path.join(configfile, os.pardir)))
    buildFile = 'build/' + parent_dir + '/' + fileBaseNme
    dependencySettings = {}
    dependencySettings = getDependencyFiles(configfile, planSettings, dependencySettings)
    compilersettings = initCompilerSettings(planSettings)
    setBuildFile(configfile, planSettings, dependencySettings)
    setCompilerSettings(buildFile, planSettings, dependencySettings)
    logger.info('=========== plan filters ============')
    displayDict(planSettings)
    logger.info('=========== dependencies from product props file ============')
    displayDict(dependencySettings)
    logger.info('=========== compilers from bamboo capability ============')
    displayDict(compilersettings)
    logger.info('=========== booster variables ============')
    dumpVariables()
    dumpBoosterVariables()
    dumpBambooVariables()
    dumpPlanSettings(planSettings)
    #displayCodeCommits()
    return buildFile


def ExecuteManualBuild(configfile):
    loadBambooVariables()
    for key in os.environ.keys():
        if key.startswith('BAMBOO_'):
            logger.info(key + ':' + os.environ[key])
    loadBoosterVariables()
    for key in os.environ.keys():
        if key.startswith('BOOSTER_VAR'):
            logger.info(key + ':' + os.environ[key])
    planSettings = loadPlanSettings()
    displayDict(planSettings)
    return configfile


def dumpVariables():
    """
    Duump all variables and their override history
    :return:
    """
    d = VarMgr()
    logger.info('=========All Variables===========')
    d.dumpAll(withSource=False)


def dumpBoosterVariables():
    root = ET.Element('BoosterVariables')
    for key in os.environ.keys():
        if key.startswith('BOOSTER_VAR'):
            ET.SubElement(root, key).text = os.environ[key]
    tree = ET.ElementTree(root)
    tree.write("build/BoosterVariables.xml")


def dumpBambooVariables():
    root = ET.Element('BambooVariables')
    for key in os.environ.keys():
        if key.startswith('BAMBOO_'):
            ET.SubElement(root, key).text = os.environ[key]
    tree = ET.ElementTree(root)
    tree.write("build/BambooVariables.xml")


def dumpPlanSettings(planSettings):
    root = ET.Element('PlanSettings')
    for key in planSettings.keys():
        ET.SubElement(root, key).text = planSettings[key]
    tree = ET.ElementTree(root)
    tree.write("build/PlanSettings.xml")


def displayDict(dict):
    logger.info('==========================')
    for key in sorted(dict.keys()):
        logger.info(key + ':' + str(dict[key]))
    logger.info('==========================')


def existsConfigFile(config):
    if os.path.exists(config):
        return True
    else:
        return False


def initBuildDir():
    need_wait = False       # TODO - a better solution
    if os.path.isdir('build'):
        shutil.rmtree('build')
        need_wait = True
    if os.path.isdir('log'):
        shutil.rmtree('log')
        need_wait = True
    if need_wait:           # NTFS may wait for a while to remove directory before you can re-create it after deleting
        import time
        time.sleep(0.2)
    os.makedirs('build')
    os.makedirs('log')


def initPlanSettings():
    # get project plan job and branch names
    # init setting dictionary
    settings = {}
    if getOS() is not None:
        settings['os'] = getOS()

    if isBambooBuild(): settings = bamboo.initPlanSettings(settings)

    # load env variables to overrdie the settings
    loadEnvVariableSettings(settings)

    # load env variables to overrdie the settings
    removeUndefSettingKey(settings)

    # set env varibales for skipper to read
    setSkipperVariables(settings)

    return settings


def initCompilerSettings(planSettings):
    if isBambooBuild(): settings = bamboo.initCompilerSettings(planSettings)
    return settings


def setP4Env():
    setP4Port()
    setP4USER()
    setP4Client()
    setP4Root()


def setP4Port():
    if isBambooBuild():
        os.environ['P4PORT'] = os.environ['BAMBOO_P4PORT']


def setP4USER():
    if isBambooBuild():
        os.environ['P4USER'] = os.environ['BAMBOO_SEN_P4USERNAME']


def setP4Client():
    if isBambooBuild():
        agentName = os.environ['BAMBOO_CAPABILITY_ORG_HOSTNAME']
        if os.environ['BAMBOO_ATA_BAMBOO_SERVER'] == '2':
            clientName = 'bamboo_sen_' + agentName
        else:
            clientName = 'bamboo_' + agentName
        os.environ['P4CLIENT'] = clientName


def setP4Root():
    if isBambooBuild():
        if getOS() == 'Windows':
            os.environ['P4ROOT'] = 'C:/bamboo-agent-home/xml-data/build-dir'
        else:
            os.environ['P4ROOT'] = '/bamboo/bamboo-agent-home/xml-data/build-dir'


def getDependencyFiles(file, planSettings, dependencySettings):
    try:
        xml = XMLFile(file)
    except Exception as e:
        # print('Failed to parse ' + file)
        logger.info('Failed to parse ' + file)
        logger.error(e)
        exit(-1)
    root = xml.root()

    # filter on build settings
    for key in planSettings.keys():
        value = str(planSettings[key])
        root = includeAttrib(root, key, value)
        root = excludeAttrib(root, 'skip_' + key, value)

    upperCasePlanSettings = upperDictKeys(planSettings)
    for element in root.iter():
        if element.tag == 'Props':
            propsfile = element.text
            propsfile = substituteInString(propsfile, upperCasePlanSettings)
            propsfile = substituteInString(propsfile, dependencySettings)
            label = element.attrib.get('label', 'default')
            propsfile = syncConfigFile(propsfile, label)
            settings = parsePropsFile(propsfile)
            for key in settings:
                if key in dependencySettings:
                    pass
                else:
                    dependencySettings[key] = settings[key]
        if element.tag == 'Import':
            importfile = element.text
            importfile = substituteInString(importfile, upperCasePlanSettings)
            importfile = substituteInString(importfile, dependencySettings)
            optional = element.attrib.get('optional', 'false').lower() == 'true'
            ifname = getImportFile(importfile, optional)
            if ifname is not None:
                getDependencyFiles(ifname, planSettings, dependencySettings)
            else:
                logger.info('optional import file {name} not exist'.format(name=element.text))

    return dependencySettings


def syncConfigFile(file, labelname):
    propsfileview = '//' + file
    p4root = os.environ.get('BAMBOO_AGENTWORKINGDIRECTORY', os.environ.get('P4ROOT', 'undef'))
    propsfile = os.path.join(p4root, file)
    removeSingleFile(propsfile)
    if labelname == 'default':
        labelname = os.environ.get('BAMBOO_PRODUCT_LABEL')
        longlabel = os.environ.get(labelname)
    else:
        longlabel = os.environ.get(labelname)
    longlabel = longlabel.replace('__head__CL', 'head__CL')
    longlabel = longlabel.replace('__head__', 'head')
    logger.info('== Load file ' + propsfile + ' from ' + longlabel + ' ==')
    (label, changelists) = P4Sync.parseLabel(longlabel)
    p4 = P4Sync.getP4Exe()
    P4Sync.sync(p4, propsfileview, label)
    for cl in changelists:
        P4Sync.unshelvedepot(p4, cl, propsfileview)
    return propsfile


def getImportFile(file, optional):
    p4root = os.environ.get('BAMBOO_AGENTWORKINGDIRECTORY', os.environ.get('P4ROOT', 'undef'))
    if os.path.exists(os.path.join(BOOSTER_DIR, file)):
        importfile = os.path.join(BOOSTER_DIR, file)
    elif os.path.exists(os.path.join(p4root, file)):
        importfile = os.path.join(os.path.join(p4root, file))
    else:
        importfile = syncConfigFile(file, 'default')
    if not os.path.exists(importfile):
        if optional:
            return None
        else:
            raise RuntimeError(fname + ' not found')
    return importfile


def parsePropsFile(file):
    propfilesettings = {}
    paresedsettings = {}
    outputsettings = {}
    try:
        xml = XMLFile(file)
    except Exception as e:
        logger.info('Failed to parse ' + file)
        logger.error(e)
        return settings
    root = xml.root()
    for element in root.iter():
        tag = element.tag.split('}')[1]
        if tag.startswith('S_') and tag.endswith('_V'):
            key = tag
            value = element.text.replace('\\', '/')
            propfilesettings[key] = value
    for key in propfilesettings:
        paresedsettings[key[2:]] = substituteInString(propfilesettings[key], propfilesettings)
    for key in paresedsettings:
        if '/' in paresedsettings[key]:
            d_version=paresedsettings[key].split('/')[1]
            d_branch=paresedsettings[key]
            outputsettings[key] = d_version
            outputsettings[key.replace('_V', '_BRANCH')] = d_branch
        else:
            outputsettings[key] = paresedsettings[key]
            outputsettings[key.replace('_V', '_BRANCH')] = paresedsettings[key]

    return outputsettings


# functions that parse bamboo plan name to get build info
def isBambooBuild():
    if 'BAMBOO_PLANNAME' in os.environ.keys() and os.environ.get('IS_GITHUB_WORKFLOW', 'false') == 'false':
        return True
    else:
        return False


def isGitHubBuild():
    if os.environ.get('IS_GITHUB_WORKFLOW', 'false') == 'true':
        return True
    else:
        return False


# functions that get os and platform info:
# settingDict['os']
def getOS():
    current_os = os.name
    if current_os == 'nt':
        return 'Windows'
    else:
        return 'Posix'


def getip():
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        logger.info('==running on host ' +ip + '==')
    except Exception as e:
        logger.warning('==Failed to get agent ip address==')
        logger.warning(e)

def setSkipperVariables(settingsDict):
    if 'compiler' in settingsDict.keys(): os.environ['BAMBOO_COMPILER'] = settingsDict['compiler']


# functions that loads manual build setting files
def loadBambooVariables():
    file = "build/BambooVariables.xml"
    try:
        xml = XMLFile(file)
    except Exception as e:
        logger.info('Failed to parse ' + file)
        logger.error(e)
        exit(-1)
    root = xml.root()
    for element in list(root):
        variable = element.tag
        if element.text is None:
            value = ''
        else:
            value = element.text
        os.environ[variable] = value


def loadBoosterVariables():
    file = "build/BoosterVariables.xml"
    try:
        xml = XMLFile(file)
    except Exception as e:
        logger.info('Failed to parse ' + file)
        logger.error(e)
        exit(-1)
    root = xml.root()
    for element in list(root):
        variable = element.tag
        if element.text is None:
            value = ''
        else:
            value = element.text
        os.environ[variable] = value


def loadPlanSettings():
    settings = {}
    file = "build/PlanSettings.xml"
    try:
        xml = XMLFile(file)
    except Exception as e:
        logger.info('Failed to parse ' + file)
        logger.error(e)
        exit(-1)
    root = xml.root()
    for element in list(root):
        variable = element.tag
        if element.text is None:
            value = ''
        else:
            value = element.text
        settings[variable] = value
    return settings


# function that loads env variables to override the settings, and extra user filters prefixed by user_filter
# never override os and drivertype
def loadEnvVariableSettings(settingsDict):
    keyPrefix = 'bamboo_user_filter'
    n = len(keyPrefix)
    for envKey in os.environ.keys():
        for settingKey in settingsDict.keys():
            if envKey.lower() == settingKey and envKey.lower() != 'os' and envKey.lower() != 'drivertype':
                settingsDict[settingKey] = os.environ[envKey]
        if envKey.lower()[:n] == keyPrefix:
            settingsDict['user_filter' + envKey.lower()[n:]] = os.environ[envKey]


# Remove keys from dict whose value is 'undef'
def removeUndefSettingKey(settingsDict):
    for key in settingsDict.keys():
        if settingsDict[key] == 'undef':
            del settingsDict[key]


# Generating build process from the input file
def setBuildFile(file, settings, dependencies, output='default'):
    upperCasePlanSettings = upperDictKeys(settings)
    try:
        xml = XMLFile(file)
    except Exception as e:
        # print('Failed to parse ' + file)
        logger.info('Failed to parse ' + file)
        logger.error(e)
        exit(-1)

    root = xml.root()
    if output == 'default':
        fileBaseNme = os.path.basename(file)
        parent_dir = os.path.basename(os.path.abspath(os.path.join(file, os.pardir)))
        buildFile = 'build/' + parent_dir + '/' + fileBaseNme
    else:
        buildFile = output

    # import bamboo variables
    for element in root.iter():
        if (element.tag == 'BambooVariables'):
            importBambooVariables(element)

    # filter on build settings
    for key in settings.keys():
        value = str(settings[key])
        root = includeAttrib(root, key, value)
        root = excludeAttrib(root, 'skip_' + key, value)

    # define plan settings
    for key in settings.keys():
        upperKey = key.upper()
        try:
            root = setEmptyElementValue(root, upperKey, settings[key])
        except:
            KeyError

    # Check and remove empty element
    root = removeEmptyNode(root)


    # import dependencies
    root = importDict(root, dependencies)


    # substitute variables defined in current build file first
    root = substituteTree(root, root)

    # import config files
    remove_nodes = []
    for element in root.iter():
        if (element.tag == 'Import'):
            importfile = element.text
            importfile = substituteInString(importfile, upperCasePlanSettings)
            importfile = substituteInString(importfile, dependencies)
            optional = element.attrib.get('optional', 'false').lower() == 'true'
            ifname = getImportFile(importfile, optional)
            if ifname is not None:
                importFile(ifname, root, settings, dependencies)
                importFileBaseName = os.path.basename(importfile)
                parent_dir = os.path.basename(os.path.abspath(os.path.join(importfile, os.pardir)))
                element.text = 'build/' + parent_dir + '/' + importFileBaseName
            else:
                logger.info('optional import file {name} not exist'.format(name=element.text))
                remove_nodes.append(element)    # not reliable to remove at iterating
    for e in remove_nodes:
        p = e.parent
        if p is not None:
            p = p()
        if p is not None:
            p.remove(e)
    remove_nodes = []

    # import env variables
    root = importEnv(root)

    # import latest labels
    root = importLatestLabals(root)

    # parse label and import version number as env variables so that we can use them in the config file
    for element in root.iter():
        if (element.tag == 'VersionNumber'):
            importVersion(element, settings)

    # import version numbers
    root = importEnv(root)

    # set variables as env variable so that they are global
    for element in root.iter():
        if (element.tag == 'Variables' or element.tag == 'BambooVariables' or element.tag == 'SetEnvVariables'):
            setBoosterVariables(element, file)

    # generate the new build file and create the parent directory if it doesn't exist
    if not os.path.exists(os.path.dirname(buildFile)):
        try:
            os.makedirs(os.path.dirname(buildFile))
        except OSError as exc:
            if exc.errno != errno.EEXIST:
                raise
    with open(buildFile, 'w'):
        xml.tree().write(buildFile)


def setCompilerSettings(file, planSettings, dependencySettings):
    upperCasePlanSettings = upperDictKeys(planSettings)
    #logger.info('set compiler settings for ' + file)
    xml = XMLFile(file)
    root = xml.root()
    # set Compiler settings in import files
    for element in list(root):
        if (element.tag == 'Import'):
            importfile = element.text
            importfile = substituteInString(importfile, upperCasePlanSettings)
            importfile = substituteInString(importfile, dependencySettings)
            optional = element.attrib.get('optional', 'false').lower() == 'true'
            ifname = getImportFile(importfile, optional)
            if ifname is not None:
                setCompilerSettings(ifname, planSettings, dependencySettings)


    # set compiler settings
    for element in root.iter():
        if element.tag == 'VisualStudio':
            importVisualStudioSettings(element, planSettings)
        elif element.tag == 'Make':
            importMakeSettings(element, planSettings)
        elif element.tag == 'Ant':
            importAntSettings(element, planSettings)
        elif element.tag == 'Mvn':
            importMvnSettings(element, planSettings)
        elif element.tag == 'Gradle':
            importGradleSettings(element, planSettings)

    with open(file, 'w'):
        xml.tree().write(file)


# find and remove empty node in a tree
def removeEmptyNode(root):
    for element in root.iter():
        for subelement in list(element):
            if subelement.text == None:
                element.remove(subelement)
                os.environ[subelement.tag]=''

    return root


# set an element in a tree
def setEmptyElementValue(root, key, value):
    for element in root.iter():
        if element.tag == key and element.text == None: element.text = value
    return root


# filter on the tree
def includeAttrib(root, key, value):
    for element in root.iter():
        for subelement in list(element):
            attribValue = subelement.attrib.get(key, 'Default')
            attribValueList = attribValue.split(',')
            if (attribValue == 'Default'):
                continue
            elif (value in attribValueList):
                continue
            else:
                if Debugger().trace('xmlstrip'):
                    print('includeAttrib: strip tag for {key}={value}'.format(key=key, value=value))
                    dumpXMLNode(subelement, True, True, True)
                element.remove(subelement)
    return root


def excludeAttrib(root, key, value):
    for element in root.iter():
        for subelement in list(element):
            attribValue = subelement.attrib.get(key, 'Default')
            attribValueList = attribValue.split(',')
            if (attribValue == 'Default'):
                continue
            elif (value not in attribValueList):
                continue
            else:
                if Debugger().trace('xmlstrip'):
                    print('excludeAttrib: strip tag for {key}={value}'.format(key=key, value=value))
                    dumpXMLNode(subelement, True, True, True)
                element.remove(subelement)
    return root


# get value of all variables from input tree
# set value for all variables in base tree
def substituteTree(inputRoot, baseRoot):
    for element in inputRoot.iter():
        varName = element.tag
        varValue = element.text
        oldString = '$(' + varName + ')'
        newString = varValue
        substituteOne(oldString, newString, baseRoot)
    return baseRoot


# substitute one variable in a tree
def substituteOne(varName, varValue, root):
    for element in root.iter():
        if (varName in element.text):
            oldText = element.text
            newText = oldText.replace(varName, varValue)
            element.text = newText
        if (varName in str(element.attrib)):
            for key in element.attrib.keys():
                oldText = element.attrib[key]
                newText = oldText.replace(varName, varValue)
                element.attrib[key] = newText


# substitude variables in a string recursively
def substituteInString(inString, inVariables):
    flag = 0
    outString = inString
    for key in inVariables.keys():
        varName = '$(' + key + ')'
        if varName in inString:
            outString = inString.replace(varName, inVariables[key])
            flag =1
    if flag == 1:
        return substituteInString(outString, inVariables)
    else:
        return outString



# import external config files
def importFile(importFile, baseRoot, settings, dict):
    # Fix the imported file before importing it
    setBuildFile(importFile, settings, dict)
    # Import the file
    # baseRoot=substituteTree(importRoot, baseRoot)
    return baseRoot


# import env variables
def importEnv(root):
    for key in os.environ.keys():
        value = os.environ[key]
        if 'BOOSTER_VAR_' in key:
            oldString = '$(' + key.replace('BOOSTER_VAR_','') + ')'
        else:
            oldString = '$(' + key + ')'
        newString = value
        substituteOne(oldString, newString, root)
    return root


# import dictionary
def importDict(root, dict):
    for key in dict.keys():
        value = dict[key]
        oldString = '$(' + key + ')'
        newString = value
        substituteOne(oldString, newString, root)
    return root


# If a customized bamboo variable is set, override the default value
def importBambooVariables(node):
    for element in list(node):
        envVarName = 'BAMBOO_' + element.tag
        if (envVarName in os.environ):
            element.text = os.environ[envVarName]
        if element.text:
            element.text = element.text.replace('__head__CL', 'head__CL')
            element.text = element.text.replace('__head__', 'head')


def setBoosterVariables(node, file):
    vm = VarMgr()

    # the tag itself text support list of name=value
    d = Var.str2dict(node.text)
    for e in d:
        varName = 'BOOSTER_VAR_' + e
        vm.add(varName, d[e], file)
        os.environ[evarName] = d[e]

    # its children override defines
    for element in node:
        varName = 'BOOSTER_VAR_' + element.tag
        vm.add(varName, element.text, file)
        os.environ[varName] = element.text

    #vm.dumpAll()

# get the latest label name
def importLatestLabals(root):
    for element in root.iter():
        if ('LABEL' in element.tag) and (element.text == '__latest__'):
            label = getLatestLabel(element)
            element.text = label
            # print('Latest ' + element.tag + ':' + label)
            logger.info('Latest ' + element.tag + ':' + label)
    return root


# Find latest label
def getLatestLabel(node):
    label = node.attrib.get('prefix', 'undef') + '*'
    if platform.system() == 'Windows':
        label = '"' + label + '"'
    else:
        label = "'" + label + "'"
    p4Port = node.attrib.get('p4port')
    p4User = node.attrib.get('p4user')
    #p4 = getP4Exe(quoted=False)
    p4 = getP4Exe()
    cmd = [p4, '-s']
    if p4Port is not None:
        cmd.extend(['-p', p4Port])
    if p4User is not None:
        cmd.extend(['-u', p4User])
    cmd.extend(['labels', '-e', label])
    p4Path = node.attrib.get('path')
    if p4Path is not None:
        cmd.append(p4Path)
    cmd = ' '.join(cmd)
    result = Command.ExecuteAndGetResult(cmd) # return list of label infos

    latestLabel = None
    for labelInfo in result.split('info: Label '):
        # labelInfo is a string with format of
        #      label date 'label description'
        # by convention, a stable label contains sub-string "<STABLE>" in its description
        if '<STABLE>' in labelInfo:
            stableLabel = P4Label(labelInfo.split(' ')[0])
            if stableLabel > latestLabel:
                latestLabel = stableLabel
    if latestLabel is None:
        logger.error('No label marked STABLE for ' + label + ': Please update <STABLE> in the label description')
        exit(-1)
    return str(latestLabel)


# set version number
def importVersion(node, settings):
    label = node.attrib.get('label', 'undef')
    label = label.split('__CL')[0]
    branch = settings['branch']
    try:
        defaultmajorVersion = branch.split('.')[0]
        defaultminorVersion = branch.split('.')[1]
    except IndexError:
        defaultmajorVersion = '0'
        defaultminorVersion = '9'
    try:
        version = (label.split('_'))[-1]
        # print('ProductVersion:' + version)
        logger.info('ProductVersion:' + version)

        versionArray = version.split('.')
        majorVersion = versionArray[0]
        minorVersion = versionArray[1]
        revision = versionArray[2]
        buildNumber = versionArray[3]
    except IndexError:
        try:
            version = (label.split('_'))[-2]
            print('ProductVersion:' + version)
            versionArray = version.split('.')
            majorVersion = versionArray[0]
            minorVersion = versionArray[1]
            revision = versionArray[2]
            buildNumber = versionArray[3]
        except IndexError:
            print(label + ' is not a release label for ' + branch)
            version = 'head'
            majorVersion = defaultmajorVersion
            minorVersion = defaultminorVersion
            revision = '0'
            buildNumber = '0000'

    # set the default/label version as env variable
    os.environ['MAJOR_V_LABEL'] = majorVersion
    os.environ['MINOR_V_LABEL'] = minorVersion
    os.environ['REVISION_V_LABEL'] = revision
    os.environ['BUILD_V_LABEL'] = buildNumber
    logger.info('majorVersionLabel:' + majorVersion)
    logger.info('minorVersionLabel:' + minorVersion)
    logger.info('revisionLabel:' + revision)
    logger.info('buildNumberLabel:' + buildNumber)

    # set version from label/head
    os.environ['MAJOR_V'] = majorVersion
    os.environ['MINOR_V'] = minorVersion
    os.environ['REVISION_V'] = revision
    os.environ['BUILD_V'] = buildNumber
    logger.info('majorVersion:' + majorVersion)
    logger.info('minorVersion:' + minorVersion)
    logger.info('revision:' + revision)
    logger.info('buildNumber:' + buildNumber)

    # create padded versions from label/head
    os.environ['PADDED_MAJOR_V'] = majorVersion.zfill(2)
    os.environ['PADDED_MINOR_V'] = minorVersion.zfill(2)
    os.environ['PADDED_REVISION_V'] = revision.zfill(2)

    # support override default version and multiple version variables
    for key in os.environ.keys():
        if key.startswith('BAMBOO_') and key.endswith('_VERSION') and not 'CAPABILITY' in key and os.environ[key].strip()!='':
            try:
                version = os.environ[key]
                if key == 'BAMBOO_BRAND_VERSION':
                    settings['ProductVersion'] = version
                versionArray = version.split('.')
                majorVersion = versionArray[0]
                minorVersion = versionArray[1]
                revision = versionArray[2]
                buildNumber = versionArray[3]

                key=key.replace('BRAND_VERSION', 'VERSION')
                versionKey = '_'.join(key.split('_')[1:-1]) + '_{version_type}'
                majorVersionKey = versionKey.format(version_type='MAJOR_V').strip('_')
                minorVersionKey = versionKey.format(version_type='MINOR_V').strip('_')
                revisionKey = versionKey.format(version_type='REVISION_V').strip('_')
                buildNumberKey = versionKey.format(version_type='BUILD_V').strip('_')
                paddedMajorVersionKey = 'PADDED_' + majorVersionKey
                paddedMinorVersionKey = 'PADDED_' + majorVersionKey
                paddedRevisionKey = 'PADDED_' + majorVersionKey

                os.environ[majorVersionKey] = majorVersion
                os.environ[minorVersionKey] = minorVersion
                os.environ[revisionKey] = revision
                os.environ[buildNumberKey] = buildNumber

                os.environ[paddedMajorVersionKey] = majorVersion.zfill(2)
                os.environ[paddedMinorVersionKey] = minorVersion.zfill(2)
                os.environ[paddedRevisionKey] = revision.zfill(2)

                logger.info(majorVersionKey + ':' + majorVersion)
                logger.info(minorVersionKey + ':' + minorVersion)
                logger.info(revisionKey + ':' + revision)
                logger.info(buildNumberKey + ':' + buildNumber)

            except IndexError:
                logger.warning(key + ':' + version + ' is not a valid version')

def importVisualStudioSettings(node, settings):
    # set compiler
    try:
        vsSetting = settings['compiler'].upper()
        msbuildSetting = os.environ['BOOSTER_VAR_' + vsSetting]
        setUndefAttribute(node, 'msbuild', msbuildSetting)
    except:
        KeyError

    # set arch
    try:
        archSetting = os.environ['BOOSTER_VAR_BUILDARCH']
        setUndefAttribute(node, 'arch', archSetting)
    except:
        KeyError

    # set target
    try:
        if 'BOOSTER_VAR_BUILDTARGET' in os.environ.keys():
            targetSetting = os.environ['BOOSTER_VAR_BUILDTARGET']
        else:
            targetSetting = 'release'
        setUndefAttribute(node, 'target', targetSetting)
    except:
        KeyError

    # set compiler env
    try:
        envSetting = os.environ['BOOSTER_VAR_' + vsSetting + '_ENV']
        setUndefAttribute(node, 'env', envSetting)
    except:
        KeyError

    # set compiler opt
    try:
        optSetting = os.environ['BOOSTER_VAR_' + vsSetting + '_OPT']
        setUndefAttribute(node, 'opt', optSetting)
    except:
        KeyError


def importMakeSettings(node, settings):
    # set arch
    try:
        archSetting = os.environ['BOOSTER_VAR_BUILDARCH']
        setUndefAttribute(node, 'arch', archSetting)
    except:
        KeyError

    try:
        if 'BOOSTER_VAR_BUILDTARGET' in os.environ.keys():
            targetSetting = os.environ['BOOSTER_VAR_BUILDTARGET']
        else:
            targetSetting = 'release'
        setUndefAttribute(node, 'target', targetSetting)
    except:
        KeyError

    # set compiler env
    try:
        compilerSetting = settings['compiler'].upper()
        envSetting = os.environ['BOOSTER_VAR_' + compilerSetting + '_ENV']
        setUndefAttribute(node, 'env', envSetting)
    except:
        KeyError

    # set compiler opt
    try:
        optSetting = os.environ['BOOSTER_VAR_' + compilerSetting + '_OPT']
        setUndefAttribute(node, 'opt', optSetting)
    except:
        KeyError


def importAntSettings(node, settings):
    # set ant
    antHomeSetting = os.environ.get('BOOSTER_VAR_ANT_HOME', 'unset')
    if antHomeSetting == 'unset':
        logger.critical(java + '_' + javaBitness + ' not found in agent capability')
    setUndefAttribute(node, 'ANT_HOME', antHomeSetting)

    # set java home
    java = setJavaHome(node, settings)

    # set target
    targetSetting = os.environ.get('BOOSTER_VAR_' + java.upper() + '_Target', 'unset')
    setUndefAttribute(node, 'target', targetSetting)

    # set compiler env
    envSetting = os.environ.get('BOOSTER_VAR_ANT_ENV')
    if envSetting:
        setUndefAttribute(node, 'ANT_ENV', envSetting)

    # set compiler opt
    optSetting = os.environ.get('BOOSTER_VAR_ANT_OPT')
    if optSetting:
        setUndefAttribute(node, 'opt', optSetting)


def importMvnSettings(node, settings):
    """
    Set Java version and maven home path.
    :param node: element.
    :param settings: plan settings.
    :return: Sets the Java version and maven home in environment variable.
    """
    # set maven
    mvnHomeSetting = os.environ.get('BOOSTER_VAR_M2_HOME', 'unset')
    bambooVarName = 'BAMBOO_CAPABILITY_SYSTEM_BUILDER_MVN_MVN'
    mvnHomeSetting = bamboo.getBambooCapability(mvnHomeSetting, bambooVarName)
    setUndefAttribute(node, 'M2_HOME', mvnHomeSetting)

    # set java home
    setJavaHome(node, settings)

def importGradleSettings(node, settings):
    """
    Set Java.
    :param node: element.
    :param settings: plan settings.
    :return: Sets the Java version and maven home in environment variable.
    """
    setJavaHome(node, settings)


def setJavaHome(node,settings):
    """
    Set Java Home.
    :param node:
    :param settings:
    """
    # Read Java version from attribute first
    javaVersion = node.attrib.get('jdk', 'unset')
    java = 'JDK' + javaVersion
    # Read Java version from plan name
    if (javaVersion == 'unset'):
        java = settings.get('compiler', None)
        if java is None:
            raise KeyError('Java version cannot be determined')

    if settings.get('bitness', '64') == '32':
        javaBitness = '32'
    else:
        javaBitness = '64'
    javaHomeSetting = os.environ.get('BOOSTER_VAR_' + java.upper() + '_HOME' + javaBitness, 'unset')
    if javaHomeSetting == 'unset':
        logger.critical(java + '_' + javaBitness + ' not found in agent capability')

    setUndefAttribute(node, 'JAVA_HOME', javaHomeSetting)
    return java


def setUndefAttribute(node, key, value):
    attribSetting = node.attrib.get(key, 'unset')
    if (attribSetting == 'unset'):
        node.attrib[key] = value


# Fix env variable keys to be all upper cases
def upperEnvVariables():
    for key in os.environ.keys():
        os.environ[key.upper()] = os.environ[key]

# Fix dictionary keys to be all upper cases
def upperDictKeys(dict):
    upperCaseKeyDict = {}
    for key in dict.keys():
        upperCaseKeyDict[key.upper()] = dict[key]
    return upperCaseKeyDict


# helper function for Code commits display
def displayCodeCommits():
    # only head requires list of Change Lists, labels get it from P4
    if 'DRV_LABEL' in os.environ.keys() and 'head' in os.environ['DRV_LABEL']:
        if 'DRV_BRANCH' in os.environ.keys() and 'PROJECT_NAME' in os.environ.keys():
            repo = '//Drivers/' + os.environ['PROJECT_NAME'] + '/'+os.environ['DRV_BRANCH'] + '/...'
            p4 = getP4Exe()
            p4Command = p4 + ' -p ' + os.environ['P4PORT'] + ' -u ' + os.environ['P4USER'] + ' changes -l  -s submitted -m 10 '+ repo
            logger.info("============================================")
            logger.info("Display Last 10 Code Commits For Repository: "+repo)
            logger.info("============================================")
            result = Command.ExecuteAndGetResult(p4Command)
            logger.info(result)
