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
    category, product, type = (repo.split('/')[-1]).split('-')
    plan_type = workflow.split('-')[0].strip()
    env = workflow.split('-')[1].strip()
    branch = ref.split('/')[-1]
    category = category.strip()
    product = product.strip()
    type = type.strip()
    plan_type = plan_type.strip()
    print env
    distribution = env.split(' ')[0].strip()
    compiler = env.split(' ')[1].strip()
    bitness = env.split(' ')[2].strip()
    branch = branch.strip()

    settings['platform'] = ''
    settings['project'] = category + type
    settings['product'] = product
    settings['product_lower'] = product.lower()
    settings['branch'] = branch
    settings['plantype'] = plan_type
    settings['distribution'] = distribution
    settings['compiler'] = compiler
    settings['plan'] = ''
    settings['job'] = job
    settings['buildtarget'] = ''
    settings['bitness'] = bitness
    settings['drivertype'] = ''
    settings['dm_name'] = ''
    settings['dm_version'] = ''
    settings['dm'] = ''
    settings['jre'] = ''
    settings['test_platform'] = ''
    settings['package_platform'] = ''
    settings['os_arch'] = ''
    settings['testtype'] = ''
    settings['packagetype'] = ''
    settings['packageformat'] = ''

    return settings


def initCompilerSettings(planSettings):
    settings = {}
    return settings