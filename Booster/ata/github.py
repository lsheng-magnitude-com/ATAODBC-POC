import re
import json
from pprint import pprint
import os
import platform


def initPlanSettings(settings):

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
        settings['bitness'] = getBitnessFromPlanName(longPlanNameArray, planNameArray, jobNameArray,
                                                     settings['compiler'])
        # print('bitness = ' + settings['bitness'])

    if getDriverTypeFromPlanName(projectNameArray, settings['compiler'], settings['plantype']) is not None:
        settings['drivertype'] = getDriverTypeFromPlanName(projectNameArray, settings['compiler'], settings['plantype'])
        # print('drivertype = ' + settings['drivertype'])

    if getDMNameFromPlanName(longPlanNameArray, planNameArray, jobNameArray, settings['plantype'],
                             settings['drivertype']) is not None:
        settings['dm_name'] = getDMNameFromPlanName(longPlanNameArray, planNameArray, jobNameArray,
                                                    settings['plantype'], settings['drivertype'])
        # print('dm_name = ' + settings['dm_name'])

    if getDMVersionFromPlanName(longPlanNameArray, jobNameArray) is not None:
        settings['dm_version'] = getDMVersionFromPlanName(longPlanNameArray, jobNameArray)
        # print('dm_version = ' + settings['dm_version'])

    if getDMFromPlanName(longPlanNameArray, planNameArray, jobNameArray, settings['plantype'],
                         settings['drivertype']) is not None:
        settings['dm'] = getDMFromPlanName(longPlanNameArray, planNameArray, jobNameArray, settings['plantype'],
                                           settings['drivertype'])
        # print('dm = ' + settings['dm'])

    if getJreFromPlanName(longPlanNameArray, planNameArray, settings['plantype'], settings['drivertype']) is not None:
        settings['jre'] = getJreFromPlanName(longPlanNameArray, planNameArray, settings['plantype'],
                                             settings['drivertype'])
        # print('jre = ' + settings['jre'])

    if getTestPlatformFromPlanName(longPlanNameArray, planNameArray, settings['plantype']) is not None:
        settings['test_platform'] = getTestPlatformFromPlanName(longPlanNameArray, planNameArray, settings['plantype'])
        # print('test_platform = ' + settings['test_platform'])

    if getPackagePlatformFromPlanName(longPlanNameArray, planNameArray, settings['plantype']) is not None:
        settings['package_platform'] = getPackagePlatformFromPlanName(longPlanNameArray, planNameArray,
                                                                      settings['plantype'])
        # print('package_platform = ' + settings['package_platform'])

    if getOSArchFromPlanName(longPlanNameArray, planNameArray, settings['plantype']) is not None:
        settings['os_arch'] = getOSArchFromPlanName(longPlanNameArray, planNameArray, settings['plantype'])
        # print('os_arch = ' + settings['os_arch'])

    if getTestTypeFromPlanName(longPlanNameArray, projectNameArray, settings['plantype']) is not None:
        settings['testtype'] = getTestTypeFromPlanName(longPlanNameArray, projectNameArray, settings['plantype'])
        # print('testtype = ' + settings['testtype'])

    if getPackageTypeFromPlanName(projectNameArray) is not None:
        settings['packagetype'] = getPackageTypeFromPlanName(projectNameArray)
        if settings['plantype'] != 'packagetest':
            settings['bitness'] = getBitnessForPackagePlan(settings['packagetype'], settings['platform'],
                                                           settings['bitness'])
            # print('packagetype = ' + settings['packagetype'])

    if getPackageFormatFromPlanName(projectNameArray, planNameArray) is not None:
        settings['packageformat'] = getPackageFormatFromPlanName(projectNameArray, planNameArray)
        # print('packageformat = ' + settings['packageformat'])

    if settings['plantype'] == 'packagetest':
        settings['distribution'] = getDistributionForPackageTest()
        settings['package_platform'] = getPackagePlatformForPackageTest(settings['distribution'])
        settings['packageformat'] = getPackageFormatForPackageTest(settings['packagetype'], settings['platform'],
                                                                   settings['package_platform'])

    # override setting with bamboo variable
    if getCompilerFromBambooVariable() is not None and getCompilerFromBambooVariable() != '': settings['compiler'] = getCompilerFromBambooVariable()
    if getDistributionFromBambooVariable() is not None and getDistributionFromBambooVariable() != '': settings['distribution'] = getDistributionFromBambooVariable()
    if getBranchFromBambooVariable() is not None and getBranchFromBambooVariable() != '': settings['branch'] = getBranchFromBambooVariable()
    if getTestTypeFromBambooVariable() is not None and getTestTypeFromBambooVariable() != '': settings['testtype'] = getTestTypeFromBambooVariable()
    if getPackageTypeFromBambooVariable() is not None and getPackageTypeFromBambooVariable() != '': settings['packaggetype'] = getPackageTypeFromBambooVariable()
    if getDSVersionFromBambooVariable() is not None and getDSVersionFromBambooVariable() != '': settings['ds_version'] = getDSVersionFromBambooVariable()
    if getTestsuiteListFromBambooVariable() is not None and getTestsuiteListFromBambooVariable() != '': settings['testsuitelist'] = getTestsuiteListFromBambooVariable()
    if getAflFlagFromBambooVariables() is not None and getAflFlagFromBambooVariables() != '': settings['afl'] = getAflFlagFromBambooVariables()
    if getDynamiclinkingFlagFromBambooVariables() is not None and getDynamiclinkingFlagFromBambooVariables() != '': settings['dynamic_linking'] = getDynamiclinkingFlagFromBambooVariables()
    if getSignedFlagFromBambooVariables() is not None and getSignedFlagFromBambooVariables() != '': settings['signed'] = getSignedFlagFromBambooVariables()
    if getMemoryTestFlagFromBambooVariables() is not None and getMemoryTestFlagFromBambooVariables() != '': settings['memory_test'] = getMemoryTestFlagFromBambooVariables()
    if getJunitTestFlagFromBambooVariables() is not None and getJunitTestFlagFromBambooVariables() != '': settings['junit_test'] = getJunitTestFlagFromBambooVariables()
    if getAppVerifierFlagFromBambooVariables() is not None and getAppVerifierFlagFromBambooVariables() != '': settings['appverifier'] = getAppVerifierFlagFromBambooVariables()
    if getVeracodeFlagFromBambooVariables() is not None and getVeracodeFlagFromBambooVariables() != '': settings['veracode'] = getVeracodeFlagFromBambooVariables()
    if getRemoteTestFlagFromBambooVariables() is not None and getRemoteTestFlagFromBambooVariables() != '': settings['remote_test'] = getRemoteTestFlagFromBambooVariables()
    if getCodeAnalysisFlagFromBambooVariables() is not None and getCodeAnalysisFlagFromBambooVariables() != '': settings['code_analysis'] = getCodeAnalysisFlagFromBambooVariables()
    if getDMVersionFromBambooVariable() is not None and getDMVersionFromBambooVariable() != '': settings['dm'] = settings['dm_name'] + '-' + getDMVersionFromBambooVariable()
    if getDMFromBambooVariable() is not None and getDMFromBambooVariable() != '': settings['dm'] = getDMFromBambooVariable()
    if getDriverLogLevelFromBambooVariable() is not None and getDriverLogLevelFromBambooVariable() != '': settings['log_level'] = getDriverLogLevelFromBambooVariable()
    if getDMTraceFromBambooVariable() is not None and getDMTraceFromBambooVariable() != '': settings['dm_trace'] = getDMTraceFromBambooVariable()
    if getBuildTargetFromBambooVariable() is not None and getBuildTargetFromBambooVariable() != '': settings['buildtarget'] = getBuildTargetFromBambooVariable()
    if getCustomerFromBambooVariable() is not None and getCustomerFromBambooVariable() != '': settings['customer'] = getCustomerFromBambooVariable()
    if getRetailFlagFromBambooVariable() is not None and getRetailFlagFromBambooVariable() != '': settings['retail'] = getRetailFlagFromBambooVariable()
    if getCodeSigningPlatformFromBambooVariable() is not None and getCodeSigningPlatformFromBambooVariable() != '':
        settings['codesigningplatform'] = getCodeSigningPlatformFromBambooVariable()
        settings['codesigning'] = '1'
        if settings['codesigningplatform'] == 'osx':
            settings['codesigningplatform'] = 'OSX'
    else:
        settings['codesigning'] = '0'
    if getDockerServerformFromBambooVariable() is not None and getDockerServerformFromBambooVariable() != '':
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
            p = value.split("=", 1)
            if (len(p)) == 2:
                varName = 'locator_' + p[0].strip()
                settings[varName.lower()] = p[1].strip()
                os.environ[varName.upper()] = p[1].strip()

    # Parse DataSourceVersion for SEN C/S test plans
    if 'SEN' in settings['project'] and settings['product'] == 'Client' and settings['plantype'] == 'test':
        settings['clientserver'] = '1'
        settings['server_product'] = getServerFromBambooVariables()
        settings['server_branch'] = getServerBranchFromBambooVariables(settings['branch'])
        settings['server_build_source'] = getServerBuildSource()
        (settings['server_os'], settings['server_platform']) = getSenServerPlatform(settings['server_build_source'])
        (settings['server_distribution'], settings['server_compiler'], settings['server_target'],
         settings['server_bitness']) = getSenServerSource(settings['server_build_source'], settings['distribution'],
                                                          settings['compiler'], settings['buildtarget'],
                                                          settings['bitness'])

    else:
        settings['clientserver'] = '0'
        pass
    setSkipperFlag(longPlanNameArray)

    return settings


# functions used by the init function
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