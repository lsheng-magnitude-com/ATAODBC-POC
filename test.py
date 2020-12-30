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


def runCommandinDocker(cmd):
    cmd = 'docker exec build_env bash -c ' + '"' + cmd + '"'
    print (cmd)
    runCommand(cmd)


def main():
    runCommand('docker -v')
    runCommand('docker pull centos:latest')
    runCommand('docker run --volume /home:/home --detach --name build_env --net=host centos:latest tail -f /dev/null')
    runCommand('docker ps')
    runCommandinDocker('cat /etc/os-release')
    runCommandinDocker('yum install gcc openssl-devel bzip2-devel -y')
    runCommandinDocker('yum install wget -y')
    runCommandinDocker('wget https://www.python.org/ftp/python/2.7.18/Python-2.7.18.tgz')
    runCommandinDocker('tar xzf Python-2.7.18.tgz')
    runCommandinDocker('cd ./Python-2.7.18 && ./configure --enable-optimizations')
    runCommandinDocker('cd ./Python-2.7.18 && make altinstall')
    runCommandinDocker('curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py')
    runCommandinDocker('python2.7 get-pip.py')



if __name__ == "__main__":
    main()
