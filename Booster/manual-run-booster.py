"""
This module is used for manual booster runs
Usage: manual-run-booster.py Config/Projects/<project>/<configfile>
e.g manual-run-booster.py Config/Projects/NoSQLODBC/MongoDB.build
"""

from __future__ import print_function

import sys

import AtaUtil
import BoosterError
import build
import init
import traceback

import ata.log

logger = ata.log.AtaLog(__name__)

whatis = '''$Id: //ATA/Booster/Maintenance/1.0/manual-run-booster.py#8 $
$Change: 652781 $
$DateTime: 2020/10/13 09:38:53 $
$Revision: #8 $
'''


def main(argv):
    logger.info(whatis)
    configfile = argv[0]
    #init.ExecuteManualBuild(configfile)
    build.Execute(configfile)


if __name__ == "__main__":
    try:
        successful_build = True
        AtaUtil.log_env("startenv.log")
        main(sys.argv[1:])
    except BoosterError.BoosterError as e:
        traceback.print_exc()
        logger.critical(e)
        successful_build = False
    except Exception as e:
        traceback.print_exc()
        logger.exception("***\n%s\n***\n" % e)
        successful_build = False
    AtaUtil.log_env("endenv.log")
    if not successful_build:
        exit(-1)
