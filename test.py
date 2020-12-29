import os
import sys
import subprocess

def runCommand(cmd):
    print (cmd)
    result = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    for line in result.stdout:
        print (line.strip().decode('utf-8'))
    for line in result.stderr:
        print (line.strip().decode('utf-8'))
    result.poll()
    if result.returncode != 0:
        exit(-1)


def main():
    runCommand('docker -v')
    runCommand('docker pull centos:latest')
    runCommand('docker run --detach --name build_env --net=host centos:latest tail -f /dev/null')
    runCommand('docker ps')
    runCommand('docker exec build_env bash -c "cat /etc/os-release"')
    runCommand('docker exec build_env bash -c "ls"')
    runCommand('docker exec build_env bash -c "ls /home/"')


if __name__ == "__main__":
    main()
