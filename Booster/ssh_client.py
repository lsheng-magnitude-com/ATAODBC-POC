import os

import Booster.Command as Command
from BoosterError import SSHError


class SSHClient(object):
    def __init__(self, private_key=None, ssh_exec="ssh", scp_exec="scp"):
        self.ssh_exec = ssh_exec
        self.scp_exec = scp_exec
        self._set_private_key(private_key)
        self.ssh_flags = ["-o", "StrictHostKeyChecking=no", "-i", self.private_key]
        # -r flag allows copying directories
        self.scp_flags = self.ssh_flags + ["-r"]

    def _set_private_key(self, private_key):
        if not private_key:
            # Default location
            self.private_key = os.path.expanduser(os.path.join('~', '.ssh', 'id_rsa'))
        else:
            self.private_key = private_key
        if not os.path.isfile(self.private_key):
            raise SSHError(__name__, "private key file {path} does not exist".format(path=self.private_key))

    def execute_on_host(self, host, cmd):
        """
        Executes a command on the remote host
        :param host: string value formatted as <user>@<ip or hostname>
        :param cmd: command to execute
        """
        command = [self.ssh_exec] + self.ssh_flags + [host, cmd]
        Command.ExecuteAndLogVerbose(command, shell=False)

    def execute_on_host_in_slient(self, host, cmd):
        """
        Executes a command on the remote host
        :param host: string value formatted as <user>@<ip or hostname>
        :param cmd: command to execute
        """
        command = [self.ssh_exec] + self.ssh_flags + [host, cmd]
        Command.ExecuteInSilentMode(command, shell=False)

    def scp(self, source, dest):
        """
        Copies a file from one host machine to another
        :param source: local or remote path to a file or directory.
        The remote path should be formatted as <user>@<ip/hostname>:<path>
        :param dest: local or remote path to a file or directory.
        The remote path should be formatted as <user>@<ip/hostname>:<path>
        """
        command = [self.scp_exec] + self.scp_flags + [source, dest]
        Command.ExecuteAndLogVerbose(command, shell=False)
