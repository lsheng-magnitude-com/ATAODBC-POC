from __future__ import print_function

import os
import glob
import traceback

import AtaUtil
import Command
from distutils.file_util import copy_file
import ata.log
from Booster.Action import Action
import shutil

_logger = ata.log.AtaLog(__name__)

class CopyAs(Action):
    """
    CopyAs      Copy and rename a file.

    This is a simple and fast version of <Copy>. It can be used to reorganize files and keep origin untouched.
    The main purpose of the module is to demonstrate the OOP style to implement an action tag.
    """

    def __init__(self, root):
        super(CopyAs, self).__init__(root, 'CopyAs')
        self.source = root.text
        self.dest = root.attrib.get('dest', None)

    def _perform(self, dry=False):
        _logger.info('Copy ' + self.source + ' to ' + self.dest)
        if not dry:
            shutil.copyfile(self.source, self.dest)

def Execute(root):
    action = CopyAs(root)
    action.run()

def Debug(root):
    action = CopyAs(root)
    action.run()


