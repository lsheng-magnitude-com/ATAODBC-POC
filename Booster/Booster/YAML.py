#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
import os.path
import re
from Booster.Debug import Debug as Debugger
try:
    import yaml
except:
    pass


def searchKey(inputDict, key):
    if hasattr(inputDict, 'items'):
        for k, v in inputDict.items():
            if k == key:
                yield v
            if isinstance(v, dict):
                for result in searchKey(v, key):
                    yield result
            elif isinstance(v,list):
                for item in v:
                    for result in searchKey(item, key):
                        yield result


class YAML(object):
    def __init__(self, file):
        self.file = os.path.normpath(file)
        if Debugger().trace('yamlparse'):
            print('Load YAML {} ============='.format(self.file))
        with open(file, 'r') as stream:
            self._dict=yaml.safe_load(stream)

    def __del__(self):
        if Debugger().trace('yamlparse'):
            print('Load {} done ------------'.format(self.file))


    def display(self):
        print((self._dict))


    def find(self, key):
        renturn (list(searchKey(self._dict, key)))

    def update(self, new_dict):
        self._dict.update(new_dict)
        with open(self.file, "w") as f:
            yaml.safe_dump(self._dict, f, default_flow_style=False)


if __name__ == '__main__':
    #TODO
    pass
