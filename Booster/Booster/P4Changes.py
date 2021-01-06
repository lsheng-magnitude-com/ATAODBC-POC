from __future__ import print_function
import os
import re
import subprocess
import ata.log
from Booster.Action import Action
from Booster.Var import VarMgr
from Booster.Debug import Debug as Debugger

logger = ata.log.AtaLog(__name__)
_unit_test = False

class P4Changes(Action):
    _patn_label = re.compile(r'__(?:CL)?')
    _patn_pound = re.compile(r'head$|\d+$', re.IGNORECASE)
    _patn_changes = re.compile(r'Change (\d+) ')

    def __init__(self, root):
        """
        The node should have following attributes
            path            P4 path to the target
            label           format: label(__CLnnn)*, default is head
            var             name of variable that stores the result
        :param root:
        """
        super(P4Changes, self).__init__(root, 'P4Changes')
        self.path = set()
        path = root.attrib.get('path')
        if path is not None:
            self.path.add(path)
        for path in root.findall('path'):
            self.path.add(path.text)
        if not self.path:
            raise LookupError('path (attribute or children) expected')
        self.var = root.attrib.get('var', '__BUILD_INFO__')
        cls = P4Changes._patn_label.split(root.attrib.get('label', 'head'))
        self.label, self.cls = cls[0], cls[1:]
        self.p4 = os.environ.get('BAMBOO_CAPABILITY_SYSTEM_P4EXECUTABLE','p4')


    def _perform(self, dry=False):
        """
        Find the latest CL of the label, append unshelve CLs (self.cls if applicable),
        then store in the variable named by self.var
        :param dry:
        :return:
        """
        label = '#' if P4Changes._patn_pound.match(self.label) else '@'
        label += self.label
        changes = self.label
        for path in self.path:
            cmd = [self.p4, 'changes', '-m1', path + label]
            if dry:
                logger.debug(' '.join(cmd))
            else:
                result = subprocess.check_output(cmd)
                m = P4Changes._patn_changes.match(result)
                if not m:
                    errmsg = 'command:\n{}\nresult:\n{}'.format(' '.join(cmd), result)
                    raise RuntimeError('P4Changes: fail to get label changelist\n' + errmsg)
                else:
                    if changes != self.label:
                        changes += '\n'
                    changes += ' {} CL{}'.format(path, m.group(1))
                    if self.cls:
                        changes += '  unshelve: ' + ','.join(self.cls)
        if _unit_test:
            print('changes={}'.format(changes))
        elif not dry:
            vm = VarMgr()
            # escape \n for two reasons
            # this is saved in environment variables
            # this is going to be inject into source code as string
            changes = changes.replace('\n', '\\n')
            vm.add(self.var, changes, '_P4Changes')


    

def Execute(root):
    if Debugger().skip('p4changes', '----Skip: p4changes'):
        return
    action = P4Changes(root)
    action.run()


def Debug(root):
    if Debugger().skip('p4changes', '----Skip: p4changes'):
        return
    print('==============================')
    print('          Enter P4Changes')
    print('==============================')
    action = P4Changes(root)
    action.run(dry=True)


if __name__ == '__main__':
    from xml.etree import ElementTree as ET
    _unit_test = True
    ss = [
        '''
        <group>
            <P4Changes label="head__CL12345__34521">
                <path>//SimbaTestTools/perftest/Trunk/script/...</path>
            </P4Changes>
        </group>
        ''',
        '''
        <group>
            <P4Changes label="perftest-0.9.12__CL12345__34521">
                <path>//SimbaTestTools/perftest/Trunk/script/...</path>
            </P4Changes>
        </group>
        ''',
        '''
        <group>
            <P4Changes label="perftest-0.9.12">
                <!-- multiple paths -->
                <path>//SimbaTestTools/perftest/Trunk/script/...</path>
                <path>//SimbaTestTools/perftest/Trunk/jdbc/...</path>
            </P4Changes>
        </group>
        '''
    ]
    for s in ss:
        root = ET.fromstring(s)
        node = root.find('P4Changes')
        Execute(node)

