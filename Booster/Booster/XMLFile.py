#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
import os.path
import re
import xml.etree.ElementTree as ET
from Booster.Debug import Debug as Debugger
import weakref

_search_path = []

def dumpXMLNode(node, showAttr=True, showParent=False, showChildren=False):
    """
    A convenient function to dump "most" info of an XML tag

    :param node:
    :param showAttr:
    :param showParent:
    :param showChildren:
    :return:
    """
    print('{tag}: {text}'.format(tag=node.tag, text=node.text))
    if showAttr:
        for a in node.attrib:
            print('    {name}={value}'.format(name=a, value=node.attrib[a]))
    if showParent:
        try:
            p = node.find('..')
            print('    parent={}'.format(p.tag))
        except:
            pass
    if showChildren:
        for c in list(node):
            print('    --{tag}: {text}'.format(tag=c.tag, text=c.text))


def getFileName(fname, optional=False):
    """
    Get required file by searching the search path in the following order:
        environment CONFIG_PATH or BAMBOO_CONFIG_PATH
        current working directory
        the directory of start script
        
    :param fname:           The file name to check
    :param optional:        if not exists, ignore (True) or raise RuntimeError
    :return:                actual file name if found, or None
    """
    if len(_search_path) == 0:
        spl = []
        for k in os.environ.keys():
            if re.match(r'(bamboo_)?CONFIG_PATH$', k, re.IGNORECASE):
                spl.extend(os.environ[k].split(os.pathsep))
        _search_path.extend([p.strip() for p in spl if p.strip()])
        _search_path.append(os.getcwd())
        _search_path.append(os.path.abspath(os.path.dirname(sys.argv[0])))

    if not os.path.isabs(fname):
        for path in _search_path:
            fname_alt = '{}/{}'.format(path, fname)
            if os.path.exists(fname_alt):
                return fname_alt
    elif os.path.exists(fname):
        return fname

    if not optional:
        raise RuntimeError(fname + ' not found')
    return None


class XMLFile(object):
    """
    ET Wrapper

    """
    def __init__(self, filename):
        fname = getFileName(filename)
        self.filename = os.path.normpath(fname)
        if Debugger().trace('xmlparse'):
            print('Load XML {} ============='.format(self.filename))
        self._tree = ET.parse(filename)
        self._root = self._tree.getroot()
        # add weakref to it parent for each node
        self._root.parent = None
        for elem in self._root.iter():
            for c in elem:
                c.parent = weakref.ref(elem)

    def __del__(self):
        if Debugger().trace('xmlparse'):
            print('Load {} done ------------'.format(self.filename))

    def tree(self):
        return self._tree

    def root(self):
        return self._root

    def iter(self, tag=None):
        return self._root.iter(tag)

    def children(self):
        return list(self._root)

    def dumpChildren(self, showAttr=True, showParent=False, showChildren=False):
        print('dumpChildren(%s)' % self.filename)
        for c in list(self._root):
            dumpXMLNode(c, showAttr, showParent, showChildren)

    def dumpTags(self, showAttr=True, showParent=False, showChildren=False):
        print('dumpTags(%s)' % self.filename)
        for c in self._root.iter():
            dumpXMLNode(c, showAttr, showParent, showChildren)



if __name__ == '__main__':
    #TODO
    pass
