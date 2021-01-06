from __future__ import print_function
import os
import re
import subprocess
from Booster.Action import Action
import Booster.P4Changes as P4Changes
from BoosterError import BoosterError
from Booster.Var import VarMgr
from Booster.Debug import Debug as Debugger

import ata.log
logger = ata.log.AtaLog(__name__)

class BIInject(Action):
    _patn_vars = re.compile(r',\s*')        # variable separator
    _patn_have = re.compile(r' - ')         # p4have separator

    def __init__(self, root):
        """
        The node should have following attributes
            path            P4 path to the target
            vars            list of tags to be replaced, tags are also the names in VarMgr
        :param root:
        """
        super(BIInject, self).__init__(root, 'BIInject')
        self.path = set()
        path = root.attrib.get('path')
        if path is not None:
            self.path.add(path)
        for path in root.findall('path'):
            self.path.add(path.text)
        if not self.path:
            raise BoosterError('path expected, either by attribute or children nodes')
        self.vars = BIInject._patn_vars.split(root.attrib.get('vars', '__BUILD_INFO__, __BUILD_TIME__'))
        self.p4 = os.environ.get('BAMBOO_CAPABILITY_SYSTEM_P4EXECUTABLE', 'p4')
        # check if vars are defined
        vm = VarMgr()
        for v in self.vars:
            if vm.get(v) is None:
                raise BoosterError('variable {} is not found'.format(v))


    def _perform(self, dry=False):
        """
        Replace/Inject named variables into source files
        :param dry:
        :return:
        """
        if dry:
            vm = VarMgr()
            logger.debug('Apply following injects')
            for vn in self.vars:
                logger.debug('    {}  ==> {}'.format(vn, vm.get(vn)))
            logger.debug('to files:')
            for path in self.path:
                logger.debug('    {}'.format(path))
        else:
            for path in self.path:
                fname = self._get_edit(path)
                self._inject(fname)


    def _get_edit(self, p4name):
        """
        return an editable filename from p4name
        :param p4name:          p4 name
        :return:                local name in workspace
        """
        result = subprocess.check_output([self.p4, 'have', p4name])
        f = BIInject._patn_have.split(result)
        if f[1] is None:
            raise BoosterError('BIInject: fail to get local file for ' + p4name)
        result = subprocess.check_output([self.p4, 'edit', p4name])
        result = subprocess.check_output([self.p4, 'revert', '-k', p4name])
        return f[1].strip()


    def _inject(self, fname):
        """
        Replace all tags in file fname with the variables that have the same name with the tags.
        :param fname:       name of file to be injected
        :return:
        """
        with open(fname) as f:
            text = f.read()
        vm = VarMgr()
        new_text = text
        for vn in self.vars:
            vv = vm.get(vn)
            new_text = new_text.replace(vn, vv)
        if new_text != text:
            with open(fname, 'w') as f:
                f.write(new_text)


def Execute(root):
    if Debugger().skip('biinject', '----Skip: biinject'):
        return
    action = BIInject(root)
    action.run()


def Debug(root):
    if Debugger().skip('biinject', '----Skip: biinject'):
        return
    print('==============================')
    print('          Enter BIInject')
    print('==============================')
    action = BIInject(root)
    action.run(dry=True)


if __name__ == '__main__':
    from xml.etree import ElementTree as ET

    s = '''
    <group>
        <P4Changes label="head__CL12345__34521">
            <path>//SimbaTestTools/perftest/Trunk/script/...</path>
        </P4Changes>
        <BIInject path="//SimbaTestTools/perftest/Trunk/script/perfgen.py" >
            <path>//SimbaTestTools/perftest/Trunk/script/perfrun.py</path>
            <path>//SimbaTestTools/perftest/Trunk/script/default.yaml</path>
        </BIInject>
    </group>
    '''
    root = ET.fromstring(s)
    n1 = root.find('P4Changes')
    P4Changes.Execute(n1)
    for n in root.findall('BIInject'):
        Execute(n)
        Debug(n)
