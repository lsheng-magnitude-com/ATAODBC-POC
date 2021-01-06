import re
import json
from pprint import pprint


def translateFromBambooVars(h):
    ''' translate bamboo variables, stripping BAMBOO_ prefix
    '''
    nh = {}
    for i in h:
        if i[:7].upper() == 'BAMBOO_':
            nh[i[7:]] = h[i]
        else:
            nh[i] = h[i]
    return h

def getBambooVar(h, name):
    ''' Get a bamboo variable. Bamboo may change cases
    '''
    bn = 'bamboo_' + name
    if h.has_key(bn):
        return h[bn]
    bn = 'BAMBOO_' + name
    if h.has_key(bn):
        return h[bn]
    bn = 'BAMBOO_' + name.upper()
    if h.has_key(bn):
        return h[bn]
    return ''

def getBambooVars(h, names):
    ''' Return a subset of bamboo vars, filtered by names, stripping bamboo_
    '''
    d = {}
    for i in names:
        v = getBambooVar(i)
        if i != None:
            d[i] = v
    return d

def decodePlan(key, name):
    """ decode Bamboo plan key/name
        return a dict
    """
    pi = dict(zip('project plan branch'.split(' '), re.split(r' - ', name)))
    pprint(pi)
    pi['planType'] = key[:4]
    pi['driverType'] = key[4:5]
    pi['driverCategory'] = key[5:8]
    pi['osCode'] = key[9:18]
    pi['projectFunction'], pi['driverTypeName'], pi['driverCategoryName'] = pi['project'].split(' ')
    pi['driverGroup'] = pi['driverCategoryName']
    if pi['planType'] == 'BULD':
        pi['compilerCode'] = key[18:27]
        pi['driverBit'] = key[27:29]
        pi['osName'], pi['osVersion'], pi['compilerName'], pi['compilerVersion'], _ = pi['plan'].split(' ')
    elif pi['planType'][:3] == 'TST':
        pi['osBit'] = key[18:20]
        pi['driverBit'] = key[20:22]
        pi['dmcode'] = key[22:23]
        pi['osName'], pi['osVersion'], pi['osArch'], _, pi['dmName'] = pi['plan'].split(' ')
    elif pi['planType'][:3] == 'PKG':
        pi['compilerCode'] = key[18:27]
        pi['driverBit'] = key[27:29]
        pi['osName'], pi['osVersion'], pi['compilerName'], pi['compilerVersion'], _, pi['pkg'] = pi['plan'].split(' ')
    pi['driverName'], pi['driverBranch'] = pi['branch'].split(' ')
    return pi

