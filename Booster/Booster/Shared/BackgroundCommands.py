# -*- encoding: utf8 -*-

from __future__ import print_function

"""
Launch processes at background, which are stored in a manager identified
by unique names.

Processes can be removed/killed by signals at anytime before they terminate.

If cores are generated, back-traces are decoded and cores are saved in
specified directory.

On Windows platform, procdump is supported to monitor/generate mini-dump.

When the script terminates, all launched processes are terminated.
"""

import time
import threading
import collections
import subprocess
import signal
import sys
import os
import os.path
import atexit
import re
import gzip
import shutil
import Booster.Shared.CrashUtils as CU
import ata.log

_py_version = sys.version_info.major

_logger = ata.log.AtaLog(__name__)
_is_win = os.name == 'nt'
_is_posix = not _is_win
#
# implement note:
# it is hard to explain but it is true
# that procdump64 is invoked and deleted if we invoke procdump for 64-bit app (at least on w2012r2)
# in addition procdump64 rejects to server 32-bit app
# so we need to choose proper version of procdump according to the bitness of app
#
_re_procdump = re.compile(r'\bprocdump\b(?![\\/])')
_re_procdump64 = re.compile(r'\bprocdump64\b(?![\\/])')

_win32api = None
if _is_win:
    try:
        import win32api
        import win32con
        import win32process
        _win32api = True
    except ImportError:
        _logger.info('win32api is not available')


__all__ = ['start', 'stop']


def start(name, command, cwd=None, output=None, env=None, shell=False, **kwargs):
    """Start a process in the background

    name:       A unique string which identifies the started process.
                Pass this into Stop() in order to kill the background process
    command:    The command to run.
                Can either be a string, in which case it should contain a command-
                line, including arguments, or a sequence, the first element the path
                to the executable, subsequent parameters individual arguments.

                No shell processing is done in either case.
    output:     Name of an output file which gets stderr/stdout
    env:        If specified, a dict containing the environment to use. Otherwise,
                the current process' environment is used.
    shell:      launch with shell if True

    extra options can be set using keyword arguments, see details in AppProcess below.

    """
    kw = {}
    if cwd:
        kw['cwd'] = cwd
    if output:
        kw['stdout'] = os.path.abspath(output)
    if env:
        kw['env'] = env
    if shell:
        kw['shell'] = shell
    for k, v in kwargs.items():
        if k not in kw:
            kw[k] = v
    if type(command) == str:
        command = command.split()
    AppProcess(name, command, **kw).start()


def stop(name, **kwarg):
    """ Stop a process previous started with Start(name, ...)

    kwargs.sig          signal sent to the application (non-Windows), default is None
    kwargs.sync         wait to stop completely, default True

    """
    AppMgr.instance().remove(name, **kwarg)


def exists_and_is_executable(path):
    """ return absolute path if file exists and is executable, raise ValueError else """
    if not os.path.exists(path):
        raise ValueError(path + ' does not exist')
    if not os.path.isfile(path):
        raise ValueError(path + ' is not a file')
    if not os.access(path, os.X_OK):
        raise ValueError(path + ' is not executable')
    return os.path.abspath(path)


def get_executable_bin(cmd, cwd=None):
    """
    Find the absolute path of the application binary, and validate it exists and executable
    :param cmd:         pathname of command
    :param cwd:         working directory
    :return:            absolute path that is validated existing and executable
    """
    if os.path.isabs(cmd):
        return exists_and_is_executable(cmd)

    if cwd is None:
        cwd = os.getcwd()

    # explicitly request to search from ./ only
    if cmd[:2] == '.' + os.path.sep:
        return exists_and_is_executable(os.path.join(cwd, cmd))

    # which = 'where' if _is_win else 'which'
    # if _py_version > 2:
    #     result = subprocess.run([which, cmd], capture_output=True, encoding='utf8')
    #     if result.returncode != 0:
    #         raise ValueError(result.stderr)
    #     return result.stdout
    # else:
    #     try:
    #         result = subprocess.check_output([which, cmd])
    #     except subprocess.CalledProcessError:
    #         raise ValueError(cmd + ' not found')
    #     return result.rstrip()
    search_path = os.environ.get('PATH').split(os.pathsep)
    if _is_win:   # Windows search command starting from . before %PATH%
        search_path.insert(0, cwd)
    for path in search_path:
        try:
            return exists_and_is_executable(os.path.join(path, cmd))
        except ValueError as e:
            if 'not executable' in str(e):
                raise
    raise ValueError('can not find executable file ' + cmd)


def get_exception(name):
    """ Return a queued exception from the named process.
        None if the process doesn't exist or no exception is queued.
    """
    app = AppMgr.instance().get(name)
    return app.get_exception() if app else None


conLock = threading.Lock()


def log(msg):
    """ log information with thread-sync """
    with conLock:
        _logger.info(msg)


class AppMgr(object):
    """ Singleton application manager """

    __mgr = None

    class AsyncJoiner(threading.Thread):
        """
        By default, remove a process (and its guardian thread) is synchronous, i.e.
        wait the process and the thread terminate.
        By setting sync=False in remove(), this operation is performed in a separated thread
        and remove() returns immediately.
        """

        def __init__(self):
            super(AppMgr.AsyncJoiner, self).__init__()
            self.cv = threading.Condition()
            self.queue = []
            self.daemon = True

        def run(self):
            while True:
                with self.cv:
                    while len(self.queue) > 0:
                        t = self.queue.pop(0)
                        if t is None:
                            return
                        else:
                            app_name = t.name
                            t.join()
                            log('app.{} is joined async'.format(app_name))
                    self.cv.wait()

        def append(self, t):
            with self.cv:
                self.queue.append(t)
                self.cv.notify_all()

    def __init__(self):
        if AppMgr.__mgr is None:
            self.lock = threading.Lock()
            self.apps = collections.OrderedDict()
            self.bg_joiner = None
            AppMgr.__mgr = self
        else:
            raise RuntimeError('AppMgr is singleton')

    @classmethod
    def instance(cls):
        if cls.__mgr is None:
            cls()
        return cls.__mgr

    @classmethod
    def clean(cls):
        _mgr = cls.__mgr
        if _mgr:
            with _mgr.lock:
                names = _mgr.apps.keys()
            if len(names) > 0:
                log('Remove following process that still run atexit')
                for n in names:
                    log('    ' + n)
                _mgr.remove(msg='AppMgr clean from atexit')

    def add(self, app):
        """ Add an application in the manager, the name must be unique
        """
        with self.lock:
            name = app.name
            if name in self.apps:
                raise KeyError('duplicate app name: ' + name)
            self.apps[name] = app

    def get(self, name):
        """ Get an application by its name """
        return self.apps.get(name)

    def remove(self, name=None, **kwargs):
        """ Remove (and stop) the application of name

        :param name:        name of application, all if not specified

        optional args:
        sig                 signal sent to stop the application,
        sync                join sync (default) or async
        rethrow             when true, throw the 1st exception if exists
        """
        if name is None:
            # remove all apps in the order they are added
            new_kwargs = dict(**kwargs)
            new_kwargs['sync'] = True
            with self.lock:
                names = list(self.apps.keys())
            if len(names) > 0 and 'msg' in kwargs:
                log('Remove all apps: {}'.format(kwargs['msg']))
            if len(names) > 1:
                new_kwargs['rethrow'] = False
            for n in names:
                self.remove(n, **new_kwargs)
            with self.lock:
                if self.bg_joiner:
                    self.bg_joiner.append(None)
                    self.bg_joiner.join()
                    self.bg_joiner = None
            return

        with self.lock:
            if name not in self.apps:
                return
            app = self.apps[name]
            del self.apps[name]

        if app.is_alive():
            app.stop(**kwargs)
        else:
            log('App.{} terminated already'.format(name))

        sync = kwargs.get('sync', True)
        if sync:
            app.join()
            log('app.{} joined'.format(name))
        else:
            with self.lock:
                if self.bg_joiner is None:
                    self.bg_joiner = AppMgr.AsyncJoiner()
                    self.bg_joiner.daemon = True
                    self.bg_joiner.start()
                log('app.{} join later'.format(name))
                self.bg_joiner.append(app)

        if kwargs.get('rethrow'):
            e = app.get_exception()
            if e:
                raise e

    def keys(self):
        with self.lock:
            return self.apps.keys()


atexit.register(AppMgr.clean)


class App(threading.Thread):
    """
    A named application/thread that is managed by AppMgr
    """

    def __init__(self, name, **kwargs):
        """
        save and set configuration, register into appmgr

        :param name:        name of app, should be unique
        :param kwargs:      indent      indent for dumping
        """
        super(App, self).__init__(group=None)
        _mgr = AppMgr.instance()
        if _mgr.get(name) is not None:
            raise KeyError('duplicated app name: ' + name)
        self.name = name
        self.indent = ' ' * kwargs.get('indent', 0)

        self.lock = threading.Lock()
        self.exit = False
        self.sig = None
        self.exceptions = []  # queued exception(s)
        self.daemon = True
        _mgr.add(self)

    def run(self):
        self.dump('start --------')
        try:
            self._run()
        except Exception as e:
            self._save_exception(e)
        finally:
            self._clean()
            self.dump('-------- end')

    def _run(self):
        """
        thread body, override by sub-class
        """
        pass

    def _clean(self):
        """ override clean actions """
        pass

    def stop(self, **kwarg):
        """ stop this thread

            This method just notifies thread to stop,
            _stop() actually does the work.

        :param kwarg        params passed to _stop
        """
        with self.lock:
            sig = kwarg.get('sig')
            timeout = kwarg.get('timeout')
            extra_info = ''
            if sig:
                extra_info += ' signal={}'.format(sig)
            if timeout:
                extra_info += ' timeout={}'.format(timeout)
            self.dump('is required to stop{}'.format(extra_info))
            self.exit = True
            self._stop(**kwarg)

    def _stop(self, **kwarg):
        pass

    def _stopped(self):
        """ check if this thread is required to stop """
        with self.lock:
            return self.exit

    def get_exception(self):
        """ return the first exception in the queue """
        with self.lock:
            return self.exceptions.pop(0) if len(self.exceptions) > 0 else None

    def _save_exception(self, e):
        with self.lock:
            self.dump('exception: {}'.format(e))
            self.exceptions.append(e)

    def dump(self, msg):
        log('{}App.{} '.format(self.indent, self.name) + msg)


class AppDummy(App):
    """
    A dummy thread that is used for debugging AppMgr, such as start/stop/kill and their sequence, etc
    """

    def __init__(self, name, **kwargs):
        super(AppDummy, self).__init__(name, **kwargs)
        self.loop = kwargs.get('loop', 0)
        self.click = kwargs.get('click', 1)
        if self.click < 0:
            self.click = 1

    def _run(self):
        loop = self.loop
        while not self._stopped() and loop > 0:
            time.sleep(self.click)
            self.dump('test loop: {}'.format(loop))
            loop -= 1


class AppProcess(App):
    """
    Guardian thread of a subprocess that takes care of interaction with the subprocess
    e.g. stdout, terminate, sync, core management, and .etc
    """

    # subprocess has a bug (python2.7 Windows only?)
    # that causes fail to launch a process (although subprocess succeeds)
    # with following message on stdout:
    #  The process cannot access the file because it is being used
    #  by another process.
    ap_lock = threading.Lock()

    def __init__(self, name, cmd=None, **kwargs):
        """
        save and set configuration, register into appmgr

        :param name:        name of app, should be unique
        :param cmd:         list to launch subprocess
                            1st is path-to-binary, followed by command options
        :param kwargs:
                cwd                 working folder for the process
                env                 environment to be used for the new process
                shell               if launched under a shell
                stdout              file name to redirect stdout
                stderr              file name to redirect stderr
                                    if not specified, stderr is bound with stdout
                core_folder         folder where core file(s) are stored

             (Windows only)
                procdump            procdump pathname, abspath is recommended unless in PATH
                procdump-option     option for procdump to generate mini-dump, default is -ma
                procdump-x-option   option for procdump to launch app (before -x option), default is -e -ma

        """
        super(AppProcess, self).__init__(name, **kwargs)
        if type(cmd) == str:
            cmd = cmd.split()
        self.cmd = cmd
        self.env = kwargs.get('env')
        self.cwd = kwargs.get('cwd')
        self.shell = kwargs.get('shell', False)
        self.stdout_name = kwargs.get('stdout', self.name + '_stdout.txt')
        self.stderr_name = kwargs.get('stderr')
        bool_str = kwargs.get('log-stdout', 'True')
        self.log_stdout = bool_str.lower() != 'false'
        self.core_folder = kwargs.get('core_folder')
        self.keep_cores = kwargs.get('keep-cores', 'false').lower() == 'true'
        try:
            self.delay_launch = int(kwargs.get('delay-to-launch', 0))
        except ValueError as e:
            self.dump('invalid delay: {}'.format(e))
            self.delay_launch = 0
        if self.core_folder:
            if not os.path.exists(self.core_folder):
                os.makedirs(self.core_folder)
        else:
            self.core_folder = os.getcwd()
        self.core_folder = os.path.abspath(self.core_folder)

        # Windows only
        self.procdump = kwargs.get('procdump') if _is_win else None
        if self.procdump:
            # choose the proper version of procdump according to plan bitness
            bitness = int(os.environ.get('BOOSTER_VAR_BITNESS', 64))
            if bitness == 32:
                self.procdump = _re_procdump64.sub('procdump', self.procdump)
            if bitness == 64:
                self.procdump = _re_procdump.sub('procdump64', self.procdump)
            self.procdump_x_option = kwargs.get('procdump-x-option', '-e -ma').split()  # used to monitor app
            self.procdump_option = kwargs.get('procdump-option', '-ma').split()  # used to generate mini-dump
            # procdump pops up dialog for accecpting EULA for the first run, let's suppress it
            accept_eula = '-accepteula'
            if accept_eula not in self.procdump_x_option:
                self.procdump_x_option.insert(0, accept_eula)
            if accept_eula not in self.procdump_option:
                self.procdump_option.insert(0, accept_eula)
            # compose a unique folder name for procdump to generate mini-dump
            # because the dump file name is not customizable if the app crashes.
            self.procdump_wd = os.path.join(self.core_folder, '__procdump__{}'.format(self.name))

        self.proc = None  # subprocess.Popen
        self.pid = None  # pid of target app (could be different if app is under control of procdump)
        self.stdout = None  # redirected stdout
        self.stderr = None  # redirected stderr
        self.processHandle = None           # used for getting return code

    def _run(self):
        """
        thread body
        """
        try:
            if self.delay_launch > 0:
                time.sleep(self.delay_launch)
        except:
            pass
        self._is_valid_cmd()

        self.stdout = self._redirect(self.stdout_name)
        self.stderr = self._redirect(self.stderr_name)

        cmd = []
        # compose procdump session (on Windows only)
        #   procdump [x_option] -x dmp_folder app_binary [app_options]
        if self.procdump:
            os.makedirs(self.procdump_wd)
            cmd.append(self.procdump)
            cmd.extend(self.procdump_x_option)
            cmd.extend(['-x', self.procdump_wd])
        cmd.extend(self.cmd)

        try:
            with AppProcess.ap_lock:
                kw = {}
                if self.env is not None:
                    kw['env'] = self.env
                if self.cwd is not None:
                    kw['cwd'] = self.cwd

                kw['stdout'] = subprocess.PIPE if self.log_stdout or self.procdump else self.stdout
                # convention: if no separated stderr required explicitly, bind it with stdout
                kw['stderr'] = self.stderr if self.stderr else subprocess.STDOUT

                if self.shell is not None:
                    kw['shell'] = self.shell
                if _py_version > 2:
                    kw['encoding'] = 'utf8'
                if _is_win:
                    # python win32 implementation requires to set CREATE_NEW_PROCESS_GROUP
                    # to send signals to sub-process
                    # win32 supports only CTRL_BREAK_EVENT and CTRL_C_EVENT, if the sub-process
                    # is not created in a new process group, signals are still sent, but both
                    # child and parent (this script) get signals (and killed if not captured)
                    si = subprocess.STARTUPINFO()
                    si.dwFlags = subprocess.STARTF_USESTDHANDLES
                    kw['startupinfo'] = si
                    kw['creationflags'] = subprocess.CREATE_NEW_PROCESS_GROUP
                self.dump('actual launch as:\n{}'.format(' '.join(cmd)))
                self.dump('cwd={}'.format(self.cwd if self.cwd else os.getcwd()))
                self.proc = subprocess.Popen(cmd, **kw)

            if self.procdump:
                self.dump('procdump={}'.format(self.proc.pid))
                self.pid = self._procdump_child_pid(self.proc.stdout)
                self.dump('procdump={} pid={}'.format(self.proc.pid, self.pid))
            else:
                self.pid = self.proc.pid
                self.dump('pid={}'.format(self.pid))

            if _is_win and _win32api:
                try:
                    self.processHandle = win32api.OpenProcess(
                        win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, self.pid)
                except Exception as e:
                    _logger.info('Fail to get process (pid={}) handle: {}'.format(self.pid, e))

            if self.proc.stdout:  # need to read from subprocess
                while not self._stopped():
                    s = self.proc.stdout.readline()
                    if s is None or len(s) == 0:  # EOF
                        self.dump('pipe closed')
                        break
                    else:
                        if type(s) != str:
                            s = s.decode('utf8')
                        if self.stdout:  # need to save stdout to a file
                            self.stdout.write(s)
                        if self.log_stdout:
                            self.dump(s.rstrip())

        except Exception as e:
            self.dump('exception in running: {}'.format(e))
            try:
                self._stop(sig='SIGABRT')
            except Exception as e_stop:
                self.dump('exception at stop: {}'.format(e_stop))
            raise e
        finally:
            if self.proc:
                exit_code = self.proc.poll()
                if exit_code is None and self._stopped():
                    self.dump('is not terminated yet, kill it')
                    self.proc.kill()
                self.dump('waiting ...')
                exit_code = self.proc.wait()
                if self.procdump and self.processHandle:
                    # exit_code is actually the return code of procdump, we need to get return code
                    # of the target process with the help of pywin32 extension
                    try:
                        exit_code = win32process.GetExitCodeProcess(self.processHandle)
                    except Exception as e:
                        _logger.info('Fail to get return code of process {} through win32api: {}'.format(self.pid, e))
                        exit_code = None
                if self.processHandle:
                    try:
                        win32api.CloseHandle(self.processHandle)
                    except: # who cares?
                        pass
                    finally:
                        self.touchstoneProcessHandle = None
                if _is_posix and exit_code < 0:
                    self.dump('==== caught signal {}'.format(-exit_code))
                else:
                    self.dump('==== exit={}'.format(exit_code))
                optional = exit_code == 0
                delete = exit_code == 0 and not self.keep_cores
                self._get_core_and_back_trace(optional, delete)

    def _is_valid_cmd(self):
        """ validate the application binary (self.cmd[0]) exists and is executable
            return True if it is, otherwise raise with reason
        """
        try:
            cmd = self.cmd[0]
        except (IndexError, TypeError) as e:
            raise ValueError('app binary is not defined')

        return get_executable_bin(cmd, self.cwd)

    @staticmethod
    def _redirect(file_name):
        """ open a file for redirection """
        if file_name is None:
            return None
        try:
            return open(file_name, 'w')
        except IOError as e:
            raise RuntimeError('fail to open redirect file: {}'.format(file_name))

    @staticmethod
    def _get_signal_value(name):
        """ translate (and validate) signal name to value """
        if (name[:3] == 'SIG' and name[:4] != 'SIG_') or (_is_win and name[-6:] == '_EVENT'):
            try:
                return getattr(signal, name)
            except AttributeError as e:
                raise e
        else:
            raise AttributeError('invalid signal name ' + name)

    def _clean(self):
        """ remove all allocated resources """
        if self.stdout:
            self.stdout.close()
            self.stdout = None
        if self.stderr:
            self.stderr.close()
            self.stderr = None
        if self.procdump and self.procdump_wd and os.path.exists(self.procdump_wd):
            try:
                shutil.rmtree(self.procdump_wd, ignore_errors=True)
            except IOError as e:
                self.dump('rmtree({}): {}'.format(self.procdump_wd, e))

    def _procdump_child_pid(self, stdout_handle):
        """ Get pid of the application that is launched by procdump

        We get pid from procdump output, which has following patterns
        in the first few lines
          Process:    exec_name (pid)
          ...
          Press Ctrl-C to end monitoring without terminating the process.

        :param stdout_handle         a file handle of stdout of the process
        :return             pid detected

        """
        pattern_pid = re.compile(r'^Process:.*\((\d+)\)\s*$')
        str_procdump_end = 'Press Ctrl-C to end'
        pid = None
        while True:
            s = stdout_handle.readline()
            if s is None or len(s) == 0:
                self.dump('==== unexpected EOF')
                break
            if s[-1] == '\n':
                s = s.rstrip()
            self.dump(s)
            if pid is None:
                m = pattern_pid.match(s)
                if m:
                    pid = int(m.group(1))
            elif str_procdump_end in s:
                break  # end of procdump head, following will be actual app output
        if pid is None:
            # we don't know reasons, but I did observer this happened
            # and I don't know solutions
            self.dump('==== fail to get pid !!!')
            raise RuntimeError('fail to get pid from procdump')
        return pid

    def _procdump_dump(self):
        """ let procdump generate mini-dump """
        cmd = [self.procdump]
        cmd.extend(self.procdump_option)  # customized dump option
        cmd.extend(['{}'.format(self.pid), 'core.{}'.format(self.name)])
        try:
            self.dump(' '.join(cmd))
            subprocess.call(cmd, cwd=self.procdump_wd)
            # note: procdump returns 2 on success
        except Exception as e:
            self.dump('==== fail to get mini-dump: {}'.format(self.name, e))

    def _get_core_and_back_trace(self, optional=False, delete=False):
        """
        Get the core file(s) (and gzip it/them) and backtrace(s)
        """
        name = self.name
        pid = self.pid
        if self.procdump:
            wd = self.procdump_wd
        else:
            wd = self.cwd or os.getcwd()

        if not optional:
            self.dump('core+bt o={}'.format(self.core_folder))
        core_file_name = 'core.{}'.format(name or pid)
        # return one of: None, core-name, list-of-core-names
        core_file = CU.find_and_save_core_dump(pid, wd, self.core_folder, core_file_name, optional, delete)

        if not core_file:
            return
        if type(core_file) != list:
            cores = [core_file]
        else:
            cores = core_file

        msg = ''
        for core_f in cores:
            msg += "Core-dump: {}\n".format(core_f)
            if _is_posix:
                try:
                    msg += CU.get_back_trace(self.cmd[0], core_f)
                except Exception as e:
                    msg += 'exception at getting back trace: ' + str(e)
            # compress it
            try:
                with open(core_f, 'rb') as f_in, gzip.open(core_f + '.gz', 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
                if os.path.exists(core_f + '.gz'):
                    os.remove(core_f)
            except IOError as e:
                msg += '==== fail to compress: {}'.format(e)
        if msg:
            # add indent and prefix for every line
            for msg_line in msg.split('\n'):
                self.dump(msg_line)

    def _stop(self, **kwarg):
        """ actually stop the subprocess:
            step 1:     send a signal to let the process terminate gracefully
            step 2:     check if it behaves gracefully, i.e. terminates by itself
            step 3:     terminate it by force after timeout

        :param kwarg:
            sig         the signal that notifies the process, by default
                        it is SIGTERM on posix and CTRL_BREAK_EVENT on windows
            timeout     seconds after sending the signal that takes action of forced termination
        """
        if self.proc and self.proc.poll() is None:  # the process is still alive, kill it
            sig_name = kwarg.get('sig')
            sig = None
            if sig_name is not None:
                try:
                    sig = self._get_signal_value(sig_name)
                except AttributeError as e:
                    self.dump('stop with signal {}: {}'.format(sig_name, e))

            default_timeout = 5
            timeout = kwarg.get('timeout', default_timeout)
            try:
                timeout = int(timeout)
            except ValueError:
                self.dump('stop with timeout {}: bad value, use {} seconds instead'.format(
                    timeout, default_timeout))
                timeout = default_timeout

            if self.procdump and sig_name is not None:
                # mini-dump is expected, it must be generated while procdump is alive
                self._procdump_dump()

            if not sig_name:
                sig = self._default_signal()
                sig_name = self._signal_name(None)

            # Windows supports only these signals
            if _is_win and sig not in (signal.CTRL_C_EVENT, signal.CTRL_BREAK_EVENT):
                sig = None

            if sig is not None:
                try:
                    self.dump('send_signal: {} {}'.format(sig_name, sig))
                    self.proc.send_signal(sig)
                except Exception as e:
                    self.dump('send_signal exception: {}'.format(e))
            else:
                timeout = 0

            if not self._is_terminated(timeout):
                self.dump('''doesn't terminate gracefully, force to terminate it ....''')
                if _is_win:
                    self.proc.terminate()
                else:
                    self.proc.kill()

    def _is_terminated(self, timeout=1):
        """ check if the proc terminates up to timeout seconds """
        if timeout <= 0 and self.proc and self.proc.poll() is not None:
            return True
        for i in range(timeout):
            if self.proc and self.proc.poll() is not None:
                return True
            time.sleep(1)
        return False

    @staticmethod
    def _default_signal():
        # if no signal is explicitly specified to terminate a process,
        # default signal is chosen, which is platform dependent
        # note:
        #     CTRL_C_EVENT seems to be more common on Windows, however, it might be
        #     a bug of python implementation that the target process can't
        #     receive it in unit test (probably because CTRL_C_EVENT value is zero)
        return signal.CTRL_BREAK_EVENT if _is_win else signal.SIGTERM

    @staticmethod
    def _signal_name(name):
        """ give a name, return a valid signal name or None """
        if name is None:
            return 'CTRL_BREAK_EVENT' if _is_win else 'SIGTERM'
        else:
            try:
                AppProcess._get_signal_value(name)
                return name
            except AttributeError:
                return None


if __name__ == '__main__':
    import platform
    import xml.etree.ElementTree as ET
    import os

    # where to load test bin
    bin = os.environ['BIN']
    if bin is None:
        bin = os.environ['HOME'] + '/bin'

    def run_app(app):
        """ run an application that can be customized by
            child tags <param>          list of command-line arguments
            attributes of app tag       options of subprocess and/or background command object
        """
        name = app.get('name', 'app')
        app_bin = app.text
        if '{' in app_bin:
            app_bin = app_bin.format(BIN=bin)
        args = [app_bin]
        for p in app.findall('param'):
            args.append(p.text)
        kwarg = {}
        for k in 'indent core_folder stdout procdump shell'.split():
            if k == 'procdump' and not _is_win:
                continue
            v = app.get(k)
            if v is not None:
                if k == 'indent':
                    kwarg[k] = int(v)
                elif k == 'shell':
                    kwarg[k] = v == 'True'
                else:
                    kwarg[k] = v
        start(name, args, **kwarg)
        return name

    def test_simple():
        """ test: simple/dummy applications, only their daemons run """
        for app in test.findall('app'):
            kw = {}
            if app.get('loop') is not None:
                kw['loop'] = int(app.get('loop'))
            if app.get('click') is not None:
                kw['click'] = float(app.get('click'))
            if app.get('indent') is not None:
                kw['indent'] = int(app.get('indent'))
            AppDummy(app.get('name'), **kw)

    def test_subp():
        """ test: run real applications, their life times are different, some of them may crash """
        for app in test.findall('app'):
            skip_os = app.get('skip_os')
            if skip_os is not None and platform.system().lower() == skip_os.lower():
                continue
            run_app(app)

    def test_term(test):
        """ test: stop an application """
        app = test.find('app')
        log('==== run an application at background')
        name = run_app(app)
        log('==== let it run for a while ....')
        time.sleep(int(test.get('sleep', 1)))
        log('==== going to stop it ...')
        stop(name, sig=test.get('sig'), timeout=int(test.get('timeout')))
        log('==== test_term done')

    mgr = AppMgr.instance()

    args = sys.argv[1:]
    tree = ET.parse(args[0])
    root = tree.getroot()
    for test in root.findall('test'):
        test_name = test.get('name')
        if test_name == 'sigterm':
            test_term(test)
        elif test_name == 'sp':
            test_subp()
        else:
            test_simple()

    main = root.find('main')
    if main:
        for step in main:
            msg = step.get('msg')
            if msg:
                log(msg)
            if step.tag == 'sleep':
                time.sleep(int(step.text))
            elif step.tag == 'abort':
                sig = step.get('signal')
                sync = step.get('sync', False)
                if sync:
                    sync = sync == 'True'
                app_name = step.get('name', 'king')
                stop(app_name, sig=sig, sync=sync)
            elif step.tag == 'remove':
                mgr.remove()
        log('==== end of unit test')

    '''
    <unit-test>
    
      <test>
        <desc>dummy applications, no real process is launched, but the framework is tested</desc>
        <app name='ace' loop='10' />
        <app name='king' loop='5' click='3.2' indent='30' />
        <app name='queen' loop='2' click='2.4' indent='60' />
      </test>
      
      <test name="sp">
        <desc>run several applications at background, they may
            terminates normally
            killed before termination
            crashes
        </desc>
        
        <app name='ace'
        >{BIN}/capp
            <desc>simply stop</desc>
            <param>10</param>
            <param>ace.txt</param>
        </app>
        
        <app name='king' indent='30' core_filder='o' stdout='king.stdout' procdump='procdump'
        >{BIN}/capp
            <desc>run last 15 seconds, stopped by SIGABRT before it ends</desc>
            <param>15</param>
            <param>king.txt</param>
        </app>
        
        <app name='queen' indent='60' core_filder='o' stdout='queen.stdout'
        >{BIN}/capp
            <desc>terminated by itself after 4 seconds</desc>
            <param>4</param>
            <param>queen.txt</param>
        </app>
        
        <app name='jack' indent='90' core_filder='o' stdout='jack.stdout' skip_os='darwin'
        >{BIN}/capp
            <desc>crash after 1 second, don't run on osx, core is too big</desc>
            <param>1</param>
            <param>crash</param>
        </app>
        
      </test>
      
      <test name="sigterm" sig="SIGINT" timeout="5">
        <app name="bgapp">{BIN}/bgapp</app>
      </test>
      
      <main>
        <sleep msg='---- main start to sleep'>2</sleep>
        <abort msg='---- abort king' name='king' sig='SIGABRT' sync='False' />
        <sleep>4</sleep>
        <noop  msg='---- main wakes up, remove all task' />
        <remove />
      </main>
      
    </unit-test>

    '''
