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
    if isBambooBuild():
        longPlanNameArray = getLongPlanNameArray()
        projectNameArray = getProjectNameArray(longPlanNameArray)
        planNameArray = getPlanNameArray(longPlanNameArray)
        jobNameArray = getJobNameArray()
        branchNameArray = getBranchNameArray(longPlanNameArray)
        settings['bamboo'] = getBambooServer()

        if getOS() is not None:
            settings['os'] = getOS()
            # print('os = ' + settings['os'])

        if getPlatform(planNameArray) is not None:
            settings['platform'] = getPlatform(planNameArray)
            # print('platform = ' + settings['platform'])

        if getProjectNameFromPlanName(longPlanNameArray, projectNameArray) is not None:
            settings['project'] = getProjectNameFromPlanName(longPlanNameArray, projectNameArray)
            # print('project = ' + settings['project'])

        if getProductNameFromPlanName(longPlanNameArray, jobNameArray, branchNameArray) is not None:
            settings['product'] = getProductNameFromPlanName(longPlanNameArray, jobNameArray, branchNameArray)
            # print('product = ' + settings['product'])

        if getProductNameLowerFromPlanName(longPlanNameArray, jobNameArray, branchNameArray) is not None:
            settings['product_lower'] = getProductNameLowerFromPlanName(longPlanNameArray, jobNameArray, branchNameArray)
            # print('product_lower = ' + settings['product_lower'])

        if getBranchFromPlanName(longPlanNameArray, projectNameArray, branchNameArray) is not None:
            settings['branch'] = getBranchFromPlanName(longPlanNameArray, projectNameArray, branchNameArray)
            # print('branch = ' + settings['branch'])

        if getPlanTypeFromPlanName(longPlanNameArray, projectNameArray) is not None:
            settings['plantype'] = getPlanTypeFromPlanName(longPlanNameArray, projectNameArray)
            # print('plantype = ' + settings['plantype'])

        if getBuildDistributionFromPlanName(longPlanNameArray, planNameArray) is not None:
            settings['distribution'] = getBuildDistributionFromPlanName(longPlanNameArray, planNameArray)
            # print('distribution = ' + settings['distribution'])

        if getCompilerFromPlanName(longPlanNameArray, planNameArray, settings['plantype']) is not None:
            settings['compiler'] = getCompilerFromPlanName(longPlanNameArray, planNameArray, settings['plantype'])
            # print('compiler = ' + settings['compiler'])

        if getPlanFromPlanName(longPlanNameArray, planNameArray) is not None:
            settings['plan'] = getPlanFromPlanName(longPlanNameArray, planNameArray)
            # print('plan = ' + settings['plan'])

        if getJobName(longPlanNameArray, jobNameArray) is not None:
            settings['job'] = getJobName(longPlanNameArray, jobNameArray)

        if getBuildTagretFromPlanName(longPlanNameArray, jobNameArray) is not None:
            settings['buildtarget'] = getBuildTagretFromPlanName(longPlanNameArray, jobNameArray)
            # print('buildtarget = ' + settings['buildtarget'])

        if getBitnessFromPlanName(longPlanNameArray, planNameArray, jobNameArray, settings['compiler']) is not None:
            settings['bitness'] = getBitnessFromPlanName(longPlanNameArray, planNameArray, jobNameArray, settings['compiler'])
            #print('bitness = ' + settings['bitness'])

        if getDriverTypeFromPlanName(projectNameArray, settings['compiler'], settings['plantype']) is not None:
            settings['drivertype'] = getDriverTypeFromPlanName(projectNameArray, settings['compiler'], settings['plantype'])
            # print('drivertype = ' + settings['drivertype'])

        if getDMNameFromPlanName(longPlanNameArray, planNameArray, jobNameArray, settings['plantype'], settings['drivertype']) is not None:
            settings['dm_name'] = getDMNameFromPlanName(longPlanNameArray, planNameArray, jobNameArray, settings['plantype'], settings['drivertype'])
            #print('dm_name = ' + settings['dm_name'])

        if getDMVersionFromPlanName(longPlanNameArray, jobNameArray) is not None:
            settings['dm_version'] = getDMVersionFromPlanName(longPlanNameArray, jobNameArray)
            # print('dm_version = ' + settings['dm_version'])

        if getDMFromPlanName(longPlanNameArray, planNameArray, jobNameArray, settings['plantype'], settings['drivertype']) is not None:
            settings['dm'] = getDMFromPlanName(longPlanNameArray, planNameArray, jobNameArray, settings['plantype'], settings['drivertype'])
            #print('dm = ' + settings['dm'])

        if getJreFromPlanName(longPlanNameArray, planNameArray, settings['plantype'], settings['drivertype']) is not None:
            settings['jre'] = getJreFromPlanName(longPlanNameArray, planNameArray, settings['plantype'], settings['drivertype'])
            #print('jre = ' + settings['jre'])

        if getTestPlatformFromPlanName(longPlanNameArray, planNameArray, settings['plantype']) is not None:
            settings['test_platform'] = getTestPlatformFromPlanName(longPlanNameArray, planNameArray, settings['plantype'])
            #print('test_platform = ' + settings['test_platform'])

        if getPackagePlatformFromPlanName(longPlanNameArray, planNameArray, settings['plantype']) is not None:
            settings['package_platform'] = getPackagePlatformFromPlanName(longPlanNameArray, planNameArray, settings['plantype'])
            #print('package_platform = ' + settings['package_platform'])

        if getOSArchFromPlanName(longPlanNameArray, planNameArray, settings['plantype']) is not None:
            settings['os_arch'] = getOSArchFromPlanName(longPlanNameArray, planNameArray, settings['plantype'])
            # print('os_arch = ' + settings['os_arch'])

        if getTestTypeFromPlanName(longPlanNameArray, projectNameArray, settings['plantype']) is not None:
            settings['testtype'] = getTestTypeFromPlanName(longPlanNameArray, projectNameArray, settings['plantype'])
            # print('testtype = ' + settings['testtype'])

        if getPackageTypeFromPlanName(projectNameArray) is not None:
            settings['packagetype'] = getPackageTypeFromPlanName(projectNameArray)
            if settings['plantype'] != 'packagetest':
                settings['bitness'] = getBitnessForPackagePlan(settings['packagetype'], settings['platform'], settings['bitness'])
            # print('packagetype = ' + settings['packagetype'])

        if getPackageFormatFromPlanName(projectNameArray, planNameArray) is not None:
            settings['packageformat'] = getPackageFormatFromPlanName(projectNameArray, planNameArray)
            # print('packageformat = ' + settings['packageformat'])

        if settings['plantype'] == 'packagetest':
            settings['distribution'] = getDistributionForPackageTest()
            settings['package_platform'] = getPackagePlatformForPackageTest(settings['distribution'])
            settings['packageformat'] = getPackageFormatForPackageTest(settings['packagetype'], settings['platform'],settings['package_platform'])

        # override setting with bamboo variable
        if getCompilerFromBambooVariable() is not None and getCompilerFromBambooVariable() !='': settings['compiler'] = getCompilerFromBambooVariable()
        if getDistributionFromBambooVariable() is not None and getDistributionFromBambooVariable() !='': settings['distribution'] = getDistributionFromBambooVariable()
        if getBranchFromBambooVariable() is not None and getBranchFromBambooVariable() != '': settings['branch'] = getBranchFromBambooVariable()
        if getTestTypeFromBambooVariable() is not None and getTestTypeFromBambooVariable() !='': settings['testtype'] = getTestTypeFromBambooVariable()
        if getPackageTypeFromBambooVariable() is not None and getPackageTypeFromBambooVariable() != '': settings['packaggetype'] = getPackageTypeFromBambooVariable()
        if getDSVersionFromBambooVariable() is not None and getDSVersionFromBambooVariable() !='': settings['ds_version'] = getDSVersionFromBambooVariable()
        if getTestsuiteListFromBambooVariable() is not None and getTestsuiteListFromBambooVariable() != '': settings['testsuitelist'] = getTestsuiteListFromBambooVariable()
        if getAflFlagFromBambooVariables() is not None and getAflFlagFromBambooVariables() !='': settings['afl'] = getAflFlagFromBambooVariables()
        if getDynamiclinkingFlagFromBambooVariables() is not None and getDynamiclinkingFlagFromBambooVariables() != '': settings['dynamic_linking'] = getDynamiclinkingFlagFromBambooVariables()
        if getSignedFlagFromBambooVariables() is not None and getSignedFlagFromBambooVariables() != '': settings['signed'] = getSignedFlagFromBambooVariables()
        if getMemoryTestFlagFromBambooVariables() is not None and getMemoryTestFlagFromBambooVariables() !='': settings['memory_test'] = getMemoryTestFlagFromBambooVariables()
        if getJunitTestFlagFromBambooVariables() is not None and getJunitTestFlagFromBambooVariables() !='': settings['junit_test'] = getJunitTestFlagFromBambooVariables()
        if getAppVerifierFlagFromBambooVariables() is not None and getAppVerifierFlagFromBambooVariables() != '': settings['appverifier'] = getAppVerifierFlagFromBambooVariables()
        if getVeracodeFlagFromBambooVariables() is not None and getVeracodeFlagFromBambooVariables() != '':settings['veracode'] = getVeracodeFlagFromBambooVariables()
        if getRemoteTestFlagFromBambooVariables() is not None and getRemoteTestFlagFromBambooVariables() != '': settings['remote_test'] = getRemoteTestFlagFromBambooVariables()
        if getCodeAnalysisFlagFromBambooVariables() is not None and getCodeAnalysisFlagFromBambooVariables() != '':settings['code_analysis'] = getCodeAnalysisFlagFromBambooVariables()
        if getDMVersionFromBambooVariable() is not None and getDMVersionFromBambooVariable() != '': settings['dm'] = settings['dm_name'] + '-' + getDMVersionFromBambooVariable()
        if getDMFromBambooVariable() is not None and getDMFromBambooVariable() !='': settings['dm'] = getDMFromBambooVariable()
        if getDriverLogLevelFromBambooVariable() is not None and getDriverLogLevelFromBambooVariable() != '': settings['log_level'] = getDriverLogLevelFromBambooVariable()
        if getDMTraceFromBambooVariable() is not None and getDMTraceFromBambooVariable() != '': settings['dm_trace'] = getDMTraceFromBambooVariable()
        if getBuildTargetFromBambooVariable() is not None and getBuildTargetFromBambooVariable() !='': settings['buildtarget'] = getBuildTargetFromBambooVariable()
        if getCustomerFromBambooVariable() is not None and getCustomerFromBambooVariable() !='': settings['customer'] = getCustomerFromBambooVariable()
        if getRetailFlagFromBambooVariable() is not None and getRetailFlagFromBambooVariable() !='': settings['retail'] = getRetailFlagFromBambooVariable()
        if getCodeSigningPlatformFromBambooVariable() is not None and getCodeSigningPlatformFromBambooVariable() !='':
            settings['codesigningplatform'] = getCodeSigningPlatformFromBambooVariable()
            settings['codesigning'] = '1'
            if settings['codesigningplatform'] == 'osx':
                settings['codesigningplatform'] = 'OSX'
        else:
            settings['codesigning'] = '0'
        if getDockerServerformFromBambooVariable() is not None and getDockerServerformFromBambooVariable() !='':
            settings['docker_hostname'] = getDockerServerformFromBambooVariable()
            settings['use_dockerhost'] = '1'
        else:
            settings['use_dockerhost'] = '0'

        if getImageVersionFromBambooVariable():
            settings['image_version'] = getImageVersionFromBambooVariable()
        else:
            settings['image_version'] = 'unset'

        if getDSLocatorFromBambooVariable():
            datasourceLocator = getDSLocatorFromBambooVariable()
            settings['ds_locator'] = datasourceLocator
            ds_values = datasourceLocator.split(',')
            for value in ds_values:
                p = value.split("=",1)
                if(len(p))==2:
                    varName = 'locator_'+p[0].strip()
                    settings[varName.lower()] = p[1].strip()
                    os.environ[varName.upper()] = p[1].strip()

        # Parse DataSourceVersion for SEN C/S test plans
        if 'SEN' in settings['project'] and settings['product']=='Client' and settings['plantype'] =='test':
            settings['clientserver'] = '1'
            settings['server_product'] = getServerFromBambooVariables()
            settings['server_branch'] = getServerBranchFromBambooVariables(settings['branch'])
            settings['server_build_source'] = getServerBuildSource()
            (settings['server_os'], settings['server_platform']) = getSenServerPlatform(settings['server_build_source'])
            (settings['server_distribution'],settings['server_compiler'], settings['server_target'],settings['server_bitness'])= getSenServerSource(settings['server_build_source'], settings['distribution'], settings['compiler'], settings['buildtarget'],settings['bitness'])

        else:
            settings['clientserver'] = '0'
            #settings['clientserver'] = ''
            #settings['server_os'] = ''
            #settings['server_platform'] = ''
            #settings['server_distribution'] = ''
            #settings['server_compiler'] = ''
            #settings['server_bitness'] = ''
            pass
        setSkipperFlag(longPlanNameArray)


    # load env variables to overrdie the settings
    loadEnvVariableSettings(settings)

    # load env variables to overrdie the settings
    removeUndefSettingKey(settings)

    # set env varibales for skipper to read
    setSkipperVariables(settings)

    return settings


def initCompilerSettings(planSettings):
    settings = {}
    #load jdk
    for envkey in os.environ.keys():
        if envkey.startswith ('BAMBOO_CAPABILITY_SYSTEM_JDK') and envkey.endswith('X86'):
            key = envkey.replace('BAMBOO_CAPABILITY_SYSTEM_JDK_','').replace('X86','')
            settings[key+ '_HOME32'] = os.environ[envkey]
        if envkey.startswith ('BAMBOO_CAPABILITY_SYSTEM_JDK') and envkey.endswith('X64'):
            key = envkey.replace('BAMBOO_CAPABILITY_SYSTEM_JDK_','').replace('X64','')
            settings[key + '_HOME64'] = settings[key + '_HOME'] = os.environ[envkey]
        if planSettings['platform'] == 'OSX' and envkey.startswith ('BAMBOO_CAPABILITY_SYSTEM_JDK') and not envkey.startswith ('BAMBOO_CAPABILITY_SYSTEM_JDK_JDK_') and not envkey.endswith('JDK'):
            key = envkey.replace('BAMBOO_CAPABILITY_SYSTEM_JDK_', '')
            settings[key + '_HOME32'] = settings[key + '_HOME64'] = settings[key + '_HOME'] = os.environ[envkey]

    #load ant
    if 'BAMBOO_CAPABILITY_SYSTEM_BUILDER_ANT_ANT' in os.environ.keys():
        settings['ANT_HOME'] = os.environ['BAMBOO_CAPABILITY_SYSTEM_BUILDER_ANT_ANT']

    for key in settings.keys():
        os.environ['BOOSTER_VAR_' + key] = settings[key]
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
    if 'BAMBOO_PLANNAME' in os.environ.keys():
        return True
    else:
        return False


def getBambooServer():
    return os.environ.get('BAMBOO_ATA_BAMBOO_SERVER', 'undef')


def getLongPlanNameArray():
    longPlanName = os.environ['BAMBOO_PLANNAME']
    longPlanNameArray = longPlanName.split(' - ')
    return longPlanNameArray


def getJobNameArray():
    jobName = os.environ['BAMBOO_SHORTJOBNAME']
    jobNameArray = jobName.split(' ')
    return jobNameArray


def isNewPlan(longPlanNameArray):
    if len(longPlanNameArray) == 2:
        return False
    if len(longPlanNameArray) == 3:
        return True


def getProjectNameArray(longPlanNameArray):
    projectName = longPlanNameArray[0]
    projectNameArray = projectName.split(' ')
    return projectNameArray


def getPlanNameArray(longPlanNameArray):
    planName = longPlanNameArray[1]
    planNameArray = planName.split(' ')
    return planNameArray


def getBranchNameArray(longPlanNameArray):
    if isNewPlan(longPlanNameArray):
        branchName = longPlanNameArray[2]
        branchNameArray = branchName.split(' ')
        return branchNameArray
    else:
        return 'undef'


def getJobName(longPlanNameArray, jobNameArray):
    if isNewPlan(longPlanNameArray):
        return jobNameArray[0]
    else:
        return os.environ['BAMBOO_SHORTJOBNAME']


# functions that get os and platform info:
# settingDict['os']
def getOS():
    current_os = os.name
    if current_os == 'nt':
        return 'Windows'
    else:
        return 'Posix'


# settingDict['platform']
def getPlatform(planNameArray):
    current_platform = platform.system()
    current_cpu = platform.processor()
    if "debian9s390x" in planNameArray:
        return "ZLinux"
    if "debian10aarch64" in planNameArray:
        return "Linux_aarch64"
    if "debian10armhf" in planNameArray:
        return "Linux_armhf"
    elif current_platform == 'Darwin':
        return 'OSX'
    elif current_platform == 'SunOS':
        if current_cpu == 'sparc':
            return 'Solaris_Sparc'
        else:
            return 'Solaris_x86'
    elif current_platform == 'Linux' and current_cpu == 'ia64':
        return 'Linux_ia64'
    elif current_platform == 'Linux' and current_cpu == 'ppc64le':
        return 'Linux_ppc64'
    elif current_platform == 'Linux' and current_cpu == 'armhf':
        return 'Linux_armhf'
    elif current_platform == 'Linux' and current_cpu == 'aarch64':
        return 'Linux_aarch64'
    else:
        return current_platform


def getip():
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        logger.info('==running on host ' +ip + '==')
    except Exception as e:
        logger.warning('==Failed to get agent ip address==')
        logger.warning(e)


# functions that get build info from plan name
# settingsDict['project']
def getProjectNameFromPlanName(longPlanNameArray, projectNameArray):
    if isNewPlan(longPlanNameArray):
        if len(projectNameArray) == 2:
            return projectNameArray[1]
        else:
            return projectNameArray[2] + projectNameArray[1]
    else:
        return projectNameArray[0]


# settingsDict['product']
def getProductNameFromPlanName(longPlanNameArray, jobNameArray, branchNameArray):
    if isNewPlan(longPlanNameArray):
        return branchNameArray[0]
    else:
        return jobNameArray[0]

# settingsDict['product_lower']
def getProductNameLowerFromPlanName(longPlanNameArray, jobNameArray, branchNameArray):
    if isNewPlan(longPlanNameArray):
        return branchNameArray[0].lower()
    else:
        return jobNameArray[0].lower()


# settingsDict['branch']
def getBranchFromPlanName(longPlanNameArray, projectNameArray, branchNameArray):
    if isNewPlan(longPlanNameArray):
        return branchNameArray[1]
    else:
        return projectNameArray[1]


# settingDict['plantype']
def getPlanTypeFromPlanName(longPlanNameArray, projectNameArray):
    if isNewPlan(longPlanNameArray):
        if projectNameArray[0] == 'Compile': return 'build'
        if projectNameArray[0] == 'TestFunctional': return 'test'
        if projectNameArray[0] == 'TestThirdParty': return 'test'
        if projectNameArray[0] == 'TestSmoke': return 'test'
        if projectNameArray[0] == 'PerformanceTest': return 'test'
        if projectNameArray[0] == 'InstallerTest': return 'packagetest'
        if projectNameArray[0] == 'OEMTest': return 'packagetest'
        if projectNameArray[0] == 'PackageOEM': return 'package'
        if projectNameArray[0] == 'PackageInstaller': return 'package'
        if projectNameArray[0] == 'RetailPackage': return 'package'
        if projectNameArray[0] == 'Installer': return 'package'
        if projectNameArray[0] == 'CodeSigning': return 'package'
        if projectNameArray[0] == 'SignedInstaller': return 'signedpackage'
        if projectNameArray[0] == 'SignedOEM': return 'signedpackage'
        if projectNameArray[0] == 'Deploy': return 'deploy'
    else:
        if 'Build' in longPlanNameArray[0]: return 'build'
        if 'Test' in longPlanNameArray[0]: return 'test'


# settingsDict['distribution']
def getBuildDistributionFromPlanName(longPlanNameArray, planNameArray):
    if isNewPlan(longPlanNameArray):
        return planNameArray[0]
    else:
        return planNameArray[1]


# settingsDict['compiler']
def getCompilerFromPlanName(longPlanNameArray, planNameArray, planType):
    if isNewPlan(longPlanNameArray):
        if planType not in ['test', 'packagetest']:
            return planNameArray[1]
        else:
            return 'undef'
    else:
        return planNameArray[2]


# settingsDict['plan']
def getPlanFromPlanName(longPlanNameArray, planNameArray):
    if isNewPlan(longPlanNameArray):
        return 'undef'
    else:
        return planNameArray[0]


# settingDict['buildtarget']
def getBuildTagretFromPlanName(longPlanNameArray, jobNameArray):
    if isNewPlan(longPlanNameArray):
        return 'release'
    elif len(jobNameArray) >= 2:
        return jobNameArray[1]
    else:
        return 'undef'


# settingDict['bitness']
def getBitnessFromPlanName(longPlanNameArray, planNameArray, jobNameArray, compiler):
    # include a bitness override
    bitness = os.environ.get('BAMBOO_BITNESS', None)
    if bitness is None:
        if 'jdk' in compiler:
            return '3264'
        elif 'jdbc' in longPlanNameArray[0].lower() or 'j2o' in longPlanNameArray[0].lower() or 'jre' in planNameArray[2].lower():
            return '64'
        else:
            if isNewPlan(longPlanNameArray):
                return planNameArray[2]
            elif len(jobNameArray) >= 3:
                return jobNameArray[2]
            else:
                return 'undef'
    else:
        return bitness


# settingDict['drivertype']
def getDriverTypeFromPlanName(projectNameArray, compiler, planType):
    if projectNameArray[1] == 'ODBC':
        return 'odbc'
    elif projectNameArray[1] == 'Insight':
        return 'insight'
    elif projectNameArray[1] == 'JDBC':
        return 'jdbc'
    elif (projectNameArray[1] == 'J2O' or projectNameArray[2] == 'J2O') and planType in ['test', 'packagetest']:
        return 'jdbc'
    elif compiler != 'undef':
        if 'jdk' in compiler:
            return 'jdbc'
        else:
            return 'odbc'
    else:
        return 'undef'


# settingDict['dm_name']
def getDMNameFromPlanName(longPlanNameArray, planNameArray, jobNameArray, planType, drivertype):
    if drivertype == 'jdbc':
        return 'undef'
    else:
        if isNewPlan(longPlanNameArray):
            if planType in ['test', 'packagetest'] and os.name != 'nt':
                return planNameArray[3]
            else:
                return 'undef'
        elif len(jobNameArray) >= 4:
            return jobNameArray[3]
        else:
            return 'undef'


# settingDict['dm_version']
def getDMVersionFromPlanName(longPlanNameArray, jobNameArray):
    if isNewPlan(longPlanNameArray):
        return 'undef'
    elif len(jobNameArray) >= 5:
        return jobNameArray[4]
    else:
        return 'undef'


# settingDict['dm']
def getDMFromPlanName(longPlanNameArray, planNameArray, jobNameArray, planType, drivertype):
    dm_name = getDMNameFromPlanName(longPlanNameArray, planNameArray, jobNameArray, planType, drivertype)
    dm_version = getDMVersionFromPlanName(longPlanNameArray, jobNameArray)
    if dm_version != 'undef':
        return dm_name + '-' + dm_version
    else:
        return dm_name


# settingDict['jre']
def getJreFromPlanName(longPlanNameArray, planNameArray, planType, drivertype):
    if drivertype == 'odbc':
        return 'undef'
    else:
        if isNewPlan(longPlanNameArray):
            if planType in ['test', 'packagetest'] and 'jre' in planNameArray[2]:
               return  planNameArray[2]
            else:
                if drivertype == 'insight':
                    return 'none'
                else:
                    return 'undef'
        else:
            return 'undef'


# settingDict['test_platform']
def getTestPlatformFromPlanName(longPlanNameArray, planNameArray, planType):
    if planType in ['test', 'packagetest']:
        if isNewPlan(longPlanNameArray):
            return planNameArray[0]
        else:
            return planNameArray[1]
    else:
        return 'undef'

# settingDict['package_platform']
def getPackagePlatformFromPlanName(longPlanNameArray, planNameArray, planType):
    if planType == 'package':
        if isNewPlan(longPlanNameArray):
            return planNameArray[0]
        else:
            return planNameArray[1]
    else:
        return 'undef'

# settingDict['os_arch']
def getOSArchFromPlanName(longPlanNameArray, planNameArray, planType):
    if planType in ['test', 'packagetest']:
        if isNewPlan(longPlanNameArray):
            return planNameArray[1]
        else:
            return 'undef'
    else:
        return 'undef'


# settingDict['testtype']
def getTestTypeFromPlanName(longPlanNameArray, projectNameArray, planType):
    if isNewPlan(longPlanNameArray):
        if projectNameArray[0] == 'TestFunctional':
            return 'functionaltest'
        # add other test types here
        elif projectNameArray[0] == 'TestThirdParty':
            return 'thirdpartytest'
        elif projectNameArray[0] == 'TestSmoke':
            return 'functionaltest'
        elif projectNameArray[0] == 'PerformanceTest':
            return 'performancetest'
        elif projectNameArray[0] == 'InstallerTest':
            return 'installertest'
        elif projectNameArray[0] == 'OEMTest':
            return 'oemtest'
        else:
            return 'undef'
    else:
        if planType == 'test':
            return 'functionaltest'
        elif planType == 'packagetest':
            return 'packagetest'


# settingDict['packagetype']
def getPackageTypeFromPlanName(projectNameArray):
    #if 'Test' in projectNameArray[0]: return 'undef'
    if 'OEM' in projectNameArray[0]: return 'OEM'
    if 'Installer' in projectNameArray[0]:return 'installer'
    if 'RetailPackage' in projectNameArray[0]: return 'retailzip'
    return 'undef'

#
def getBitnessForPackagePlan(packagetype, platform, bitness):
    if packagetype == 'OEM':
        if platform == 'OSX': return 'universal'
        else:return '64'
    return bitness


# settingDict['packageformat']
def getPackageFormatFromPlanName(projectNameArray, planNameArray):
    #if 'Test' in projectNameArray[0]: return 'undef'
    if 'OEM' in projectNameArray[0] or 'Installer' in projectNameArray[0] or 'PackageRetail' in projectNameArray[0]: return planNameArray[-1]
    #if 'Installer' in projectNameArray[0]: return planNameArray[3]
    return 'undef'


# couple helper functions for package test plans
def getDistributionForPackageTest():
    return getDistributionFromBambooVariable()


def getPackagePlatformForPackageTest(distribution):
    return os.environ.get('BAMBOO_PACKAGE_PLATFORM', distribution)


def getPackageFormatForPackageTest(packagetype,platform,packageplatform):
    if packagetype == 'OEM':
        if platform == 'Windows' : return 'zip'
        else: return 'tar'
    if packagetype == 'installer':
        if platform == 'Windows' : return 'msi'
        if platform == 'Linux':
            if 'debian' in packageplatform: return 'deb'
            else: return 'rpm'
        if platform == 'OSX': return 'dmg'
        if platform == 'AIX': return 'rpm'


# functions that get build info from bamboo variables
# settingDict[compiler]
def getCompilerFromBambooVariable():
    if 'BAMBOO_COMPILER' in os.environ.keys(): return os.environ['BAMBOO_COMPILER']


# settingDict[distribution]
# in test plans, distribution is the build distribution
def getDistributionFromBambooVariable():
    if 'BAMBOO_BUILD_SOURCE' in os.environ.keys(): return os.environ['BAMBOO_BUILD_SOURCE']


# settingDict[branch]
def getBranchFromBambooVariable():
    if 'BAMBOO_BRANCH' in os.environ.keys(): return os.environ['BAMBOO_BRANCH']


# settingDict[testtype]
def getTestTypeFromBambooVariable():
    if 'BAMBOO_TEST_TYPE' in os.environ.keys(): return os.environ['BAMBOO_TEST_TYPE']


# settingDict[Packagetype]
def getPackageTypeFromBambooVariable():
    if 'BAMBOO_PACKAGE_TYPE' in os.environ.keys(): return os.environ['BAMBOO_PACKAGE_TYPE']


# settingDict[ds_locator]
def getDSLocatorFromBambooVariable():
    if 'BAMBOO_DS_LOCATOR' in os.environ.keys(): return os.environ['BAMBOO_DS_LOCATOR']


# settingDict[ds_version]
def getDSVersionFromBambooVariable():
    if 'BAMBOO_DATASOURCE_VER' in os.environ.keys(): return os.environ['BAMBOO_DATASOURCE_VER']


# settingDict[image_version]
def getImageVersionFromBambooVariable():
    if 'BAMBOO_DOCKER_IMAGE_VER' in os.environ.keys():
        return os.environ['BAMBOO_DOCKER_IMAGE_VER']


# settingDict[testsuitelist]
def getTestsuiteListFromBambooVariable():
    return os.environ.get('BAMBOO_TESTSUITE_LIST', None)


# settingDict[afl]
def getAflFlagFromBambooVariables():
    return os.environ.get('BAMBOO_AFL', '0')

def getDynamiclinkingFlagFromBambooVariables():
    return os.environ.get('BAMBOO_DYNAMIC_LINKING', '0')

def getMemoryTestFlagFromBambooVariables():
    return os.environ.get('BAMBOO_MEMORY_TEST', '0')

def getJunitTestFlagFromBambooVariables():
    return os.environ.get('BAMBOO_JUNIT', '0')

def getAppVerifierFlagFromBambooVariables():
    return os.environ.get('BAMBOO_APPVERIFIER', '0')

def getVeracodeFlagFromBambooVariables():
    return os.environ.get('BAMBOO_VERACODE', '0')

def getCodeAnalysisFlagFromBambooVariables():
    return os.environ.get('BAMBOO_CODE_ANALYSIS', '0')

def getRemoteTestFlagFromBambooVariables():
    return os.environ.get('BAMBOO_REMOTE_TEST', '0')

def getSignedFlagFromBambooVariables():
    return os.environ.get('BAMBOO_SIGNED', '0')


# settingDict[dm_version]
def getDMVersionFromBambooVariable():
    if 'BAMBOO_DM_VERSION' in os.environ.keys(): return os.environ['BAMBOO_DM_VERSION']


# settingDict[dm]
def getDMFromBambooVariable():
    if 'BAMBOO_DM' in os.environ.keys(): return os.environ['BAMBOO_DM']


# settingDict[loglevel]
def getDriverLogLevelFromBambooVariable():
    return os.environ.get('BAMBOO_LOG_LEVEL', '0')


def getDMTraceFromBambooVariable():
    return os.environ.get('BAMBOO_DM_TRACE', '0')


# settingDict[buildtarget]
def getBuildTargetFromBambooVariable():
    if 'BAMBOO_TARGET' in os.environ.keys(): return os.environ['BAMBOO_TARGET']


# settingDict[customer]
def getCustomerFromBambooVariable():
    if 'BAMBOO_DRV_BRAND' in os.environ.keys():
        return os.environ['BAMBOO_DRV_BRAND']
    else:
        return 'Simba'


# settingDict[retail]
def getRetailFlagFromBambooVariable():
    if 'BAMBOO_RETAIL' in os.environ.keys():
        return os.environ['BAMBOO_RETAIL']
    else:
        return '0'


# settingDict[codesigningplatform]
def getCodeSigningPlatformFromBambooVariable():
    return os.environ.get('BAMBOO_CODESIGNING_PLATFORM', None)


def getDockerServerformFromBambooVariable():
    return os.environ.get('BAMBOO_DOCKER_SERVER', os.environ.get('BAMBOO_CAPABILITY_ORG_BARCAHOST', None))


def getServerBranchFromBambooVariables(clientBranch):
    if os.environ.get('BAMBOO_SERVER_BRANCH','') != '':
        return os.environ.get('BAMBOO_SERVER_BRANCH')
    else:
        return clientBranch


def getServerFromBambooVariables():
    return os.environ.get('BAMBOO_SERVER_PRODUCT', 'undef')


def getServerBuildSource():
    return os.environ.get('BAMBOO_SERVER_BUILD_SOURCE', 'default')


def getSenServerPlatform(server_build_source):
    platform = server_build_source.split(' ')[0].strip()
    if platform == 'Windows': os = 'Windows'
    else: os = 'Posix'
    return (os, platform)


def getSenServerSource(server_build_source, clientDistribution, clientCompiler, clientTarget,clientBitness):
    if server_build_source == '' or server_build_source == 'default':
        return (clientDistribution, clientCompiler, clientTarget,clientBitness)
    else:
        serverDistribution = server_build_source.split(' ')[1].strip()
        serverCompiler = server_build_source.split(' ')[2].strip()
        serverTarget = server_build_source.split(' ')[3].strip()
        serverBitness = server_build_source.split(' ')[4].strip()
        return (serverDistribution, serverCompiler, serverTarget,serverBitness)


#def parseSENDataSource(datasource):
#    platform = datasource.split(' ')[0].strip()
#    distro = datasource.split(' ')[1].strip()
#    compiler = datasource.split(' ')[2].strip()
#    bitness = datasource.split(' ')[3].strip()
#    if plaloadPlanSettingstform == 'Windows': os = 'Windows'
#    else: os = 'Posix'
#    return (os, platform, distro, compiler, bitness)


# set turn off skipper option
def setSkipperFlag(longPlanNameArray):
    if not isNewPlan(longPlanNameArray):
        os.environ['USE_SKIPPER'] = 'False'
    #elif 'TURN_OFF_SKIPPER' in os.environ.keys() or 'BAMBOO_TURN_OFF_SKIPPER' in os.environ.keys():
    #    os.environ['USE_SKIPPER'] = 'False'
    elif os.environ.get('TURN_OFF_SKIPPER', '0') == '1':
        os.environ['USE_SKIPPER'] = 'False'
    elif os.environ.get('BAMBOO_TURN_OFF_SKIPPER', '0') == '1':
        os.environ['USE_SKIPPER'] = 'False'
    else:
        os.environ['USE_SKIPPER'] = 'True'
    print("USE_SKIPPER: " + os.environ['USE_SKIPPER'])


# set env variables that skipper needs to read
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
    mvnHomeSetting = getBambooCapability(mvnHomeSetting, bambooVarName)
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

    #javaHomeSetting = os.environ.get('BOOSTER_VAR_' + java.upper() + '_HOME', 'unset')
    #bambooVarName = 'BAMBOO_CAPABILITY_SYSTEM_JDK_JDK' + javaVersion
    #javaBitness = settings.get('bitness', '64')
    #if javaBitness == '32':
    #    bambooVarName = bambooVarName + 'X86'
    #javaHomeSetting = getBambooCapability(javaHomeSetting, bambooVarName)
    setUndefAttribute(node, 'JAVA_HOME', javaHomeSetting)
    return java


#def setJavaversion(javaVersion, settings):
    """
    Set Java version in environment variable.
    :param node: element.
    :param settings: plan settings.
    :return: Java version.
    """
#    if javaVersion == 'unset':
#        java = settings.get('compiler', None)
#        if java is None:
#            raise KeyError('Java version cannot be determined')
#        return java
#    else:
#        java = 'JDK' + javaVersion
#        return java



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


# helper function to compare bamboo capability
def getBambooCapability(var, bamboo_var):
    """ Match variable to bamboo capability, return capability if bamboo
    capability exists and is different, return original variable otherwise.
    Logs warnings when capability is returned instead

    Args:
        var (str): the original variable value
        bamboo_var(str): the name of the bamboo capability environment variable

    Returns:
        str: the final value of the variable after comparison
    """
    capability = os.environ.get(bamboo_var, None)
    if capability is None or var == capability:
        return var
    else:
        message = 'WARNING! Current setting differs from bamboo capability'
        message += '\n overriding %s with %s\n'
        logger.critical(message % (var, capability))
        return capability

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
