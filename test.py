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
    docker_env_string = init_github_env()
    workspace = os.environ.get('GITHUB_WORKSPACE','').replace("'","")
    run_command('export')
    run_command('docker -v')
    run_command('docker pull simbadevops/centos7-gcc5_5:latest')
    run_command('docker run --volume /home:/home ' + docker_env_string + ' --detach --name build_env --net=host simbadevops/centos7-gcc5_5:latest tail -f /dev/null')
    run_command('docker ps')
    run_command_in_docker('cat /etc/os-release')
    run_command_in_docker('cd ' + workspace + '/Booster && python booster.py ICU.build')


def init_github_env():
    repo = os.environ.get('GITHUB_REPOSITORY','')
    workflow = os.environ.get('GITHUB_WORKFLOW','')
    ref = os.environ.get('GITHUB_REF')
    job = os.environ.get('GITHUB_JOB', '')
    workspace = os.environ.get('GITHUB_WORKSPACE', '')
    #category, product, type = (repo.split('/')[-1]).split('-')
    #plan_type, env = workflow.split('-')
    #branch = ref.split('/')[-1]
    #category = category.strip()
    #product = product.strip()
    #type = type.strip()
    #plan_type = plan_type.strip()
    #env = env.strip()
    #branch = branch.strip()
    #plan_name = plan_type + ' ' + type + ' ' + category + ' - ' + env + ' - ' + product + ' ' + branch
    #job_name = os.environ.get('GITHUB_JOB', '').replace("'", "")
    docker_env_string = '--env GITHUB_REPOSITORY=' + "'" + repo + "'" + ' --env GITHUB_WORKFLOW=' + "'" + workflow + "'" + ' --env GITHUB_REF=' + "'" + ref + "'" + ' --env GITHUB_JOB=' + "'" + job + "'" + ' --env GITHUB_WORKSPACE=' + "'" + workspace + "'"
    return docker_env_string


if __name__ == "__main__":
    main()
