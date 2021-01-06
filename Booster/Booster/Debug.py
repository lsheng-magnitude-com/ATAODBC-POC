#! /usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import re
import ata.log

logger = ata.log.AtaLog(__name__)


class Debug(object):
    """
    Debug utilities, which are useful on local debugging

    skip        skip modules according to environ DEBUG_SKIP
                e.g.
                if you have sync driver source and don't want to repeat sync during debug iteration
                    DEBUG_SKIP=skipper,p4revert,p4sync
                if you want skip everything but copy
                    DEBUG_SKIP=all,-copy

                skipper     don't notify skipper (almost always set in local debugging)
                p4revert    don't p4revert (in case you want to keep your change)
                p4sync      don't sync if you have sync already (manually or in the previous iteration)
                extract     don't extract from nfs zip/tar
                remove      don't remove so you can check the result of execution
                copy        don't copy, for whatever reasons

    trace       dump information such as
                xmlparse    import sequence
                var         vars and their override history
                xmlstrip    when an xml node is removed during filter


    """
    # modules that are skipped
    initialized = False
    skipAll = ('skipper', 'p4revert', 'p4sync', 'extract', 'remove', 'copy',
               'make', 'ts', 'ant', 'jts', 'zip', 'tar', 'biinject', 'p4changes')
    skipDict = {}
    traceAll = ('xmlparse', 'xmlstrip', 'var', 'exec')
    traceDict = {}

    def __init__(self):
        if not Debug.initialized:
            self._parseEnv('DEBUG_SKIP', Debug.skipAll, Debug.skipDict)
            self._parseEnv('DEBUG_TRACE', Debug.traceAll, Debug.traceDict)
            Debug.initialized = True

    def _parseEnv(self, name, optList, optDict):
        if name in os.environ:
            v = os.environ[name]
            # items are separated by these chars
            vlist = [i.lower() for i in re.split(r'[ ,:;]+', v) if len(i) > 0]
            if len(vlist) == 0:
                return
            for i in vlist:
                if i == 'all':  # all supported items
                    optDict.update(optList)
                elif i[:1] == '-':  # use to remove from all-list
                    i = i[1:]
                    if i in optDict:
                        del optDict[i]
                else:  # add named
                    optDict[i] = True


    def skip(self, name, msg=None):
        """
        Return True if the name is in the list of DEBUG_SKIP, and print msg if applicable
        This is used to skip specified modules

        :param name:        name to check
        :param msg:         message to print/log when matched
        :return:            True if in the list
        """
        name = name.strip().lower()
        if name in Debug.skipDict:
            if msg != None and msg != '':
                print(msg)
                logger.info(msg)
            return True
        else:
            return False


    def trace(self, name):
        """
        Return True if the name is in the list of DEBUG_TRACE
        This is used to trace/print additional information

        :param name:        name to check
        :return:            True if in the list
        """
        name = name.strip().lower()
        return name in Debug.traceDict


if __name__ == '__main__':
    d = Debug()
    for i in ('what', 'p4sync'):
        print('%s=%s' % (i, d.skip(i)))
    d.skip('copy', 'copy is skipped')
