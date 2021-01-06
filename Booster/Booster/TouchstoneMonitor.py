"""
Python interface to launch Touchstone and monitor its running status
Usage on an external script:
import TouchstoneMonitor
arg = {
    "testEnv": "environment.xml",
    "testSuite": "suite.xml",
    "outputPrefix": "output prefix",
    ...
}
TouchstoneMonitor.TouchstoneMonitor(**arg).run()
 For a full list of valid arguments and their default values, check TouchstoneMonitor's valid_args dictionary
"""
from __future__ import print_function

import sys
import asynchat
import asyncore
import collections
import gzip
import logging
import os
import os.path
import platform
import re
import shutil
import signal
import socket
import string
import subprocess
import threading
import time
import traceback
import xml.etree.ElementTree as ET

import AtaUtil
import Booster.Shared.CrashUtils as CrashUtils
import ata.log
from BoosterError import BoosterError

class PyVer:
    pass


pyver = PyVer()
pyver.major, pyver.minor = sys.version_info.major, sys.version_info.minor


logger = ata.log.AtaLog(__name__)
logger.info('================= python version: {}.{}'.format(pyver.major, pyver.minor))

whatis = """$Id: //ATA/Booster/Maintenance/1.0/Booster/TouchstoneMonitor.py#68 $
$Change: 675485 $
$DateTime: 2020/11/24 19:02:36 $
$Revision: #68 $
"""


_win32api = None
if platform.system() == 'Windows':
    try:
        import win32api
        import win32con
        import win32process
        _win32api = True
    except ImportError:
        logger.info('win32api is not available')
        pass


class TsmException(Exception):

    def __init__(self, *args):
        super(TsmException, self).__init__(args)


class SubConsoleLogger(threading.Thread):
    def __init__(self, f_iter, f_name=None):
        super(SubConsoleLogger, self).__init__()
        self.f_iter = f_iter
        self.f_name = f_name

    def run(self):
        try:
            if self.f_iter and self.f_name:
                with open(self.f_name, 'w') as fout:
                    for s in self.f_iter:
                        fout.write(s)
        except Exception as e:
            logger('SubConsoleLogger exception: {}'.format(e))
        self.f_name = None
        self.f_iter = None


class TouchstoneMonitor(collections.MutableMapping):
    """
    Inheriting from collections.MutableMapping allows the object to be shared and used as a dictionary
    """

    def __init__(self, *args, **kwargs):
        self.status_items = ['SUCCEED',
                             'FAILED',
                             'SUSPENDED',
                             'NOT_FOUND',
                             'RESULT_IGNORED',
                             'FAILED_STARTUP',
                             'CLEANUP_FAILED',
                             'CRASHED',
                             'TIMEOUT',
                             'TOTAL'
                             ]

        self.valid_args = {
            "touchstone": {
                'description': 'full path of touchstone binary',
                'type': str
            },
            "testEnv": {
                'description': 'test environment XML file',
                'alias': 'te',
                'type': str
            },
            "testSuite": {
                'description': 'test suite XML file',
                'alias': 'ts',
                'type': str
            },
            "loop": {
                'description': 'loop running test suite',
                'alias': 'n',
                'value': 1,
                'type': int
            },
            "outputPrefix": {
                'description': 'prefix for names of output files',
                'alias': 'o',
                'type': str
            },
            "maxConsecutiveCrashes": {
                'description': 'max allowed consecutive crashes',
                'value': 3,
                'type': int
            },
            "maxCrashes": {
                'description': 'max allowed accumulated crashes',
                'value': 5,
                'type': int
            },
            "timeoutBeforeInitialized": {
                'description': 'timeout of before touchstone call-in (in second)',
                'value': 120,
                'type': int
            },
            "timeout": {
                'description': 'timeout of a single testcase (in minute)',
                'value': 5,
                'type': float
            },
            "maxConsecutiveTimeout": {
                'description': 'max allowed consecutive timeout',
                'value': 5,
                'type': int
            },
            "maxAccumulatedTimeout": {
                'description': 'max allowed accumulated timeout',
                'value': 20,
                'type': int
            },
            "maxConsecutiveFailure": {
                'description': 'max allowed consecutive test failures',
                'value': 50,
                'type': int
            },
            "port": {
                'description': 'port number that touchstone monitor listens to',
                'value': 0,
                'type': int
            },
            "maxPortScan": {
                'description': 'max scan available port when listen port is occupied',
                'value': 500,
                'type': int
            },
            "wd": {
                'description': 'working directory',
                'type': str,
                'value': '.',
            },
            "valgrind": {
                'description': 'valgrind tool',
                'type': str,
                'value': 'none',
            },
            "procdump": {
                'description': 'procdump tool, prepend to Touchstone launch string',
                'type': str,
            },
            "NO_BT": {
                'description': 'do not get backtrace when core is saved, set by xml or environment',
                'type': bool,
                'value': False,
            },
            "fail_norun": {
                'description': 'synthesize a failure test if no test has actually run',
                'type': bool,
                'value': True,
            },
            "QUICK_ABORT": {
                'description': 'abort the session if the 1st test case crashes or timeout, set by xml or environment',
                'type': bool,
                'value': True,
            },
        }

        self.lastInputTime = None
        self.sessionStartTime = None    # what's for?
        self.lastTestCaseTime = None    # used for timeout
        self.test_suite_name = None
        self.currentSet = None
        self.currentId = 1              # by convention, test case starts from 1
        self.childProc = None           # touchstone might be launched indirectly, e.g. via procdump on Windows
        self.touchstonePid = None
        # this handle is used to get return code on Windows when it can't be obtained by subprocess
        # by using win32api extension
        self.touchstoneProcessHandle = None
        self.currentSetCounts = self.init_counts()
        self.totalCounts = self.init_counts()
        self.sessionInited = False      # set when ServerStatusLog connected, reset before launch
        self.sessionStarted = False
        self.sessionCompleted = False
        self.consecutiveCrashes = 0
        self.crashes = 0
        self.consecutiveTimeout = 0
        self.accumulatedTimeout = 0
        self.consecutiveFailure = 0
        self.fail_norun = True
        self.signal = {}
        self.abort = False
        self.abortReason = None
        self.server = None
        self.procdump = None
        self.sub_console_logger = None

        self.__dict__.update(*args, **kwargs)
        self.outputDir = '.'

        self.touchstone_stdout_name = None
        self.touchstone_loggers = {}
        self.touchstone_logger_factory = TouchstoneLoggerFactory(self.outputPrefix)
        self._create_loggers()
        self.server_timeout = 5  # In seconds
        self.active_loggers = 0
        self.generation = 0      # how many times touchstone is launched

        msg = '\n\nLaunching Touchstone Monitor\n{}\n\n\n'.format(whatis)
        self.alert(msg, 'info')

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        return str(self.__dict__)

    def init_counts(self):
        return {status: 0 for status in self.status_items}

    def _create_loggers(self):
        """
        Pre-create all loggers before launching touchstone.
        The test session use a single set of loggers that are shared/reused by all generations.
        :return:
        """
        loggers = [
            'SummaryCsvLog',
            'SetSummaryCsvLog',
            'XmlSummaryLog',
            'ServerStatusLog',
            'VerboseLog',
            'Console'
        ]
        for l in loggers:
            self.touchstone_loggers[l] = self.touchstone_logger_factory.get_logger(self, l)

    def set_test_suite(self, suite_name):
        self.test_suite_name = suite_name

    def set_test_set(self, test_set_name):
        """
        Touchstone notifies that the test set is changed
        :param test_set_name:   the name that the test set starts
        """
        if test_set_name != self.currentSet:
            if not self.currentSet:
                self.touchstone_loggers['SetSummaryCsvLog'].write_log(
                    ','.join(['Test Set'] + self.status_items))
            else:
                current_set_counts = [str(self.currentSetCounts[status]) for status in self.status_items]
                self.touchstone_loggers['SetSummaryCsvLog'].write_log(
                    ','.join([self.currentSet] + current_set_counts))
            self.currentSetCounts = self.init_counts()
            self.currentSet = test_set_name
            self.currentId = 1

    def validate_test_set(self, name):
        """
        Validate if test set is changed unexpectly, warn and adjust if it is.
        :param name:    set-name
        """
        if name != self.currentSet:
            self.alert('Test set is changed unexpectedly, adjust to {} (from {}).'.format(name, self.currentSet))
            self.set_test_set(name)

    def validate_test_id(self, id):
        """
        Validate if test id is changed unexpectly, warn and adjust if it is.
        :param id:    test case id
        """
        if self.currentId != id:
            self.alert('Test IDs are not consecutive, adjust to {} (from {}-{}).'.format(id, self.currentSet, self.currentId))
            self.currentId = id

    def synthesizeFailure(self, msg, status='FAILED'):
        """
        Unexpected error, synthesize one to make sure the plan fails.
        :param msg:     error message
        """
        set_name = self.currentSet if self.currentSet is not None else 'Unknown'
        self.touchstone_loggers['XmlSummaryLog'].append_case(set_name, self.currentId, msg)
        self.currentSetCounts[status] += 1
        self.totalCounts[status] += 1
        self.currentSetCounts['TOTAL'] += 1
        self.totalCounts['TOTAL'] += 1
        if status != 'FAILED':      # put a mark in status log
            self.touchstone_loggers['ServerStatusLog'].write_log('STATUS:{}({}-{})\n======relaunch'.format(status, set_name, self.currentId))

    def set_test_id(self, name, id):
        """
        Touchstone notifies that a test case starts
        :param name:    set-name
        :param id:      id
        """
        if not self.sessionStarted:
            self.sessionStarted = True
        self.validate_test_set(name)
        self.currentId = id

    def set_test_status(self, name, id, status):
        """
        Touchstone notifies that a test case is finished and reports its status
        :param name:            test set name
        :param id:              test case ID
        :param status:          test case status, e.g. SUCCEED, FAILED, SUSPENDED
        :return:
        """
        if not self.sessionStarted:
            self.sessionStarted = True
        status = 'SUSPENDED' if status == 'EXCLUDED' else status
        self.consecutiveCrashes = 0
        self.consecutiveTimeout = 0
        self.lastTestCaseTime = time.time()
        if status == 'SUCCEED':
            self.consecutiveFailure = 0
        elif re.search(r'FAILED', status):
            self.consecutiveFailure += 1
        self.validate_test_set(name)
        self.validate_test_id(id)

        self.currentSetCounts[status] += 1
        self.totalCounts[status] += 1
        self.currentSetCounts['TOTAL'] += 1
        self.totalCounts['TOTAL'] += 1

        if self.maxConsecutiveFailure and self.consecutiveFailure >= self.maxConsecutiveFailure:
            msg = '\n\n!!!!!!!!!!!!!!!!!!!! ABORT !!!!!!!!!!!!!!!!!!!    after {} consecutive failures\n'.format(self.consecutiveFailure)
            self.alert(msg)
            self.abort = True
            self.abortReason = 'too many consecutive failures'
            self.kill_child()

        self.currentId += 1

    def validate_config(self, user_config):
        """
        Validate configurations
        :param user_config:
        :return:
        """
        if user_config:
            logger.debug("From User Config")
            for key in user_config:
                logger.debug("%s = %s" % (key, user_config[key]))
                if key in self or key in self.valid_args:
                    self[key] = user_config[key]
        # convert to valid value and type
        for key in self.valid_args:
            if key not in self.__dict__ and 'value' in self.valid_args[key]:
                self[key] = self.valid_args[key]['value']
            elif key in self:
                value = self[key]
                value_type = type(value)
                valid_type = self.valid_args[key].get('type', None)
                if value is not None and valid_type and value_type != valid_type:
                    logger.debug(
                        "Fixing {key}'s value type from {type} to {valid_type}".format(key=key, type=value_type,
                                                                                       valid_type=valid_type))
                    if valid_type == bool and value_type == str:
                        self[key] = True if self[key].upper() in ('TRUE', 'T', '1') else False
                    else:
                        self[key] = valid_type(self[key])

        # hard-code restrictions
        if self.maxCrashes > 5: self.maxCrashes = 5
        if platform.system() == 'Darwin' and self.maxCrashes > 2: self.maxCrashes = 2   # each osx core is 600M+
        # remove this restriction, XM big-join runs over 20min
        # DDP-433 will give alternative solutions
        # if self.timeout > 20: self.timeout = 20

        logger.debug("----------------- Effective Settings -------------------")
        for key in self.valid_args:
            logger.debug("%s = %s" % (key, self[key]))
        logger.debug("--------------------------------------------------------\n")

    def kill_child(self, sig=None):
        """
        Kills the Touchstone sub process
        Args:
            sig: an integer representing the SIG type. For more details,
            refer to https://docs.python.org/2/library/signal.html
        """
        # only kill or send signal to a running process
        if os.name == 'nt':
            sig = None
        if self.childProc and self.childProc.poll() is None:
            logger.info('kill_child: subprocess={} touchstone={}'.format(self.childProc.pid, self.touchstonePid))
            if sig:
                self.childProc.send_signal(sig)
            elif self.procdump:
                # touchstone is launched by procdump indirectly
                # let procdump generate core dump.
                # By convention the name is core.dump at the working directory,
                # post-process will rename and move the the proper folder
                logger.info('procdump dumps to core.dmp')
                pid = self.touchstonePid
                cmd = self.procdump.split(' ') + ['{}'.format(pid), 'core.PID.dmp']
                logger.info(' '.join(cmd))
                rc = subprocess.call(cmd)
                logger.info('return of subprocess.call={}'.format(rc))
                try:
                    # strange but it is true
                    # that Windows doesn't always allow to kill grandchild
                    # (or pid is not consistent between procdump and python)
                    #
                    # os.kill(pid, signal.SIGTERM)
                    # instead of letting procdump terminate gracefully (after touchstone terminates)
                    # kill it directly after a little delay
                    logger.info('wait for 2 seconds')
                    time.sleep(2)
                    logger.info('kill_child (subprocess={})'.format(self.childProc.pid))
                    self.childProc.kill()
                except Exception as e:
                    logger.info('fail to kill touchstone, kill procdump instead: {}'.format(e))
                    try:
                        self.childProc.kill()
                    except:
                        pass
            else:
                self.childProc.kill()
            start_wait = time.time()
            logger.debug("Waiting for process {}".format(self.touchstonePid))
            self._get_return_code()
            self.childProc = None
            end_wait = time.time()
            logger.debug(
                "Process {} took {} seconds to terminate".format(self.touchstonePid, end_wait - start_wait))
            if sig or self.procdump:
                self.alert(self._get_core_and_back_trace())
            self.touchstonePid = None
            self._wait_all_sockets_close()
        self._close_sub_console()

    def signal_handler(self, sig, stack):
        self.abort = True
        self.abortReason = 'signal caught ({})'.format(sig)

    def _get_core_and_back_trace(self, log_it=True):
        """
        Get the core file (and gzip it) and backtrace
        :param log_it:
        :return:
        """
        core_file = CrashUtils.find_and_save_core_dump(self.touchstonePid, self.wd, self.outputDir)
        msg = ''
        if not core_file:
            return ''
        cores = []
        if type(core_file) != list:
            cores.append(core_file)
        else:
            cores.extend(core_file)
        for coref in cores:
            msg += "Core-dump: {}\n".format(coref)
            if not (self.NO_BT or platform.system() == 'Windows'): # decode core on posix unless forbidden
                try:
                    msg += CrashUtils.get_back_trace(self.touchstone.split(' ')[0], coref)
                except Exception as e:
                    msg += str(e)
            # compress it
            with open(coref, 'rb') as fin, gzip.open(coref + '.gz', 'wb') as fout:
                shutil.copyfileobj(fin, fout)
            if os.path.exists(coref + '.gz'):
                os.remove(coref)
        if log_it and msg != '':
            logger.info(msg)
        return msg

    def _on_timeout(self):
        """
        Handles process timeout
        """
        msg = '\n\n!!!!!!!!!!!!!!!!!!!! TIMEOUT !!!!!!!!    {}-{} is not finished in {} minutes, Touchstone will be killed.\n'.format(self.currentSet, self.currentId, self.timeout)
        self.alert(msg)
        total_so_far = self._get_total()
        self.synthesizeFailure('Timed out. Current setting is {timeout} minutes.'.format(timeout=self.timeout), 'TIMEOUT')

        self.kill_child(signal.SIGABRT)  # core dump for further investigation. TODO: should we dump every time?

        msg = ''
        self.consecutiveTimeout += 1
        if self.consecutiveTimeout >= self.maxConsecutiveTimeout:
            msg = "\n\nABORT: Too many consecutive timeouts, current limit is {timeout} min * {maxConsecutiveTimeout}\n\n".format(
                **self)
            self.abort = True
            self.abortReason = 'too many consecutive timeouts'
        self.accumulatedTimeout += 1
        if not self.abort and (self.accumulatedTimeout >= self.maxAccumulatedTimeout):
            msg = "\n\nABORT: Too many accumulated timeouts, current limit is {timeout} min * {maxAccumulatedTimeout}\n\n".format(
                **self)
            self.abort = True
            self.abortReason = 'too many accumulated timeouts'
        if not self.abort and total_so_far == 0 and self.QUICK_ABORT:
            msg = "\n\nABORT: timeout on the 1st test case\n\n"
            self.abort = True
            self.abortReason = 'timeout on the 1st test case'
        if msg != '':
            self.alert(msg)
        if not self.abort:
            self._relaunch_process()

    def execute(self, command):
        """
        Executes a system command
        Args:
            command: array containing the executable at index 0 and followed by arguments
        """
        self._close_sub_console() # for safety, make sure any existed console loggers finish
        self.sessionInited = False
        self.sessionStarted = False
        self.childProc = None
        self.touchstonePid = None
        if self.touchstoneProcessHandle:
            try:
                win32api.CloseHandle(self.touchstoneProcessHandle)
            except:
                pass
        self.touchstoneProcessHandle = None
        logger.info(' '.join(command))
        if pyver.major == 2:
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, encoding='utf8')
        self.childProc = proc
        self.touchstonePid = proc.pid
        f_iter = iter(proc.stdout.readline, '')
        if self.procdump:
            # in this case, touchstone is actually the child of procdump
            #
            # first few lines are from procdump, which contain info that we care
            # Process:    exec_name (pid)
            # ...
            # Press Ctrl-C to end monitoring without terminating the process.
            #
            pattern_pid = re.compile(r'^Process:.*\((\d+)\)\s*$')
            str_procdump_end = 'Press Ctrl-C to end'
            pid = None
            for s in f_iter:
                if len(s) > 0 and s[-1] == '\n':
                    s = s.rstrip()
                if pid is None:
                    m = pattern_pid.match(s)
                    if m:
                        pid = int(m.group(1))
                        self.touchstonePid = pid
                elif str_procdump_end in s:
                    break
        logger.info("Running subprocess pid={} (touchstone: {})".format(proc.pid, self.touchstonePid))
        if _win32api and self.touchstonePid != self.childProc.pid:
            try:
                self.touchstoneProcessHandle = win32api.OpenProcess(
                    win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, int(self.touchstonePid))
            except Exception as e:
                logger.info('Fail to get process handle of touchstone: {}'.format(e))
        self.generation += 1
        self.lastTestCaseTime = time.time()
        self.touchstone_stdout_name = self._mk_pathname('touchstone-stdout-{}.txt'.format(self.touchstonePid))
        self.sub_console_logger = SubConsoleLogger(f_iter, self.touchstone_stdout_name)
        self.sub_console_logger.start()

    def _relaunch_process(self):
        """
        Relaunches a new Touchstone sub process.
        This happens when crash or timeout-and-killed
        """
        self._wait_all_sockets_close()
        self._close_sub_console()
        self.alert("\nRelaunch Touchstone, skip {}-{}".format(self.currentSet, self.currentId))
        resume_touchstone_cmd = self.command + ["-rtn", "{}-{}".format(self.currentSet, self.currentId)]
        self.execute(resume_touchstone_cmd)

    def _get_total(self, name=None):
        """
        Get total count of test cases so far
        name:       name of total, default is TOTAL
        :return:
        """
        if name is None or name not in self.totalCounts:
            name = 'TOTAL'
        return self.totalCounts[name]

    def _close_sub_console(self):
        """ close sub-console logger if it is running
        """
        if self.sub_console_logger:
            self.sub_console_logger.join()
            self.sub_console_logger = None

    def is_subprocess_running(self):
        """
        Check if subprocess is still running,
        if it is not, get and dump the return code or signal caught.

        Returns: True if the Touchstone sub process is still running
        """
        is_running = self.childProc and self.childProc.poll() is None
        if not is_running and self.childProc:
            self._get_return_code()
            self.childProc = None
            # leave touchstonePid unchanged, which is used to get core if applicable
        return is_running

    def _get_return_code(self):
        """
        Get touchstone return code
        :return:
        """
        pid = self.childProc.pid
        return_code = self.childProc.wait()  # make sure this is called after poll() to avoid deadlock
        if os.name != 'nt' and return_code < 0:
            logger.info('subprocess {} caught signal {}'.format(pid, -return_code))
        else:
            logger.info('subprocess {} return code {} ({:X})'.format(pid, return_code, 0xffffffff & return_code))
            if os.name == 'nt' and self.touchstonePid != pid:
                if self.touchstoneProcessHandle:
                    try:
                        return_code = win32process.GetExitCodeProcess(self.touchstoneProcessHandle)
                        logger.info('touchstone pid={} return code={}'.format(self.touchstonePid, return_code))
                        win32api.CloseHandle(self.touchstoneProcessHandle)
                    except Exception as e:
                        logger.info('Fail to get return code through win32api: {}'.format(e))
                    self.touchstoneProcessHandle = None
                elif not _win32api:
                    logger.info('touchstone is launched by procdump, please install pywin32 to get its return code')

    def _is_crash(self):
        """
        Check if Touchstone has crashed
        Returns: False if tests did not complete
        """
        fallback_left = self.fallback is not None and os.path.isfile(self.fallback)
        msg = ''
        if self.sessionCompleted and fallback_left:
            # crash but we don't care, just put a log
            msg = '\n\nAll tests finish successfully, however CRASH happened during cleanup!!!\n'
        elif not self.sessionCompleted and self.fallback and not fallback_left:
            # no crash, no COMPLETE, but self.fallback is deleted by touchstone
            # treat as normal complete
            self.sessionCompleted = True
        if msg != '':
            self.alert(msg)

        return not self.sessionCompleted

    def _on_crash(self):
        """
        Handles Touchstone crashes
        """
        if self.abort:
            return

        if not self.sessionInited:
            self._close_sub_console()
            msg = "\nERROR: Could not start running tests. Check given arguments and/or DLL.\n"
            msg += "try to get the core file\n"
            msg += self._get_core_and_back_trace()
            raise BoosterError(__name__, msg)

        total_so_far = self._get_total()
        self.synthesizeFailure('Test crashed.', 'CRASHED')

        msg = "\n\n!!!!!!!!!! CRASHED !!!!!!!!!!    {currentSet}-{currentId}\n".format(**self)
        msg += self._get_core_and_back_trace()

        self.consecutiveCrashes += 1
        if self.consecutiveCrashes >= self.maxConsecutiveCrashes:
            msg += '\n\n!!!!!!!!!!!!!!!!!!!! ABORT !!!!!!!!!!!!!!!!!!!     after {} consecutive crashes\n'.format(self.consecutiveCrashes)
            self.abort = True
            self.abortReason = 'too many consecutive crashes'
        self.crashes += 1
        if not self.abort and self.crashes >= self.maxCrashes:
            msg += '\n\n!!!!!!!!!!!!!!!!!!!! ABORT !!!!!!!!!!!!!!!!!!!    after {} accumulated crashes\n'.format(self.crashes)
            self.abort = True
            self.abortReason = 'too many crashes'
        if total_so_far == 0 and self.QUICK_ABORT:
            msg += '\n\n!!!!!!!!!!!!!!!!!!!! ABORT !!!!!!!!!!!!!!!!!!!     crash on the 1st test case\n'
            self.abort = True
            self.abortReason = 'crash on the 1st test case'
        self.alert(msg)
        if not self.abort:
            self._relaunch_process()

    def _complete_output(self):
        """ Flush SetSummaryCsvLog. """
        ctx_totalcounts = {s: self.totalCounts[s] for s in self.status_items}
        total = ctx_totalcounts['TOTAL']
        suspended = ctx_totalcounts['SUSPENDED']
        not_found = ctx_totalcounts['NOT_FOUND']
        if total - suspended - not_found == 0:
            self.alert('!!!!!!!!!!!!! No test has actually run')
            self.alert('    total:     {:10d}'.format(total))
            self.alert('    suspended: {:10d}'.format(suspended))
            if not_found:
                self.alert('    not found: {:10d}'.format(not_found))
            if self.fail_norun:
                self.synthesizeFailure('No test has actually run')
                self.alert('    the whole session is considered failed')
                self.alert('    (feature configurable by _Monitor.fail-norun in env xml)')
                ctx_totalcounts = {s: self.totalCounts[s] for s in self.status_items}
        num_failures = ctx_totalcounts['FAILED']
        current_set_counts = [str(self.currentSetCounts[status]) for status in self.status_items]
        total_counts = [str(self.totalCounts[status]) for status in self.status_items]

        self.touchstone_loggers['SetSummaryCsvLog'].write_log(
            ','.join([str(self.currentSet)] + current_set_counts))
        self.touchstone_loggers['SetSummaryCsvLog'].write_log(
            ','.join(['SUITE SUMMARY'] + total_counts))

        output_summary = \
            """
--------------------------------
Total           {TOTAL:10d}
SUCCEED         {SUCCEED:10d}
FAILED          {FAILED:10d}
FAILED_STARTUP  {FAILED_STARTUP:10d}
CLEANUP_FAILED  {CLEANUP_FAILED:10d}
RESULT_IGNORED  {RESULT_IGNORED:10d}
SUSPENDED       {SUSPENDED:10d}
NOT_FOUND       {NOT_FOUND:10d}
CRASHED         {CRASHED:10d}
TIMEOUT         {TIMEOUT:10d}
--------------------------------
End of tests
            """.format(**ctx_totalcounts)

        logger.info("{} Results:".format(self.test_suite_name))
        logger.info(output_summary)
        return ctx_totalcounts

    def _get_executable(self):
        fp = self.touchstone
        self.bin = re.sub(r'.*/', '', fp)
        return self.bin

    def _mk_pathname(self, fname):
        """
        Create a pathname for fname in the path of output_prefix, e.g.
        return output_dir/myfile when output_prefix is output_dir/o
        """
        return os.path.join(self.outputDir, fname)

    def _create_fallback_file(self, path):
        """
        Create a fallback file, touchstone should remove it when it terminates without crash
        Returns: the filename if succeed, or None
        """
        fallback = ''
        if not os.path.isdir(path):
            path = os.path.dirname(path)
        fallback = os.path.join(path, "fallback.dat")
        try:
            with open(fallback, 'w'):
                pass
            if not os.path.isfile(fallback):
                raise Exception("\n\n!!!!!!!!!!!!!!!!!!!! Fallback: fail to create {fallback}".format(fallback))
        except Exception as exc:
            logger.warning("\n\n!!!!!!!!!!!!!!!!!!!! Fallback: fail to create {fallback}. error: \"{error}\". \
            Crash detection might be inaccurate!".format(fallback=fallback, error=str(exc)))
            fallback = ''
        return fallback

    def _get_config_from_xml(self, xml_file_name, config_tag, filter):
        """
        Get configurations from XML file
        Args:
           xml_file_name:
           config_tag: root tag that contains the configuration.
           filter:  list of accepted tags

        Returns: Touchstone Monitor configuration in a dictionary format
        """
        try:
            tree = ET.parse(xml_file_name)
            monitor_settings = tree.find(config_tag)
            config = {}
            if monitor_settings is not None and len(monitor_settings):
                for element in monitor_settings:
                    # by conventioin, xml tags/attrs use dash (-) to separate words
                    # python attributes don't, they use underscore (_) unless using camel-style
                    setting = element.tag.replace('-', '_')
                    value = element.text
                    if setting in filter:
                        config[setting] = value
            return config
        except ET.ParseError:
            logger.critical("Failed to parse {}".format(xml_file_name))
            raise

    def _init_environment(self, cwd):

        logger.info("Current working directory: %s" % cwd)
        xmlcfg = self._get_config_from_xml(self.testEnv, '_Monitor',
                                           self.valid_args.keys())
        # environment variables override xmlcfg
        # NO_BT         true|t|1    disable to get backtrace from core
        for ev in ('NO_BT', 'QUICK_ABORT'):
            if ev in os.environ:
                xmlcfg[ev] = os.environ[ev]

        self.validate_config(xmlcfg)
        if not self._get_executable():
            raise Exception("Not executable: %s\n" % self.touchstone)

        if cwd != self.wd and self.wd != '.':
            if not os.path.isdir(self.wd):
                raise Exception("Working directory {wd} doesn't exist".format(**self))
            if not os.access(self.wd, os.X_OK | os.W_OK):
                raise Exception("No permission to access and write in {wd}".format(**self))
            logger.info("Changing current working directory to {wd}".format(**self))
            os.chdir(self.wd)

        self.outputDir = os.path.normpath(os.path.join(self.wd, self.outputPrefix))
        if not os.path.isdir(self.outputDir):
            self.outputDir = os.path.dirname(self.outputDir)
            if self.outputDir == '':
                self.outputDir = '.'
        self.fallback = self._create_fallback_file(self.outputDir)

        self.signal['INT'] = signal.signal(signal.SIGINT, self.signal_handler)
        self.signal['TERM'] = signal.signal(signal.SIGTERM, self.signal_handler)
        if os.name != 'nt':
            self.signal['QUIT'] = signal.signal(signal.SIGQUIT, self.signal_handler)

        # fallback solution to perform procdump (not through tsm.py or env.TOUCHSTONE_COMMAND_PREFIX)
        if platform.system() == 'Windows':
            if self.procdump is None and 'PROCDUMP' in os.environ:
                self.procdump = os.environ['PROCDUMP']
                if '-e' not in self.procdump:
                    self.procdump += ' -e'
        else:
            self.procdump = None

    def _create_server(self):
        """ Create a server and bind specified address
            the port can be either assigned by the core (if port == 0)
            or scan from a base port

            return: server,port
        """
        host = 'localhost'
        port = self.get('port', 0)
        if port == 0 and platform.system() == 'HP-UX':
            # hpux has a bug that getsockname() returns (0, (0,0,...))
            # due to a corrupted build of _socket
            # http://grokbase.com/t/python/python-list/11a5mqzmxw/socket-getsockname-is-returning-junk
            #
            # simba internal: DDP-297
            port = 18000
        if port == 0:
            # Let the kernel choose the port number
            # not recommended, because it is a selfish behavior which
            # makes itself always available but potentially block other services
            server = Server((host, port), self)
            ip, port = server.socket.getsockname()
            return server, port
        # otherwise scan from port upto maxPortScan
        max_scan = self.get('maxPortScan', 500)
        for n in range(max_scan):
            try:
                server = Server((host, port), self)
                return server, port
            except socket.error as e:
                try:
                    server.close()
                except:
                    pass
                port += 1
        raise BoosterError(__name__, "ERROR: Monitor could not find a listen port.\n")

    def _wait_all_sockets_close(self):
        """
         In some cases, loggers will still be active
         even when all tests complete
         This provides a last chance for loggers to send data
        """
        for i in range(self.server_timeout):
            if self.active_loggers > 0:
                asyncore.loop(timeout=1, count=1)

    def _start_touchstone(self):
        """ Launch touchstone binary
        """
        self.server, port = self._create_server()
        self.server.listen(5)
        self.command = self.touchstone.split(' ') + ["-te", self.testEnv, "-ts", self.testSuite,
                        "-o", self.outputPrefix, "-n", "1", "-serverip", '127.0.0.1', "-sp", str(port)]
        if self.procdump is not None:
            self.command = self.procdump.split(' ') + ['-x', self.wd] + self.command
        fallback = self.get('fallback', None)
        if fallback is not None and self.fallback != '':
            self.command += ['-fb', self.fallback]
        self.execute(self.command)
        now = time.time()
        self.sessionStartTime = now
        while True:
            # Loop times out after a second
            asyncore.loop(timeout=1, count=1)
            now = time.time()
            if self.active_loggers == 0 and self.sessionInited:
                # delay checking subprocess health
                # as long as there is a socket connection, touchstone is alive
                if not self.is_subprocess_running() and self._is_crash():
                    self._on_crash()
            if not self.sessionInited:
                if not self.is_subprocess_running():
                    msg = 'Touchstone dies before initialization'
                    self.abort = True
                elif now - self.lastTestCaseTime >= self.timeoutBeforeInitialized:
                    msg = 'it takes too long for touchstone to initialize ({} seconds), abort...'.format(now - self.lastTestCaseTime)
                    self.kill_child(signal.SIGABRT)
                    self.abort = True
                if self.abort:
                    self.abortReason = msg
                    logger.info(msg)
                    print(msg)
            else:
                # Handle timeout if touchstone is initialized and is still running
                if not (self.abort or self.sessionCompleted) and self.childProc:
                    if now - self.lastTestCaseTime >= self.timeout * 60:
                        self._on_timeout()
            if self.abort or self.sessionCompleted:
                break

        self._close_sub_console()

        self._wait_all_sockets_close()
        # Explicitly close all sockets in case they're still open
        if self.active_loggers > 0:
            logger.debug(
                "There are still {} active loggers. Attempting to close them explicitly...".format(self.active_loggers))
            asyncore.close_all()

        # append a synthetic test-case for abort
        if self.abort:
            self.synthesizeFailure('SESSION ABORT: {}'.format(self.abortReason))

        # Process test results if there are any
        test_results = self._complete_output()
        # Dump test_results dictionary to a file
        logger.debug("Saving test results in " + self.outputPrefix + "_summary.pickle")
        AtaUtil.pickle_obj(test_results, self.outputPrefix + "_summary.pickle")


    def _cleanup(self, cwd):
        if self.server is not None:
            self.server.close()
        self.kill_child()
        # close all touchstone log files
        for ts_log in self.touchstone_loggers:
            self.touchstone_loggers[ts_log].close_log()
        # delete fallback anyway
        fallback = self.get('fallback', None)
        if fallback and os.path.isfile(fallback):
            os.remove(fallback)

        # Change back to the initial cwd
        if cwd != self.wd:
            os.chdir(cwd)

        # restore signals
        if self.signal:
            signal.signal(signal.SIGINT, self.signal['INT'])
            signal.signal(signal.SIGTERM, self.signal['TERM'])
            if os.name != 'nt':
                signal.signal(signal.SIGQUIT, self.signal['QUIT'])

    def run(self):
        """
        Executes a Touchstone process and monitors its status
        This is the interface for other booster modules
        Return a tuple of (is_abort, reason)
        """
        logger.info("Running Test Suite: %s\n\n" % os.path.basename(self.testSuite))
        cwd = os.getcwd()
        try:
            self._init_environment(cwd)
            self._start_touchstone()
        except Exception:
            raise Exception("Touchstone monitor failed. error: {}".format(traceback.format_exc()))
        finally:
            self._cleanup(cwd)
        return (self.abort, self.abortReason)

    def alert(self, msg, hint=None):
        """
        Log important information, such as crash, timeout, kill, etc
        to make sure it is logged everywhere.
        """
        if hint == 'info':
            logger.info(msg)
            self.touchstone_loggers['Console'].write_log(msg)
        else:
            logger.warning(msg)
            self.touchstone_loggers['Console'].write_log(msg)
            self.touchstone_loggers['VerboseLog'].write_log(msg)


class Server(asyncore.dispatcher):
    """
    Receives connections from a Touchstone process and establishes handlers for each client.
    """

    def __init__(self, address, ts_monitor):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        s = self.socket
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        s.setsockopt(socket.IPPROTO_TCP, 1, 1)
        s.bind(address)
        self.ts_monitor = ts_monitor

    def handle_accept(self):
        """ Handles a new connection from a client socket """
        client_info = self.accept()  # client_sock, peer_addr
        if client_info:
            Handler(client_info[0], self.ts_monitor)

    def handle_close(self):
        """ Handling closing a connection. This occurs when all clients finished sending data """
        try:
            self.close()
        except Exception as e:
            print('handle close exception: ' + e)


class Handler(asynchat.async_chat):
    """
    This is used for handling the data sent from a client to the server
    """

    def __init__(self, sock, context):
        self.received_data = []
        asynchat.async_chat.__init__(self, sock)
        self.set_terminator(b'\n')  # we receive data in lines
        self.name = None
        self.bad_logname = False
        self.log_file = None
        self.test_complete = False
        self.context = context
        return

    def collect_incoming_data(self, data):
        # client can send data in chunks
        self.received_data.append(data)

    def found_terminator(self):
        """ When a full line has been received
        """
        try:
            if pyver.major == 2:
                data = ''.join(self.received_data)
            else:
                data = b''.join(self.received_data).decode('utf8')
        except Exception as e:
            print('====found_terminator exception:')
            traceback.print_exc()
            for c in self.received_data:
                print('    {}'.format(c))
            print('===')
            data = ''
        self.received_data = []
        # The first data received from a client is the log type
        if not self.name:
            self.name = data
            self.context.active_loggers += 1
            logger.debug('++++ {} connected: {}'.format(self.name, self.context.active_loggers))
            try:
                self._getLogger().on_connect()
            except Exception as e:
                logger.debug(e)
        elif not self.bad_logname:
            # Perform the touchstone log's action
            self._getLogger().action(data)


    def handle_close(self):
        try:
            self.close()
        except Exception as e:
            logger.debug('---- {} handle close exception: {}'.format(self.name, e))
            pass
        self.context.active_loggers -= 1
        logger.debug('---- {} disconnected: {}'.format(self.name, self.context.active_loggers))
        if self.name and not self.bad_logname:
            self._getLogger().on_disconnect()
 

    def _getLogger(self):
        if self.name is None:
            raise TsmException('Logger is not bound yet')
        try:
            return self.context.touchstone_loggers[self.name]
        except KeyError:
            # TODO: unknown log name/type
            self.bad_logname = True         # don't try to get logger by name later
            raise TsmException('unknown Logger: {}'.format(self.name))



class TouchstoneLog(object):
    """
    The base class for TouchstoneLog types

    standalone          vs  TSM/ID
    info.csv                n/a
    performance.csv         n/a
    set_summary.csv         set_summary.csv/SetSummaryCsvLog
    summary.csv             summary.csv/SummaryCsvLog
    summary.xml             summary.xml/XmlSummaryLog
    temp.txt                n/a
    verbose.log             verbose.log/VerboseLog
    n/a                     status.log/ServerStatusLog
    n/a                     console.log/Console

    """

    def __init__(self, owner, logname):
        """
        Constructor
        Args:
            logname: Log type name
        """
        self.owner = owner          # TouchstoneMonitor
        self.logname = logname
        self.base_logname = os.path.basename(self.logname)
        self.handler = logging.FileHandler(filename=logname, mode='w')
        self.log = logging.getLogger(self.base_logname)
        self.log.setLevel(logging.DEBUG)
        self.log.addHandler(self.handler)

    def action(self, line):
        """
        Args:
            line: data to handle for a log object
        """
        pass

    def close_log(self):
        try:
            self.handler.close()
        except Exception as e:
            print('{} close exception: {}'.format(self.base_logname, e))
            pass

    def _escape(self, data):
        """ escape non-printable characters
        """
        printable = [c if c in string.printable else repr(c) for c in data]
        return ''.join(printable)

    def write_log(self, data):
        self.log.debug(str(data))
        self.handler.flush()

    def on_connect(self):
        """ handler when a named touchstone socket is connected
        """
        pass

    def on_disconnect(self):
        """ handler when a named touchstone socket is disconnected
        """
        pass

class SetSummaryCsvLog(TouchstoneLog):
    """
    sample: (counts of each test set)
    SUCCEED,FAILED,FAILED_STARTUP,CLEANUP_FAILED,RESULT_IGNORED,SUSPENDED,NOT_FOUND,CRASHED,TOTAL
    INTERNAL_1,1,1,0,0,0,0,0,0,2
    INTERNAL_2,1,0,1,0,0,0,0,0,2
    DATACONVERTION,0,0,1,1,0,0,0,0,2
    SQL_TEST,0,0,2,0,0,0,0,0,2

    SUITE SUMMARY,2,1,4,1,0,0,0,0,8
    """
    def __init__(self, owner, output_prefix):
        super(SetSummaryCsvLog, self).__init__(owner, output_prefix + "__set_summary.csv")


class SummaryCsvLog(TouchstoneLog):
    """
    Info and status of each test case, in csv format.

    sample
    "Result","IsIgnorable","TestRunID","TestSuiteName","TestSetName","TestCaseName","ID","Description","Summary Info","Elapse"
    "SUCCEED","","R20180625180027","Touchstone","INTERNAL_1","SIMULATE-SETCODE","1","Set specified return code","","0"
    "FAILED","","R20180625180027","Touchstone","INTERNAL_1","SIMULATE-SETCODE","2","Set specified return code","","0"
    "SUCCEED","","R20180625180027","Touchstone","INTERNAL_1","SIMULATE-TIMEOUT","3","Simulate the driver timeout","","2996"
    "FAILED_STARTUP","","R20180625180027","Touchstone","INTERNAL_1","SIMULATE-SETCODE","4","Set specified return code","","0"

    """
    def __init__(self, owner, output_prefix):
        super(SummaryCsvLog, self).__init__(owner, output_prefix + "__summary.csv")
        self.lines = 0

    def action(self, line):
        """
        Args:
            line: data to write in a log file
        """
        self.write_log(line)
        self.lines += 1

    def close_log(self):
        if self.lines == 0:     # nothing written yet, make a synthetic error message
            self.write_log('''Result,IsIgnorable,TestRunID,TestSuiteName,TestSetName,TestCaseName,ID,Description,Summary Info,Elapse
FAILED,,unknown,unknown-suite,unknown-set,unknown-case,1,unknown,"Fail to launch or empty suite/set,0
''')
        super(SummaryCsvLog, self).close_log()


class XmlSummaryLog(TouchstoneLog):
    """
    Info and status of each test case, in XML format.

    sample
    <?xml version="1.0" encoding="UTF-8" ?>
    <testsuite tests="2" failures ="1" name="Touchstone">
    <testcase name="INTERNAL_1-1"/>
    <testcase name="INTERNAL_1-2">
        <failure message="...."/>
    </testcase>
    </testsuite>

    """

    def __init__(self, owner, output_prefix):
        super(XmlSummaryLog, self).__init__(owner, output_prefix + "__summary.xml")
        self.cache = []
        self.test_suite_name = None

    def action(self, line):
        """
        Args:
            line: data to write in a log file
        """
        # Add data to a cache in the context
        # non-printable characters might break the xml parser
        printable_line = self._escape(line)
        if self.test_suite_name is None:
            self.test_suite_name = printable_line
            self.owner.set_test_suite(self.test_suite_name)
        else:
            self.cache.append(printable_line)


    def append_case(self, test_set=None, test_case=None, fail_msg=None):
        """
        Insert synthetic message when TSM detects exceptions, such as
            * crash
            * timeout

        """
        self.close_testcase()
        if test_set is None: test_set = 'unknown'
        if test_case is None: test_case = 'unknown'
        if fail_msg is None:
            self.cache.append('  <testcase name="{}-{}" />'.format(test_set, test_case))
        else:
            self.cache.append('  <testcase name="{}-{}">'.format(test_set, test_case))
            self.cache.append('    <failure message="{}" />'.format(fail_msg))
            self.cache.append('  </testcase>')


    def close_testcase(self):
        """
        Close test case if it is open.

        The socket is updated by line, however summary.xml has following pattern for test-cases
            <testcase name="set_name-case_id"/>
        or
            <testcase name="set_name-case_id">
              <failure message="..."/>
            </testcase>
        Because the socket can be broken anytime, closing tag </testcase> can be lost.
        """
        n = len(self.cache)
        if n > 0:
            close_tag = re.compile(r'\s*</testcase>|\s*<testcase\s+name="[^"]+"\s*/>')
            last_line = self.cache[n - 1]
            if not close_tag.match(last_line):
                self.cache.append('  </testcase>')

    def close_log(self):
        """
        Actually write to summary.xml log:
            count total/failures
            generate synthetic failure if no test case is actually logged
        """
        self.close_testcase()
        suite_name = self.test_suite_name
        if suite_name is None:
            suite_name = 'unknown'
        else:
            suite_name = suite_name.strip()

        p_case = re.compile(r'\s*<testcase\s')
        p_fail = re.compile(r'\s*<failure\s')
        total = 0
        failures = 0
        for e in self.cache:
            if p_case.match(e): total += 1
            if p_fail.match(e): failures += 1

        # Make junit parser red if total is zero
        if total == 0:
            self.append_case('Unknown', '1', 'Touchstone Monitor: zero test case executes - fail to launch or empty suite')
            total = 1
            failures = 1

        self.write_log('''<?xml version="1.0" encoding="UTF-8" ?>
<testsuite tests="{total}" failures="{failures}" name="{suite_name}">
{data}
</testsuite>
'''.format(total=total, failures=failures, suite_name=suite_name, data='\n'.join(self.cache)))
        super(XmlSummaryLog, self).close_log()




class ServerStatusLog(TouchstoneLog):
    """
    Used for synchronizing status between TS and TSM, not applicable to stand-alone TS.
    Each line stands for a status change, identified by a pattern (see below)
    """
    def __init__(self, owner, output_prefix):
        super(ServerStatusLog, self).__init__(owner, output_prefix + "__status.log")

        class OnSessionCompleted(object):
            def __init__(self):
                self.pattern = re.compile(r'COMPLETE')

            def __call__(self, monitor, m):
                monitor.sessionComplete = True

        class OnSessionInit(object):
            def __init__(self):
                self.pattern = re.compile(r'INIT')

            def __call__(self, monitor, m):
                monitor.sessionInited = True

        class OnSessionStart(object):
            def __init__(self):
                self.pattern = re.compile(r'START')

            def __call__(self, monitor, m):
                monitor.sessionStarted = True

        class OnSetChange(object):
            def __init__(self):
                self.pattern = re.compile(r'SET CHANGE:(.+)')

            def __call__(self, monitor, m):
                name = m.group(1)
                monitor.set_test_set(name)

        class OnTestStart(object):
            def __init__(self):
                self.pattern = re.compile(r'CASE:(.+)-([0-9]+)$')

            def __call__(self, monitor, m):
                name, id = m.groups()
                monitor.set_test_id(name, int(id))

        class OnTestFinish(object):
            def __init__(self):
                self.pattern = re.compile(r'STATUS:(.+)\((.+)-([0-9]+)\)')

            def __call__(self, monitor, m):
                status, name, id = m.groups()
                monitor.set_test_status(name, int(id), status)

        self.commands = [           # in the order of frequency
            OnTestStart(),
            OnTestFinish(),
            OnSetChange(),
            OnSessionInit(),
            OnSessionStart(),
            OnSessionCompleted(),
        ]

    def on_connect(self):
        self.owner.sessionInited = True

    def on_disconnect(self):
        # self.owner.sessionInited = True
        # TODO - touchstone terminates
        pass

    def action(self, line):
        """
        Find patterns in line for handling different Touchstone server statuses
        Args:
            line: data to write in a log file

        """
        # print('========ServerStatus: [{}]'.format(line))
        self.write_log(line)
        monitor = self.owner
        for cmd in self.commands:
            m = re.match(cmd.pattern, line)
            if m:
                cmd(monitor, m)
                return
        monitor.alert('====UNKNOWN STATUS: [{}]'.format(line))


class VerboseLog(TouchstoneLog):
    """
    TS start time, followed by verbose info and status of each test case.
    TSM insert 8 blank lines before the 1st TS line (start-time) to separate each generation.
    Each test case starts with a dash-line.

    sample:

    Simba Test Verbose Log Started on Mon Jun 25 11:00:27 2018
    ----------------------------------------------------------------------
    Test Suite: Touchstone
    Test Set: INTERNAL_1
    Test Case: SIMULATE-SETCODE (1) : Set specified return code
    Status: SUCCEED

    ----------------------------------------------------------------------
    Test Suite: Touchstone
    Test Set: INTERNAL_1
    Test Case: SIMULATE-SETCODE (2) : Set specified return code
    Status: FAILED

    ...
    ----------------------------------------------------------------------
    Test Suite: Touchstone
    Test Set: SQL_TEST
    Test Case: SQL_QUERY (1) : Basic SQL Query test.
    Status: FAILED_STARTUP

    SQLDriverConnectW: Diagnostic mismatch.
    File: SimbaODBCTestFramework\Factories\ConnectionFactory.cpp at line: 182
    Expected:
            RC: SQL_SUCCESS
            -or-
            RC: SQL_SUCCESS_WITH_INFO SQLSTATES: 01000 and 01000
            -or-
            RC: SQL_SUCCESS_WITH_INFO SQLSTATES: 01000
            -or-
            RC: SQL_SUCCESS_WITH_INFO SQLSTATES: 01000 and HYC00
            -or-
            RC: SQL_SUCCESS_WITH_INFO SQLSTATES: 01000 and S1C00
    Actual:
            RC: SQL_ERROR
            IM002 (0) [Microsoft][ODBC Driver Manager] Data source name not found and no default driver specified
    ...

    """
    def __init__(self, owner, output_prefix):
        super(VerboseLog, self).__init__(owner, output_prefix + "__verbose.log")

    def action(self, line):
        self.write_log(line)

    def on_connect(self):
        self.write_log('\n' * 8)


class ConsoleLog(TouchstoneLog):
    def __init__(self, owner, output_prefix):
        TouchstoneLog.__init__(self, owner, output_prefix + "__console.log")

    def on_connect(self):
        self.write_log('\n' * 8)

    def action(self, line):
        logger.debug(line)
        self.write_log(line)


class TouchstoneLoggerFactory(object):
    """
    Factory for creating Touchstone Log types
    """

    #
    # TODO - a factory should be a singleton object
    #

    def __init__(self, output_prefix=''):
        self.outputPrefix = output_prefix

    def get_logger(self, owner, name):
        """
        Returns: A TouchstoneLog object

        """
        log = None
        if name == 'SummaryCsvLog':
            log = SummaryCsvLog(owner, self.outputPrefix)

        elif name == 'SetSummaryCsvLog':
            log = SetSummaryCsvLog(owner, self.outputPrefix)

        elif name == 'XmlSummaryLog':
            log = XmlSummaryLog(owner, self.outputPrefix)

        elif name == 'ServerStatusLog':
            log = ServerStatusLog(owner, self.outputPrefix)

        elif name == 'VerboseLog':
            log = VerboseLog(owner, self.outputPrefix)

        elif name == 'Console':
            log = ConsoleLog(owner, self.outputPrefix)

        return log


if __name__ == '__main__':
    # The root directory of Booster should be added to PYTHONPATH if TouchstoneMonitor is ran as a standalone script
    # on Windows:
    # > set PYTHONPATH=[P4ROOT]\ATA\Booster\[BRANCH]
    # on *nix:
    # > export PYTHONPATH=[P4ROOT]\ATA\Booster\[BRANCH]

    from argparse import ArgumentParser

    parser = ArgumentParser(description='Touchstone Monitor Command Options')
    parser.add_argument('-te', '--testEnv', type=str, default='env.xml', help='Environment file')
    parser.add_argument('-ts', '--testSuite', type=str, default='suite.xml', help='TestSuite file')
    parser.add_argument('-o', '--outputPrefix', type=str, help='Output path prefix for the test result files')
    parser.add_argument('-e', '--touchstone', type=str, help='The Touchstone executable', required=True)
    parser.add_argument('-wd', '--wd', type=str, default='.', help='The current working directory')

    ext = re.compile(r'.*\.xml$', re.IGNORECASE)
    def fix(d, key):
        """ append .xml if it is not """
        fname = d.get(key)
        if fname is None:
            raise AssertionError('{} is not defined'.format(key))
        elif not ext.match(fname):
            d[key] = fname + '.xml'

    args = vars(parser.parse_args())
    fix(args, 'testEnv')
    fix(args, 'testSuite')
    TouchstoneMonitor(**args).run()
