from __future__ import print_function

import os
import sys
import threading
import time
import traceback
import unittest

import AtaUtil
import ata.log
from RESTClient import RESTClient
from ata.bamboo import getBambooVar

logger = ata.log.AtaLog(__name__)

local = 'http://localhost:5555/rest'
closure_min = ['BAMBOO_PLANKEY', 'BAMBOO_BUILDNUMBER']
base = getBambooVar(os.environ, 'ATA_SKIPPER')
if base is None:
    base = local


class Skipper(RESTClient):
    def __init__(self, args={}):
        self.args = args
        self.ping_interval = 180  # seconds
        self.ping_thread = SkipperThread(args, self._ping, "ping", self.ping_interval)
        self.ping_thread_timeout = 60  # seconds
        self.plan = Plan(base, self.args)

    def startPlan(self, optional=None):
        self.startPingThread()
        return self.plan.start(optional=optional)

    def endPlan(self, optional=None):
        self.stopPingThread()
        return self.plan.end(optional=optional)

    def _ping(self):
        """
        Sends interval pings to skipper using a rest request
        This allows skipper to get updates on a plan's status
        """
        return self.post(
            base,
            '/plan/ping',
            AtaUtil.getSelectedBambooVariables(self.args, closure_min)
        )

    def startPingThread(self):
        self.ping_thread.start()

    def stopPingThread(self):
        self.ping_thread.stop()
        self.ping_thread.join(self.ping_thread_timeout)
        if self.ping_thread.is_alive():
            logger.warning("WARNING: Ping thread timed out after {} seconds.".format(
                self.ping_thread_timeout))
        if self.ping_thread.exc_info:
            msg = "Ping thread failed during the run. Last reported failure:\n"
            msg += self.ping_thread.exc_info
            logger.critical(msg)


class Plan(RESTClient):
    def __init__(self, base_url, args):
        super(Plan, self).__init__()
        self.args = args
        self.product = self.args['BAMBOO_SHORTPLANNAME'].split()[0]
        self.branch = self.args['BAMBOO_SHORTPLANNAME'].split()[1]
        # The following is a temporary fix for cases where SEN label is overridden in the booster config file
        # It's not a good practice as it breaks the mapping in Skipper. However, it's the only straight forward way to
        # override it for nightly scheduled plans.
        # Note: Only Teradata ODBC needs this fix for now.
        # TODO: Implement a better solution to address overriding the default Bamboo variables for scheduled plans
        if 'BAMBOO_SEN_LABEL' not in self.args:
            self.args['BAMBOO_SEN_LABEL'] = '__latest__'
            if self.product.lower() == 'teradata' and self.branch.lower() == 'dev01':
                self.args['BAMBOO_SEN_LABEL'] = '__head__'
        self.args['BAMBOO_DRV_LABEL'] = self.args.get('BAMBOO_DRV_LABEL', '__head__')

        if 'BAMBOO_MANUALBUILDTRIGGERREASON_USERNAME' in self.args:
            self.buildTrigger = self.args.get('BAMBOO_MANUALBUILDTRIGGERREASON_USERNAME')
            self.testSuiteList = None
        else:
            # Temporary change to disable smoke test until we have new skipper
            self.buildTrigger = 'REPOSITORY_CHANGE'
            # self.testSuiteList = 'Smoke'
            self.testSuiteList = None

        self.required_start_args = {
            # if run from bamboo, BAMBOO_ATA_PLANID key does not exist
            'planId': self.args.get('BAMBOO_ATA_PLANID', None),
            'BAMBOO_BUILD_SOURCE': self.args.get('BAMBOO_BUILD_SOURCE', self.args['DISTRIBUTION']),
            'BAMBOO_BUILD_TRIGGER': self.buildTrigger,
            'BAMBOO_TESTSUITE_LIST': self.testSuiteList,
        }
        # By default result is set to 'succeed'
        # Exceptional cases are handled by passing 'fail' as optional args
        # to override the result
        self.required_end_args = {
            'result': 'succeed',
            'driverName': self.product,
            'driverBranch': self.branch,
        }
        self.base_url = base_url
        self.closure_basic = [
            'BAMBOO_PLANKEY',
            'BAMBOO_BUILDNUMBER',
            'BAMBOO_COMPILER',
            'BAMBOO_TARGET',
            'BAMBOO_DRV_BRAND',
            'BAMBOO_DRV_LABEL',
            'BAMBOO_CORE_LABEL',
            'BAMBOO_SEN_LABEL',
            'BAMBOO_BOOSTER_LABEL',
            'BAMBOO_PRODUCT_LABEL',
            'BAMBOO_RETAIL_SUFFIX',
        ]

    def start(self, optional=None):
        arg = AtaUtil.getSelectedBambooVariables(self.args, self.closure_basic)
        merged = AtaUtil.mergeDict(arg, self.required_start_args)
        # Merge with additional non-required keys
        merged = AtaUtil.mergeDict(merged, optional)
        final_merge = AtaUtil.mergeDict(arg, merged)
        return self.post(self.base_url,
                         '/plan/start',
                         final_merge)

    def end(self, optional=None):
        arg = AtaUtil.getSelectedBambooVariables(self.args, self.closure_basic)
        logs_paths = self._get_logs_path()
        arg['BUILD_LOGS'] = logs_paths
        artifacts = self._get_artifacts_path()
        if artifacts:
            arg['BUILD_ARTIFACTS'] = artifacts
        merged = AtaUtil.mergeDict(arg, self.required_end_args)
        # Merge with additional non-required keys
        merged = AtaUtil.mergeDict(merged, optional)
        final_merge = AtaUtil.mergeDict(arg, merged)
        logger.debug("final Skipper payload {}".format(str(final_merge)))
        return self.post(self.base_url,
                         '/plan/end',
                         final_merge)

    def _get_logs_path(self):
        win_logs_path = os.environ.get('BOOSTER_VAR_LOGS_PATH_WIN')
        unix_logs_path = os.environ.get('BOOSTER_VAR_LOGS_PATH_WIN')
        logs_dict = {
            'windows': win_logs_path,
            'unix': unix_logs_path,
        }
        logger.debug("logs dict {}".format(str(logs_dict)))
        return logs_dict

    def _get_artifacts_path(self):
        artifacts = os.environ.get('BOOSTER_VAR_BUILD_ARTIFACTS')
        if not artifacts:
            return None
        artifacts = AtaUtil.fix_booster_path(artifacts, os.environ, recursive=True)
        win_path, unix_path = AtaUtil.normalize_path(artifacts)
        artifacts_dict = {'windows': win_path, 'unix': unix_path}
        logger.debug("artifacts dict {}".format(str(artifacts_dict)))
        return artifacts_dict


class SkipperThread(threading.Thread):
    """
    Customized thread class used for running a worker method every x seconds
    """

    def __init__(self, env, worker, name="", sleep_interval=0):
        """
        :param env: environment variables
        :param worker: function that the thread worker runs
        :param sleep_interval: sleep interval in seconds
        :param name: thread name
        """
        super(SkipperThread, self).__init__(name=name)
        self.exit_flag = False
        self.env = env
        self.worker = worker
        self.sleep_interval = sleep_interval  # in seconds
        self.exc_info = None

    def run(self):
        self._skipper_worker()

    def stop(self):
        self.exit_flag = True

    def _skipper_worker(self):
        while not self.exit_flag:
            try:
                self.worker()
                time.sleep(self.sleep_interval)
            except Exception:
                self.exc_info = traceback.format_exc()
                logger.debug("WARNING: {} thread failed!".format(self.name))
                logger.debug(self.exc_info)


class TestSkipper(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # cls.env = AtaUtil.setupFakeBambooEnv()
        cls.skipper = Skipper({k.strip().upper():
                                   os.environ[k] for k in os.environ})

    def testSkipperStartEndPlan(self):
        try:
            start_resp = self.skipper.startPlan()
            self.assertEqual(start_resp["state"],
                             "ok",
                             "Skipper start plan failed")
            time.sleep(3)
            end_resp = self.skipper.endPlan(optional={'result': 'succeed'})
        except Exception as e:
            sys.stderr.write(str(e))
            end_resp = self.skipper.endPlan(optional={'result': 'fail'})
        self.assertEqual(end_resp["state"], "ok", "Skipper end plan failed")

    def tearDown(self):
        self.skipper.stopPingThread()


if __name__ == '__main__':
    unittest.main()
