from __future__ import print_function

import sys
import os
# import traceback

from Booster.Action import Action
# import AtaUtil
import re

"""
Run a module method mod.action(**kw)
kw are attributes except following reserved attributes:
  name          name of the module
  paths         list of path to search module
  cwd           workding directory to run the module
"""

#import ata.log
#logger = ata.log.AtaLog(__name__)



class RunModule(Action):
    _context = '''def mod_action(*args, **kw):
    import {}
    return {}.action(*args, **kw)
'''

    def __init__(self, root):
        super(RunModule, self).__init__(root, 'RunModule')
        self.root = root
        self.paths = re.split(r'[,:; ]+', root.attrib.get('paths', ''))
        self.name = root.attrib.get('name')
        self.cwd = root.attrib.get('cwd')
        self.args = {
            'text': root.text
        }
        for i in root.attrib:
            if i not in ('name', 'paths', 'cwd'):
                self.args[i] = root.attrib[i]

    def _perform(self, dry=False):
        """
        Replace/Inject named variables into source files
        :param dry:
        :return:
        """
        if dry:
            # print-alt: logger.debug()
            if len(self.paths) > 0:
                print('module search path:')
                for i in self.paths:
                    print('    {}'.format(i))
            if self.cwd:
                print('    cwd={}')
            if self.args:
                print('    Arguments:')
                for i in self.args:
                    print('      {}={}'.format(i, self.args[i]))
        else:
            npaths = len(self.paths)
            if npaths > 0:
                sys.path.extend(self.paths)
            if self.cwd:
                cwd0 = os.getcwd()
                os.chdir(self.cwd)
            try:
                if self.cwd:
                    os.chdir(self.cwd)
                exec(RunModule._context.format(self.name, self.name))
                #return mod_action(**(self.args))
                return None
            except Exception as e:
                print('RunMod: Exception: {}'.format(e))
                raise
            finally:
                if self.cwd:
                    os.chdir(cwd0)
                if npaths > 0:
                    sys.path = sys.path[:-npaths]


def Execute(root):
    print('==============================')
    print('      Enter RunMod')
    print('==============================')
    mod = RunModule(root)
    return mod.run()

def Debug(root):
    print('==============================')
    print('      Enter RunMod')
    print('==============================')
    mod = RunModule(root)
    mod.run(dry=True)

