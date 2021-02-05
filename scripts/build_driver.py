# This script is to build the snowflake driver in github action
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


def build_windows():
    print ("====> Read build config from env")
    arch = os.environ.get('ARCH', 'x64')
    target = os.environ.get('TARGET', 'release')
    vs = os.environ.get('VS', 'undef')
    php = os.environ.get('PHP', 'undef')
    if vs == 'undef':
        print ("==Please set VS in env variable==")
        exit(-1)
    if php == 'undef':
        print ("==Please set PHP in env variable==")
        exit(-1)
    print ("arch = " + arch)
    print ("target = " + target)
    print ("vs = " + vs)
    print ("php = " + php + " (make sure the source version you use here is same as the on in setup-php action)")

    cwd = os.environ.get('GITHUB_WORKSPACE')
    ropo = os.path.join(cwd, 'pdo_snowflake')
    print ("====> building snowflake driver: " + cwd)
    print ("====> working directory: " + ropo)
    print ("====> prepare repository")
    runCommand('git clone https://github.com/snowflakedb/pdo_snowflake.git')
    os.chdir(ropo)
    runCommand("rmdir ./libsnowflakeclient/lib/linux /s/q")
    runCommand("rmdir ./libsnowflakeclient/lib/darwin /s/q")
    runCommand("rmdir ./libsnowflakeclient/deps-build/linux /s/q")
    runCommand("rmdir ./libsnowflakeclient/deps-build/darwin /s/q")

    print ("====> setup php sdk and php source")
    runCommand("./scripts/setup_php_sdk.bat " + arch + " " + target + " " + vs + " " + php + " c:/php-sdk")
    runCommand("./scripts/run_setup_php.bat " + arch + " " + target + " " + vs + " " + php + " c:/php-sdk")

    print ("====> build pdo driver")
    runCommand("./scripts/run_build_pdo_snowflake.bat " + arch + " " + target + " " + vs + " " + php + " c:/php-sdk")
    runCommand("xcopy c:/php-sdk/phpmaster/" + vs.replace("VS","vc") + "/" + arch + "/ php-src/" + arch + "/" + target + "_TS/php_pdo_snowflake.dll c:/tools/php/ext/ /I/Y/F")
    runCommand("c:/tools/php/php.exe -dextension=pdo_snowflake -m")


def main():
    current_os = os.name
    if current_os == 'nt':
        build_windows()
    else:
        build_posix()



if __name__ == "__main__":
    main(sys.argv)
