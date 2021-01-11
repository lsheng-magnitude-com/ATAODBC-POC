import os
import sys
import subprocess

def run_command(cmd):
    print (cmd)
    result = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=True)
    for line in result.stdout:
        print (line.strip().decode('utf-8'))
    for line in result.stderr:
        print (line.strip().decode('utf-8'))
    result.poll()
    if result.returncode != 0:
        exit(-1)


def run_command_in_docker(cmd):
    cmd = 'docker exec build_env bash -c ' + '"' + cmd + '"'
    print (cmd)
    run_command(cmd)


def main():
    BAMBOO_PLANNAME, BAMBOO_SHORTJOBNAME = init_github_env()
    run_command('export')
    run_command('docker -v')
    run_command('docker pull simbadevops/centos7-gcc5_5:latest')
    run_command('docker run --volume /home:/home --env BAMBOO_PLANNAME=' + "'" + BAMBOO_PLANNAME + "'" +' --env BAMBOO_SHORTJOBNAME=' + BAMBOO_SHORTJOBNAME + ' --detach --name build_env --net=host simbadevops/centos7-gcc5_5:latest tail -f /dev/null')
    run_command('docker ps')
    run_command_in_docker('cat /etc/os-release')
    run_command_in_docker('cd /home/runner/work/ATA/ATA/Booster && python booster.py test.xml')


def init_github_env():
    repo = os.environ.get('GITHUB_REPOSITORY','').replace("'","")
    workflow = os.environ.get('GITHUB_WORKFLOW','').replace("'","")
    ref = os.environ.get('GITHUB_REF').replace("'","")
    category, product, type = (repo.split('/')[-1]).split('-')
    plan_type, env = workflow.split('-')
    branch = ref.split('/')[-1]
    category = category.strip()
    product = product.strip()
    type = type.strip()
    plan_type = plan_type.strip()
    env = env.strip()
    branch = branch.strip()
    BAMBOO_PLANNAME = plan_type + ' ' + type + ' ' + category + ' - ' + env + ' - ' + product + ' ' + branch
    BAMBOO_SHORTJOBNAME = os.environ.get('GITHUB_JOB', '').replace("'", "")
    return BAMBOO_PLANNAME, BAMBOO_SHORTJOBNAME


if __name__ == "__main__":
    main()
