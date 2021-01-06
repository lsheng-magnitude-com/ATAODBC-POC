#! /usr/bin/env python
# -*- encoding: utf8 -*-

from __future__ import print_function
import os
import re
import sys
import time
import os.path
import platform
import pdb


def Execute(root):
    Debug(root)
    use_pdb = re.match(r't(rue)?$', root.attrib.get('pdb', '').lower())
    dbg_freeze(root.text, use_pdb)

def Debug(root):
    fname = root.text
    print('==============================')
    print('     Freeze: waiting for {}'.format(os.path.abspath(fname)))
    print('==============================')














def dbg_freeze(fname, dbg=False):
    """
    Suspend the script execution until fname is found with at least one line text.
    If the first word of the file is 'exit', sys.exit() is called to terminate the script.

    To resume exec:
        echo > fname
    To terminate exec:
        echo exit > fname

    During suspend, the environment can be set by a script setenv.sh (setenv.bat)
    at the same folder of fname.

    :param fname:   name of file
    :return:
    """
    def _save_env(path, fname, win=False):
        try:
            with open(os.path.join(path, fname), 'w') as f:
                if win:
                    for k, v in os.environ.items():
                        f.write('set {}={}\n'.format(k, v))
                else:
                    for k, v in os.environ.items():
                        fmt = "export {}='{}'\n" if ' ' in v else 'export {]={}\n'
                        f.write(fmt.format(k, v))
        except Exception as e:
            print('save_env: {}'.format(e))

    isWin = platform.system() == 'Windows'
    retry = 5

    # save environment (shell to restore the current environment)
    path = os.path.dirname(fname)
    _save_env(path, 'setenv.sh', False)
    if isWin:
        _save_env(path, 'setenv.bat', True)

    # wait until fname exists and is not empty
    lastEx = None
    count = 0
    while True:
        try:
            st = os.stat(fname)
            if st.st_size != 0:
                break
        except Exception as e:
            emsg = str(e)
            if lastEx != emsg:
                lastEx = emsg
                print('stat: {}'.format(emsg))
                print('freez: waiting for {}'.format(fname))
                print('environment is saved at {}'.format(path))
            elif count < 25:    # keep it rolling for a while, otherwise you won't see updates from bamboo console
                print('freez: waiting for {}'.format(fname))
                count += 1
        time.sleep(retry)

    try:
        with open(fname, 'rt') as f:
            text = f.readline()
            # print('read text=[{}] len={}'.format(text, len(text)))
        os.remove(fname)
    except Exception as e:
        print('read/remove exception: {}'.format(e))
    if re.match(r'exit\b', text, re.IGNORECASE):
        print('resume and exit')
        sys.exit(1)
    if dbg:
        pdb.set_trace()



if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('fname', type=str)
    parser.add_argument('-d', '--pdb', action='store_true', help='trigger pdb')
    args = parser.parse_args()
    try:
        print('mytask start')
        for i in range(10):
            time.sleep(1)
            print('    heart beat {}'.format(i))
            dbg_freeze(args.fname, args.pdb)
            print('    continue to work ...')
    except Exception as e:
        print('Exception: {}'.format(e))
    print('The End.')

