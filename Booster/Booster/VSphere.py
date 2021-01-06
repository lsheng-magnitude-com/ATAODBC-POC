from __future__ import print_function

import os
import time
try:
    import urllib2
except ImportError:
    import urllib.request
    import urllib.error
    
from ata.bamboo import getBambooVar
import ata.log
from Booster.classes.BoosterTag import BoosterTag
import BoosterError
from RESTClient import RESTClient

logger = ata.log.AtaLog(__name__)

LOCAL = 'http://localhost:5555'
REVERT_URI = '/vm_manager/vsphere/revert/'
STATUS_URI = '/vm_manager/vsphere/status/'

EXTRA_URI = "/rest"


class VSphere(BoosterTag):
    """
    Class that Communicates with Skipper to get interact with vSphere vCenter
    through the API provided by VMWare
    """
    def __init__(self):
        """
        Constructor to help set up the Skipper host that Booster will be
        interacting with
        """
        self.base_url = getBambooVar(os.environ, 'ATA_SKIPPER')
        if self.base_url is None:
            self.base_url = LOCAL
        if self.base_url.endswith(EXTRA_URI):
            self.base_url = self.base_url[:-len(EXTRA_URI)]
        self.revert_url = self.base_url + REVERT_URI
        self.status_url = self.base_url + STATUS_URI

    def run(self, root, debug=False):
        """
        Method that acts as the primary entry point for the class. It parses
        the root and determines what actions to take
        """
        vm_name = root.text
        action = root.attrib.get('action', '')
        if action == 'revert':
            image_name = root.attrib.get('image_name', '')
            self.revert_to_image(
                vm_name=vm_name,
                image_name=image_name,
                debug=debug,
            )
        elif action == 'status':
            print("Checking status of {vm}".format(vm=vm_name))
            self.check_status(vm_name=vm_name, debug=debug)
        elif action == 'wait':
            timeout = root.attrib.get('timeout', "600")
            wait_time = root.attrib.get('wait_time', "0")
            ping_time = root.attrib.get('ping_time', "60")
            self.wait(
                vm_name=vm_name,
                timeout=int(timeout),
                wait_time=int(wait_time),
                ping_time=int(ping_time),
                debug=debug,
            )
        else:
            raise BoosterError.BoosterTagError(
                "Unknown action {action} in attribute".format(
                    action=action,
                )
            )

    def revert_to_image(self, vm_name, image_name, debug=False):
        """
        Method to revert a specified VM to a specified image, using the the
        revert_url found in the instance
        """
        print("reverting {vm} to {image}".format(vm=vm_name, image=image_name))
        payload = {"vm_name": vm_name, "image_name": image_name}
        if debug:
            print("Send POST request to {url} with {payload}".format(
                url=self.base_url + REVERT_URI,
                payload=payload,
            ))
            return None
        else:
            rest_client = RESTClient()
            try:
                response = rest_client.post(self.base_url, REVERT_URI, payload)
            except urllib2.HTTPError as err:
                error_message = "Error {error_code} {reason} from {url}: {info}".format(
                    error_code=err.code,
                    url=err.geturl(),
                    reason=err.reason,
                    info=err.read(),
                )
                raise BoosterError.BoosterError(__name__, error_message)
            success_message = "vSphere will revert {vm} to {image} with {task}"
            print(success_message.format(vm=vm_name, image=image_name, task=response["task"]))
            return response["task"]

    def check_status(self, vm_name, debug=False):
        """
        Method to check the status of a specified VM using the status_url of
        the instance. This simply reports the status and is non-blocking
        """
        full_uri = STATUS_URI + vm_name
        if debug:
            print("Send GET request to {url}".format(
                url=self.base_url + full_uri,
            ))
            print("checked status of {vm}".format(vm=vm_name))
        else:
            rest_client = RESTClient()
            try:
                response = rest_client.get(self.base_url, full_uri)
            except urllib2.HTTPError as err:
                error_message = "Error {error_code} from {url}: ".format(
                    error_code=err.code,
                    url=err.geturl(),
                )
                error_message += err.read()
                raise BoosterError.BoosterError(__name__, error_message)
            success_message = "vSphere will update status of {vm}"
            print(success_message.format(vm=vm_name))
            self._print_status(vm_name, response)
            return response

    def wait(self, vm_name, timeout=300, wait_time=0, ping_time=60, debug=False):
        """
        Method that causes the script to pause and wait for the VM to come
        online before continuing with execution
        """
        if debug:
            print("waiting on {vm} to power on by checking status".format(
                vm=vm_name,
            ))
            print("checking status of {vm}".format(vm=vm_name))
            print("timeout {timeout}, wait_time {wait}, ping_time {ping}".format(
                timeout=timeout,
                wait=wait_time,
                ping=ping_time,
            ))
        else:
            start = time.time()
            status = None
            while (time.time() - start) < timeout:
                status = self.check_status(vm_name, debug)
                if all(status.values()):
                    break
                else:
                    elapsed = int(time.time() - start)
                    message = "VM is not ready. {time}s have elapsed."
                    print(message.format(time=elapsed))
                    print("Will check again in {ping}s".format(
                        ping=ping_time,
                    ))
                    time.sleep(ping_time)
            else:
                message_list = []
                message_list.append("TIMEOUT!!!!!:")
                message_list.append(
                    "{time}s has passed, exceeding the timeout of {timeout}s".format(
                        time=int(time.time() - start),
                        timeout=timeout,
                    )
                )
                message_list.append(
                    "<Last known {vm} status: {status}>".format(
                        vm=vm_name,
                        status=str(status),
                    )
                )
                error_message = " ".join(message_list)
                raise BoosterError.BoosterError(__name__, error_message)
            self._start_wait(wait_time)

    @staticmethod
    def _print_status(vm_name, status_dict):
        """
        Helper method to print out the status given by VMWare vSphere
        """
        powered_on = status_dict["powered_on"]
        tools_ok = status_dict["tools_ok"]
        if powered_on and tools_ok:
            print("{vm} is on and ready.".format(vm=vm_name))
        elif powered_on and not tools_ok:
            print("{vm} is on but vm tools not ready.".format(vm=vm_name))
        elif not powered_on and tools_ok:
            print("{vm} is off but vm tools is ready. How did you even get this?".format(vm=vm_name))
        else:
            print("{vm} is currently powered down.".format(vm=vm_name))

    # TODO this method can be moved out if other tags need it
    @staticmethod
    def _start_wait(wait_time):
        """
        Helper method to control the wait cycle, blocking script execution
        until the wait is complete
        """
        print("Entering wait phase. Waiting time of {wait}s.".format(
            wait=wait_time,
        ))
        start = time.time()
        end = start + wait_time
        while time.time() < end:
            print("waited for {time}s".format(
                time=int(time.time() - start),
            ))
            print("{time}s remaining".format(
                time=int(end - time.time()),
            ))
            update_time = min(int(end - time.time()), 60)
            if update_time < 1:
                # prevent constant wait times of 0
                update_time = 1
            print("next update in {time}s".format(
                time=update_time,
            ))
            time.sleep(update_time)
        else:
            print("Wait complete, now continuing with rest of script execution")


def Execute(root):
    print('==============================')
    print('          Enter vSphere Manager')
    print('==============================')

    logger.debug('Enter VSphere')
    vsphere = VSphere()
    vsphere.run(root, debug=False)


def Debug(root):
    print('==============================')
    print('          Debug vSphere Manager')
    print('==============================')

    logger.debug('Enter VSphere')
    vsphere = VSphere()
    vsphere.run(root, debug=True)
