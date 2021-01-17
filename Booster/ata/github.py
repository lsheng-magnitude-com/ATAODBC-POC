import re
import json
from pprint import pprint
import os
import platform


def initPlanSettings(settings):
    repo = os.environ.get('GITHUB_REPOSITORY')
    workflow = os.environ.get('GITHUB_WORKFLOW')
    ref = os.environ.get('GITHUB_REF')
    job = os.environ.get('GITHUB_JOB')
    category = (repo.split('/')[-1]).split('-')[0]
    product = (repo.split('/')[-1]).split('-')[1]
    type = (repo.split('/')[-1]).split('-')[2]
    workflow_type = workflow.split('-')[0].strip()
    env = workflow.split('-')[1].strip()
    branch = ref.split('/')[-1].strip()
    category = category.strip()
    product = product.strip()
    type = type.strip()
    distribution = env.split(' ')[0].strip()
    compiler = env.split(' ')[1].strip()

    settings['platform'] = getPlatform()
    settings['project'] = category + type
    settings['product'] = product
    settings['product_lower'] = product.lower()
    settings['drivertype'] = getDriverType(type)
    settings['plantype'] = getPlanType(workflow_type)
    settings['branch'] = branch
    settings['distribution'] = distribution
    settings['compiler'] = compiler
    settings['job'] = job
    settings['buildtarget'] = getBuildTarget()
    settings['bitness'] = getBitness(env, settings['drivertype'])
    settings['dm'] = getDM(env, settings['drivertype'], settings['plantype'])
    settings['jre'] = getJre(env, settings['drivertype'], settings['plantype'])
    settings['test_platform'] = getTestPlatform(distribution, settings['plantype'])
    settings['package_platform'] = getPackagePlatform(distribution, settings['plantype'])
    settings['os_arch'] = getOSArch(env, settings['plantype'])
    settings['testtype'] = getTestType(workflow_type)
    settings['packagetype'] = getPackageType(workflow_type)
    settings['packageformat'] = getPackageFormat(env, settings['plantype'])

    return settings


def getPlatform():
    current_platform = platform.system()
    if current_platform == 'Darwin':
        return 'OSX'
    return current_platform


def getPlanType(workflow_type):
    if workflow_type == 'Compile': return 'build'
    if workflow_type == 'TestFunctional': return 'test'
    if workflow_type == 'TestThirdParty': return 'test'
    if workflow_type == 'TestSmoke': return 'test'
    if workflow_type == 'PerformanceTest': return 'test'
    if workflow_type == 'InstallerTest': return 'packagetest'
    if workflow_type == 'OEMTest': return 'packagetest'
    if workflow_type == 'PackageOEM': return 'package'
    if workflow_type == 'PackageInstaller': return 'package'
    if workflow_type == 'RetailPackage': return 'package'
    if workflow_type == 'Installer': return 'package'
    if workflow_type == 'CodeSigning': return 'package'
    if workflow_type == 'SignedInstaller': return 'signedpackage'
    if workflow_type == 'SignedOEM': return 'signedpackage'
    if workflow_type == 'Deploy': return 'deploy'


def getBuildTarget():
    return 'release'


def getDriverType(type):
    return type.lower()


def getBitness(env, drivertype):
    if drivertype == 'jdbc':
        return '3264'
    else:
        return env.split(' ')[2].strip()


def getDM(env, drivertype, plantype):
    if drivertype == 'odbc' and plantype == 'test':
        return env.split(' ')[3].strip()
    else:
        return 'undef'


def getJre(env, drivertype, plantype):
    if drivertype == 'jdbc' and plantype == 'test':
        return env.split(' ')[2].strip()
    else:
        return 'undef'


def getTestPlatform(distribution, plantype):
    if plantype == 'test':
        return distribution
    else:
        return 'undef'


def getPackagePlatform(distribution, plantype):
    if plantype == 'package' or plantype == 'signedpackage':
        return distribution
    else:
        return 'undef'


def getOSArch(env, plantype):
    if plantype == 'test':
        return env.split(' ')[2].strip()
    else:
        return 'undef'


def getTestType(workflow_type):
    if workflow_type == 'TestFunctional':
        return 'functionaltest'
    elif workflow_type == 'TestThirdParty':
        return 'thirdpartytest'
    elif workflow_type == 'TestSmoke':
        return 'functionaltest'
    elif workflow_type == 'PerformanceTest':
        return 'performancetest'
    elif workflow_type == 'InstallerTest':
        return 'installertest'
    elif workflow_type == 'OEMTest':
        return 'oemtest'
    else:
        return 'undef'


def getPackageType(workflow_type):
    if 'OEM' in workflow_type: return 'OEM'
    if 'Installer' in workflow_type: return 'installer'
    if 'RetailPackage' in workflow_type: return 'retailzip'
    return 'undef'


def getPackageFormat(env, plantype):
    if plantype == 'package' or plantype == 'signedpackage':
        return env.split(' ')[2].strip()
    else:
        return 'undef'


def getImportFile(file, optional):
    workspace = os.environ.get('GITHUB_WORKSPACE')
    if os.path.exists(os.path.join(BOOSTER_DIR, file)):
        importfile = os.path.join(BOOSTER_DIR, file)
    elif os.path.exists(os.path.join(workspace, file)):
        importfile = os.path.join(os.path.join(workspace, file))
    else:
        importfile = syncConfigFile(file, 'default')
    if not os.path.exists(importfile):
        if optional:
            return None
        else:
            raise RuntimeError(fname + ' not found')
    return importfile


def initCompilerSettings(planSettings):
    settings = {}
    return settings