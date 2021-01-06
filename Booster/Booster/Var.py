#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import re
import datetime

_varDict = {
    '__BUILD_TIME__': { 'value': datetime.datetime.now().strftime('%Y-%m-%d %H:%M'), 'source': None },
}
_override = []


def str2dict(s):
    """
    Convert a string into dictionary. The string is a list of lines, each in format of name = value
    :param s:       input string
    :return:        dictionary
    """
    d = dict({})
    for i in s.split('\n'):
        t = i.split('=', 1)
        if len(t) == 2:
            name = t[0].strip()
            value = t[1].strip()
            if re.match(r"""^(['"])(.*)\1""", value):
                value=value[1:-1]       # if the value is quoted, strip the quotes
            if len(name) > 0:
                d[name] = value
    return d

def file2dict(fname):
    """
    Convert the content of a text file into a dictionary using str2dict
    :param s:
    :return:
    """
    with open(fname, 'r') as fh:
        txt = fh.read()
        return str2dict(txt)


p1 = re.compile(r'\$\((\w+)\)', re.I)           # $(tag)
p2 = re.compile(r'\$(\w+)', re.I)               # $tag


def expandMacro(s, r=None, raiseUnknown=False):
    """
    Expand macros
    :param s:           target can be a string, array, or dict
    :param r:           a dictionary of macros
    :raiseUnknown       if set, raise error if macro is not defined in r
    :return:            expanded result, depends on by value or by reference
    """
    if isinstance(s, dict):
        if r is None:
            r = s
        for n in s:
            s[n] = expandMacro(s[n], r, raiseUnknown)
        return s
    if r is None or not isinstance(r, dict):
        raise ValueError('invalid macro define')
    if isinstance(s, str):
        s = _rep_pattern(s, p1, r, raiseUnknown)
        s = _rep_pattern(s, p2, r, raiseUnknown)
        return s
    if isinstance(s, list):
        for n in s:
            s[n] = expandMacro(s[n], r, raiseUnknown)
        return s
    raise ValueError('invalid argument')


def _rep_pattern(v, pat, r, raiseUnknown=False):
    if r is not None and isinstance(r, dict):
        off = 0
        while off < len(v):
            m = pat.search(v[off:])
            if not m:
                break
            tag = m.group(1)
            if tag in r:
                v = v.replace(m.group(0), r[tag])
            elif raiseUnknown:
                raise ValueError
            else:
                off += m.end(0)
    return v



class VarMgr(object):
    """
    Variable manager - trace variable load/override/substitute etc

    """

    # def __init__(self):
    #     if not vm_initialized:
    #         # TODO
    #         vm_initialized = True
    #         self.add('BUILD-TIME', datetime.datetime.now().strftime('%Y-%m-%d %H:%M'))


    def add(self, name, value, source=None):
        """
        Add (register) a variable, if it exists already, put the old define in override history

        :param name:        name of variable
        :param value:       value of variable
        :param source:      source xml file that defines variable
        :return:            None
        """
        global _varDict
        global _override
        if name in _varDict:
            # configure xml files are potentially loaded several times
            # only record those are _really_ overridden
            if value != _varDict[name]['value'] or source != _varDict[name]['source']:
                _override.append(dict({'name': name,
                    'value': value,
                    'source': source,
                    'orgValue': _varDict[name]['value'],
                    'orgSource': _varDict[name]['source']}))
        _varDict[name] = dict({ 'value': value, 'source': source })


    def get(self, name, fallback=None):
        """
        Return the value of a variable specified by name
        :param name:        name of the variable
        :param fallback:    value if the name variable does not exist
        :return:            value
        """
        global _varDict
        return _varDict[name]['value'] if name in _varDict else fallback


    def dumpAll(self, withSource=True):
        """
        Dump all "current" variables, ordered in name
        :param withSource:      show source xml
        :return:
        """
        print('--------------dumpAll------------')
        global _varDict
        names = _varDict.keys()
        names.sort()
        lastFile = None
        for name in names:
            if withSource and lastFile != _varDict[name]['source']:
                lastFile = _varDict[name]['source']
                print('{name}={value}\n    {file}'.format(name=name, value=_varDict[name]['value'], file=_varDict[name]['source']))
            else:
                print('{name}={value}'.format(name=name, value=_varDict[name]['value']))

    def dumpOverride(self, name=None):
        """
        Dump the override history, ordered in override order
        :param name:    None for all variables, otherwise only the named variable is dumped
        :return:        None
        """
        global _varDict
        global _override
        if len(_override) > 0:
            print('--------------dumpOverride------------')
            for e in _override:
                if name is None or e['name'] == name:
                    if e['value'] == e['orgValue']:
                        # override with the same value, usually an error
                        print('{name}={value} [{source}]\n    from [{orgSource}]'.format(**e))
                    else:
                        # override with different value
                        print('{name}={value} [{source}]\n    from {orgValue} [{orgSource}]'.format(**e))


if __name__ == '__main__':
    v = VarMgr()
    v.add('abc', 'sunny', 'sys.xml')
    v.add('greet', 'hello', 'sys.xml')
    v.add('abc', 'rain', 'van.xml')
    v.add('alla', 'hello', 'van.xml')
    v.add('greet', 'Hello, world', 'simba.xml')
    v.add('abc', 'alphabet', 'simba.xml')
    v.add('log', 'here', 'simba.xml')

    v.dumpAll()
    v.dumpOverride()
    v.dumpOverride('abc')

