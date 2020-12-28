import os
import sys
import subprocess

def runCommand(cmd):
    print (cmd)
    result = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    for line in result.stdout:
        print (line)
    for line in result.stderr:
        print (line)
    result.poll()
    if result.returncode != 0:
        exit(-1)


def main():
    runCommand('docker -v')


if __name__ == "__main__":
    main()
