import re
import json
from pprint import pprint
import os
import platform


def initPlanSettings(settings):
    print os.environ.get('GITHUB_REPOSITORY')
    print os.environ.get('GITHUB_WORKFLOW')
    print os.environ.get('GITHUB_REF')
    print os.environ.get('GITHUB_JOB')
    return settings


def initCompilerSettings(planSettings):
    settings = {}
    return settings