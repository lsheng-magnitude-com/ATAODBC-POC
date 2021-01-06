from __future__ import print_function

import json
import time
import traceback
try:
    import urllib2
except ImportError:
    import urllib.request
    import urllib.error

import BoosterError
import ata.log
from Booster.Debug import Debug as Debugger

logger = ata.log.AtaLog(__name__)

user = 'bamboo'
password = ''
# server = "http://BTAServicesVM.lakes.ad:8888/PowerShell?"
server = "http://BTAServicesVM.lakes.ad:5000/rest/vm/"
timeout_seconds = 600
default_preparation_time = 10.0  # seconds


def Execute(root):
    print('==============================')
    print('          Enter Manage VM')
    print('==============================')

    logger.debug('Enter ManageVM')
    vmname = root.text
    command = root.attrib.get('command', '')
    snapshotname = root.attrib.get('snapshotname', '')
    try:
        preparation_time = float(root.attrib.get('preparation_time', default_preparation_time))
    except ValueError:
        raise BoosterError.BoosterTagError(__name__, "preparation_time attribute should be a number")

    try:
        logger.info(command + " " + snapshotname)
        manage_vm(vmname=vmname, command=command, snapshotname=snapshotname, preparation_time=preparation_time)
    except BoosterError.BoosterError:
        raise
    except Exception:
        raise BoosterError.BoosterError(__name__, "Unexpected error", traceback=traceback.format_exc())


def Debug(root):
    print('==============================')
    print('          Debug ManageVM')
    print('==============================')

    vmname = root.text
    command = root.attrib.get('command', 'RevertSnapshot')
    snapshotname = root.attrib.get('snapshotname', 'test')
    url = "http://" + server + "/PowerShell?command=" + command + "&VM=" + vmname + "&SnapshotName=" + snapshotname
    logger.info("URL " + url)


def wait(vm_name, preparation_time):
    if Debugger().skip('vm', '----Skip: wait {}'.format(preparation_time)):
        return ''
    url = server + "getdetails"
    values = {"vmname": vm_name}
    timeout = time.time() + timeout_seconds
    ip = ""
    tool_status = "toolsNotRunning"
    request = ""
    inform_tool_status = False
    inform_ip_status = False
    while tool_status == "toolsNotRunning" or ip == "" or ip == "0.0.0.0":
        request = run_request(url, values)
        arg = json.loads(request)
        if 'IPAddress' not in arg:
            ip = ""
        else:
            ip = arg['IPAddress']
        tool_status = arg['ToolsStatus']
        if (tool_status == "toolsNotRunning" and ip != "") or time.time() > timeout:
            if time.time() > timeout:
                raise BoosterError.BoosterError(__name__, 'Manage VM Error! wait error: ' + vm_name +
                                                ' did not reach a usable state in ' + str(timeout_seconds) + ' seconds')
            break
        else:
            if tool_status == "toolsNotRunning" and not inform_tool_status:
                logger.info('Waiting on OS to start up...')
                # This prevents the same message to be logged multiple times
                inform_tool_status = True
            elif ip == "" and not inform_ip_status:
                logger.info('Waiting on IP to be assigned...')
                # This prevents the same message to be logged multiple times
                inform_ip_status = True

        if arg['PowerState'] == 'Powered off':
            raise BoosterError.BoosterError(__name__, 'Manage VM Error! wait error: ' + vm_name + ' is not powered on')
        # Wait for 10 seconds before the next request
        time.sleep(10)

    logger.info("Waiting on VM preparation (currently set to {} seconds)...".format(preparation_time))
    time.sleep(preparation_time)
    return request


def run_request(url, values):
    values['User'] = user
    data = json.dumps(values)
    logger.debug("url: {}".format(url))
    logger.debug("values: {}".format(values))
    if Debugger().skip('vm', '----Skip:\n  url[{}]\n  data[{}]'.format(url, data)):
        return ''
    request = urllib2.Request(url, data, {'Content-Type': 'application/json'})
    try:
        f = urllib2.urlopen(request)
        result = f.read()
        f.close()
    except urllib2.HTTPError as e:
        raise BoosterError.BoosterError(__name__, 'Manage VM Error! ' + e.read())
    arg = json.loads(result)
    logger.debug("response: {}".format(arg))
    if 'Error' in arg:
        raise BoosterError.BoosterError(__name__, 'Manage VM Error! ' + arg['Error'])
    return result


def manage_vm(**kwargs):
    # Validate input
    vm_name = kwargs['vmname']
    command = kwargs['command']
    if vm_name:
        logger.info('VM Name: ' + vm_name)
    else:
        raise BoosterError.BoosterTagError(__name__, 'vm_name is blank')
    if command:
        logger.info('Command: ' + command)
    else:
        raise BoosterError.BoosterTagError(__name__, 'command is blank')
    command_lower = command.lower()
    # run based off command

    if command_lower == "wait":
        preparation_time = kwargs['preparation_time']
        results = wait(vm_name, preparation_time)
    else:
        snapshotname = kwargs['snapshotname']
        if command_lower == "revert":
            if snapshotname is None or snapshotname.strip() == '':
                raise BoosterError.BoosterTagError(__name__, 'snapshotname is blank')
            else:
                logger.info('Snapshot Name: ' + snapshotname)
                url = server + "revert"
                values = {"vmname": vm_name, "snapshotname": snapshotname}
        elif command_lower == "start":
            url = server + "start"
            values = {"vmname": vm_name}
        elif command_lower == "stop":
            url = server + "stop"
            values = {"vmname": vm_name}
        elif command_lower == "getdetails":
            url = server + "getdetails"
            values = {"vmname": vm_name}
        else:
            raise BoosterError.BoosterTagError(__name__, 'Command "{command}" is invalid'.format(command=command_lower))
        results = run_request(url, values)
    return results
