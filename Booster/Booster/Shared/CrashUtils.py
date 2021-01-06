"""Utilities to deal with process crashes (getting core dumps, stack traces)
"""

__all__ = ['save_core_dump', 'find_and_save_core_dump', 'get_back_trace']

import ata.log
import os
import os.path
import platform
import re
import shutil
import glob
import subprocess

logger = ata.log.AtaLog(__name__)


class CrashUtilsException(Exception):
    def __init__(self, *args):
        super(CrashUtilsException, self).__init__(args)


def save_core_dump(core, output_dir, core_file_name):
    """
    Move core to the output directory and normalize to core.pid, or core_file_name if provided
        core            original core file name
        output_dir      location of the output
        core_file_name  new file name
    
    :return:            the result file name
    """

    old_core = os.path.normpath(core)
    core = os.path.normpath(os.path.join(output_dir, core_file_name))
    if old_core != core:
        logger.debug('move {} to {}'.format(old_core, core))
        shutil.move(old_core, core)
    return core


def _get_file_contents(file_name):
    """ quick helper to load content of a text file """
    try:
        with open(file_name) as f:
            return f.read().strip()
    except Exception as e:
        logger.warning('fail to read {}\n{}'.format(file_name, e))
        return ''


def _find_core_on_linux(pid, cwd):
    """
    Figure out core filename on linux

    Morden Linux distros typically use two files to define core
    file                                    sample          description
    /proc/sys/kernel/core_pattern           /tmp/core.%p    'core' on default new agents
    /proc/sys/kernel/core_uses_pid          0               1: append pid

    """
    pass
    pattern = _get_file_contents('/proc/sys/kernel/core_pattern')
    use_pid = _get_file_contents('/proc/sys/kernel/core_uses_pid')
    if not use_pid:
        use_pid = '0'
    
    m = re.match('(.*)(core.*)', pattern)
    
    prefix, suffix = '', pattern
    if m:
        prefix = m.group(1)
        suffix = m.group(2)
        
    core = None
    if (suffix == 'core' and use_pid != '0') or suffix == 'core.%p':
        core = '{}core.{}'.format(prefix, pid)
    elif '%' not in pattern:
        if use_pid == '0':
            core = pattern
        else:
            core = '{}.{}'.format(pattern, pid)
    else:
        logger.warning('Unsupported core_pattern: "{}"'.format(pattern))
    
    if core and '/' not in prefix:
        core = '{}/{}'.format(cwd, core)
    
    # fallback to old convention
    if not core or not os.path.exists(core):
        if not core:
            logger.warning('''Smart guessed core ({}) doesn't exist, try /tmp/core.{}'''.format(core, pid))
        core = '/tmp/core.{}'.format(pid)
    
    return core


def find_and_save_core_dump(pid, working_dir, output_dir, core_file_name=None, optional=False, delete=False):
    """
    Get the core file
    The core file has different name (pattern) and location, depending to platforms.
    This method get/check and rename to output_dir/core.pid
    Note: This should not be used when using ProcDump on windows, as it will not find the created dump

    :return:    the final core file name (there is one and only one core file)
                list of final core file names (more than one core file, happens on Windows)
                None (core is not available)
    """
    sys_platform = platform.system()
    cwd = working_dir
    core = None
    if sys_platform == 'Linux':
        core = _find_core_on_linux(pid, working_dir)
    elif sys_platform == 'Darwin':
        core = "/cores/core.{}".format(pid)
    elif sys_platform in ['SunOS', 'AIX', 'HP-UX']:
        core = "{}/core".format(cwd)
    elif sys_platform == 'Windows':
        # It is possible to have multiple dmp files on Windows
        #   * created by app itself
        #   * created by 3rd utilities e.g. procdump
        #
        core = glob.glob('{}/*.dmp'.format(cwd))
        if len(core) == 0:
            if not optional:
                logger.warning('core file does not exist at {}'.format(cwd))
            return None
        elif delete:
            for f in core:
                os.remove(f)
            return None
        else:
            cores = []
            for f in core:      # move to output dir, insert/append pid to each filename
                ext = os.path.splitext(os.path.basename(f))
                cores.append(save_core_dump(f, output_dir, '{}_pid{}{}'.format(ext[0], pid, ext[1])))
            return cores if len(cores) > 1 else cores[0]
    if core:
        if os.path.isfile(core):
            if delete:
                os.remove(core)
                return None
            # move core to the output directory and normalize to core.pid, or core_file_name if provided
            newName = core_file_name or 'core.{}'.format(pid)
            core = save_core_dump(core, output_dir, newName)
        else:
            if not optional:
                logger.warning('core file does not exist: {}'.format(core))
            core = None
    return core


def get_back_trace(app, core):
    def find_app(app):
        """ Return the full path of an app by searching $PATH
        """
        binpath = os.environ['PATH']
        for p in binpath.split(':'):
            fp = os.path.join(p, app)
            if os.path.exists(fp):
                return fp
        raise CrashUtilsException(app + ' is not in the search path')
    
    def run_cmd(args, input=None):
        """Get the output of a command, with optional input file.

            args            args to subprocess
            fstdin          input as cmd stdin

        Returns:
            output of the command
        """
        if input is None:
            dat = subprocess.check_output(args, stdin=None, stderr=subprocess.STDOUT)
        else:
            p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            dat = p.communicate(input)[0]
        return dat
    
    class GetBacktrace(object):
        """
        Get backtrace from core on different platforms
        """

        def __init__(self, app, core):
            """ Create the object, save the binary and core
            """
            self.app = app
            self.core = core

        def run(self):
            """ Dispatch by platform
            """
            pfn = platform.system().lower()
            if pfn == 'linux':
                return run_cmd([find_app('gdb'),
                                '--batch',
                                '--quiet',
                                '-ex',
                                'thread apply all bt',
                                '-ex',
                                'quit',
                                self.app,
                                self.core])
            elif pfn == 'hp-ux':
                return run_cmd([find_app('gdb'),
                                '-quiet',
                                self.app,
                                self.core],
                               'thread apply all bt\nquit\n')
            elif pfn == 'darwin':
                ''' old version of lldb (e.g. 340.x) doesn't support access through pipe
                    the capability starts from xcode 7.2 in osx 10.11
                '''
                msg = 'can not get backtrace from old lldb'
                try:
                    r_main = int(platform.release().split('.')[0])
                    if r_main < 15:     # i.e. osx 10.11
                        return msg
                except:
                    return msg
                return run_cmd([find_app('lldb'), '-b', '-o', 'bt all', '-c', self.core, self.app])
            elif pfn == 'aix':
                return self._run_dbx('thread', r'[> ]\s*(\$t\d+)\s')
            elif pfn == 'sunos':
                return self._run_dbx('threads', r'(?:.>)?\s+(t@\d+)\s')

        def _run_dbx(self, cmd, pattern):
            # extract thread from output, sample
            #
            # aix:
            # (dbx) thread
            # thread  state-k     wchan    state-u    k-tid   mode held scope function
            # $t1     run                  blocked  41156697     u   no   sys  _event_sleep
            # $t2     run                  running  23068859     u   no   sys  _p_nsleep
            #>$t3     run                  running  42402021     k   no   sys  CrashThread::run()
            #
            # sunos:
            #(dbx) threads
            #      t@1  a  l@1   ?()   LWP suspended in  __lwp_wait()
            #      t@2  a  l@2   stub()   LWP suspended in  __nanosleep()
            #o>    t@3  a  l@3   stub()   signal SIGSEGV in  run()
            where_options = ''
            pfn = platform.system().lower()
            if pfn == 'sunos':
                # -l    include library name with function name
                # -h    include hidden frames
                # -v    verbose trace back (args and line info)
                where_options = '-l -h -v'
            p_th = re.compile(pattern)
            dbx = find_app('dbx')
            s = run_cmd([dbx, self.app, self.core], cmd + '\n')
            cmd = []
            for n in s.split('\n'):
                m = p_th.match(n)
                if m:
                    cmd.append('where {} {}'.format(where_options, m.group(1)))
            # send a list of where $thread command to dbx again
            return run_cmd([dbx, self.app, self.core], '\n'.join(cmd) + '\n')
    
    return GetBacktrace(app, core).run()
