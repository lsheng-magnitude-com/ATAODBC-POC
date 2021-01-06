from __future__ import print_function

import os
import re
import subprocess
import sys
import traceback

import AtaUtil
import Booster.Command as Command
import Booster.Var as Var
import ata.log
import build
import init
from Booster.Debug import Debug as Debugger
from BoosterError import SkipperError, BoosterError
from Skipper import Skipper

logger = ata.log.AtaLog(__name__)

whatis = """$Id: //ATA/Booster/Maintenance/1.0/booster.py#30 $
$Change: 634910 $
$DateTime: 2020/08/25 17:09:32 $
$Revision: #30 $
"""

def main(argv):
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--env', type=str, help='loadable environment, usually for debug purpose or simulation')
    parser.add_argument('file', type=str, nargs='?', help='substituted config file')
    args = parser.parse_args()
    if args.env is not None:
        extra = Var.file2dict(args.env)
        os.environ.update(extra)

    logger.info(whatis)
    if args.file is None:
        # bamboo invokes the plan script without extra config file
        # all information are passed/parsed by environment variables
        buildfile = init.ExecuteBambooBuild()
        init.ExecuteTask("Config/Common/finalTask.xml")
        if not Debugger().skip('skipper') and os.environ['USE_SKIPPER'] == 'True':
            print("=====enter skipper========")
            try:
                skipper = Skipper({k.strip().upper().replace('BOOSTER_VAR_',''): os.environ[k] for k in os.environ})
                status = {'result': 'succeed'}
                res = skipper.startPlan()
                if res['state'] != 'ok':
                    raise SkipperError('startPlan', res['detail'], traceback=traceback.format_exc())
                build.Execute(buildfile)
            except BoosterError:
                status['result'] = 'fail'
                raise
            except Exception as e:
                status['result'] = 'fail'
                raise BoosterError(__name__, "Unexpected error: {exception}".format(exception=e),
                                   traceback=traceback.format_exc())
            finally:
                skipper.endPlan(optional=status)
        else:
            print('Do not use Skipper')
            build.Execute(buildfile)
    else:
        configfile = args.file
        buildfile = init.ExecuteInputFile(configfile)
        init.ExecuteTask("Config/Common/finalTask.xml")
        build.Execute(buildfile)


#def stash():
#    try:
        # Skip stashing for BuildScripts for the following reasons:
        # - Environment will not be setup correctly. e.g $(STAGING_DIR) and other variables will not be setup
        # - BuildScripts already log everything in stdout and save functional test results on oak. TODO: Update buildscripts to save logs to Filbert
#        if "STAGING_DIR" not in os.environ:
#            logger.debug("Skipping stashing. STAGING_DIR is not set in the environment.")
#            return
#        logger.info('Start stashing build files')
#        buildfile = init.ExecuteTask("Config/Common/Build.archive")
#        build.process(buildfile)
#        logger.info('Finished stashing build files')
#    except Exception as e:
#        logger.error("Stashing failed: %s" % e)


#def cleanup(configfile):
#    logger.info("Performing cleanup...")
#    buildfile = init.ExecuteTask(configfile)
#    build.process(buildfile)


if __name__ == "__main__":
    try:
        successful_build = True
        current_directory = os.getcwd()
        AtaUtil.log_env("startenv.log")
        main(sys.argv[1:])
    except subprocess.CalledProcessError as error:
        traceback.print_exc()
        logger.critical(error.output)
        successful_build = False
    except BoosterError as error:
        traceback.print_exc()
        logger.critical(error)
        successful_build = False
    except Exception as e:
        traceback.print_exc()
        logger.exception("***\n%s\n***\n" % e)
        successful_build = False
    finally:
        if os.getcwd() != current_directory:
            logger.debug("Change directory back to {}".format(current_directory))
            os.chdir(current_directory)
    AtaUtil.log_env("endenv.log")
#    cleanup("cleanup.xml")
#    stash()
    if not successful_build:
        exit(-1)
